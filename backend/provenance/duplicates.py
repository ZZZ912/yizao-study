import hashlib
import json
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _normalized_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(
        character
        for character in normalized
        if not character.isspace() and not unicodedata.category(character).startswith("P")
    )


def _digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def content_checksum(question: dict) -> str:
    content = {
        "question_type": question.get("question_type"),
        "stem": _collapse_whitespace(question.get("stem", "")),
        "options": [
            {
                "label": str(option.get("label", "")).strip().upper(),
                "text": _collapse_whitespace(str(option.get("text", ""))),
            }
            for option in question.get("options", [])
        ],
        "answer": sorted(str(label).strip().upper() for label in question.get("answer", [])),
        "analysis": _collapse_whitespace(question.get("analysis", "")),
    }
    return _digest(content)


def exact_hash(question: dict) -> str:
    return _digest(
        {
            "stem": _collapse_whitespace(question.get("stem", "")),
            "options": [
                (
                    str(option.get("label", "")).strip().upper(),
                    _collapse_whitespace(str(option.get("text", ""))),
                )
                for option in question.get("options", [])
            ],
        }
    )


def normalized_hash(question: dict) -> str:
    return _digest(
        {
            "stem": _normalized_text(question.get("stem", "")),
            "options": sorted(
                _normalized_text(str(option.get("text", "")))
                for option in question.get("options", [])
            ),
        }
    )


def _group_payload(group_type: str, records: list[dict], details: dict | None = None) -> dict:
    return {
        "type": group_type,
        "external_ids": [record["data"].get("external_id", "") for record in records],
        "line_numbers": [record["line_number"] for record in records],
        "details": details or {},
    }


def detect_duplicate_candidates(records: list[dict]) -> list[dict]:
    groups: list[dict] = []
    by_external_id: dict[str, list[dict]] = defaultdict(list)
    by_exact_hash: dict[str, list[dict]] = defaultdict(list)
    by_normalized_hash: dict[str, list[dict]] = defaultdict(list)
    by_normalized_stem: dict[str, list[dict]] = defaultdict(list)

    for record in records:
        data = record["data"]
        by_external_id[data["external_id"]].append(record)
        by_exact_hash[exact_hash(data)].append(record)
        by_normalized_hash[normalized_hash(data)].append(record)
        by_normalized_stem[_normalized_text(data["stem"])].append(record)

    for duplicate_records in by_external_id.values():
        if len(duplicate_records) < 2:
            continue
        checksums = {content_checksum(record["data"]) for record in duplicate_records}
        if len(checksums) > 1:
            groups.append(_group_payload("external_id_content_conflict", duplicate_records))

    for duplicate_records in by_exact_hash.values():
        if len(duplicate_records) > 1:
            groups.append(_group_payload("exact_hash", duplicate_records))

    exact_group_lines = {
        tuple(group["line_numbers"]) for group in groups if group["type"] == "exact_hash"
    }
    for duplicate_records in by_normalized_hash.values():
        line_numbers = tuple(record["line_number"] for record in duplicate_records)
        if len(duplicate_records) > 1 and line_numbers not in exact_group_lines:
            groups.append(_group_payload("normalized_hash", duplicate_records))

    for stem_records in by_normalized_stem.values():
        if len(stem_records) < 2:
            continue
        answers = {
            tuple(sorted(str(label).strip().upper() for label in record["data"].get("answer", [])))
            for record in stem_records
        }
        option_orders = {
            tuple(
                str(option.get("label", "")).strip().upper()
                for option in record["data"].get("options", [])
            )
            for record in stem_records
        }
        if len(answers) > 1:
            groups.append(_group_payload("same_stem_answer_conflict", stem_records))
        if len(option_orders) > 1:
            groups.append(_group_payload("same_stem_option_order_changed", stem_records))

    similarity_buckets: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for record in records:
        normalized_stem = _normalized_text(record["data"]["stem"])
        similarity_buckets[(normalized_stem[:8], len(normalized_stem) // 20)].append(record)

    seen_pairs: set[tuple[int, int]] = set()
    for bucket_records in similarity_buckets.values():
        for index, left in enumerate(bucket_records):
            left_stem = _normalized_text(left["data"]["stem"])
            for right in bucket_records[index + 1 :]:
                pair = (left["line_number"], right["line_number"])
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                right_stem = _normalized_text(right["data"]["stem"])
                if left_stem == right_stem or not left_stem or not right_stem:
                    continue
                score = SequenceMatcher(None, left_stem, right_stem, autojunk=False).ratio()
                if score >= 0.92:
                    groups.append(
                        _group_payload(
                            "stem_similarity",
                            [left, right],
                            {"score": round(score, 4)},
                        )
                    )

    return groups


def warning_codes_for_lines(groups: list[dict]) -> dict[int, set[str]]:
    codes: dict[int, set[str]] = defaultdict(set)
    for group in groups:
        if group["type"] in {"external_id_content_conflict", "same_stem_answer_conflict"}:
            code = (
                "answer_conflict"
                if group["type"] == "same_stem_answer_conflict"
                else "external_id_conflict"
            )
        elif group["type"] == "same_stem_option_order_changed":
            code = "option_order_changed"
        else:
            code = "duplicate_candidate"
        for line_number in group["line_numbers"]:
            codes[line_number].add(code)
    return codes
