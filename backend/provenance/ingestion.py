import hashlib
import json
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from jsonschema import Draft202012Validator

from curriculum.models import Chapter, Section, Subject
from questions.models import Question, QuestionOption, QuestionVersion

from .duplicates import content_checksum, detect_duplicate_candidates, warning_codes_for_lines
from .models import ContentImportBatch, ContentImportItem, ContentProvenance, SourceMaterial

SCHEMA_PATH = Path(settings.BASE_DIR).parent / "content" / "schemas" / "question.schema.json"
PRIVATE_REPORT_ROOT = Path(settings.BASE_DIR).parent / "import-reports" / "private"


class ContentValidationError(Exception):
    def __init__(self, report: dict):
        super().__init__("Content validation failed.")
        self.report = report


@dataclass
class ValidationResult:
    path: Path
    source_checksum: str
    records: list[dict]
    report: dict

    @property
    def has_errors(self) -> bool:
        return self.report["error_count"] > 0


def _issue(code: str, message: str, path: str = "") -> dict:
    return {"code": code, "message": message, "path": path}


def _schema_validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _semantic_errors(data: dict, input_path: Path) -> list[dict]:
    errors: list[dict] = []
    labels = [str(option.get("label", "")).strip().upper() for option in data.get("options", [])]
    if len(labels) != len(set(labels)):
        errors.append(_issue("duplicate_option_label", "Option labels must be unique.", "options"))

    answers = [str(label).strip().upper() for label in data.get("answer", [])]
    missing_answers = sorted(set(answers) - set(labels))
    if missing_answers:
        errors.append(
            _issue(
                "answer_not_in_options",
                f"Answer labels are absent from options: {', '.join(missing_answers)}.",
                "answer",
            )
        )

    source_file = str(data.get("source_file", ""))
    if "/" in source_file or "\\" in source_file:
        errors.append(
            _issue(
                "source_file_is_path", "source_file must contain a file name only.", "source_file"
            )
        )

    is_public_fixture = any(
        part.lower() in {"fixtures", "demo-data", "public-fixtures"} for part in input_path.parts
    )
    if is_public_fixture and data.get("public_repo_allowed") is False:
        errors.append(
            _issue(
                "private_content_in_public_fixture",
                "Private content cannot be emitted to a public fixture directory.",
                "public_repo_allowed",
            )
        )
    return errors


def _normalized_warnings(data: dict) -> list:
    warnings = list(data.get("warnings", []))
    if data.get("extraction_confidence", 1) < 0.8:
        warnings.append(
            {
                "code": "low_extraction_confidence",
                "message": "Extraction confidence is below 0.8 and requires manual review.",
            }
        )
    return warnings


def validate_jsonl(path: str | Path) -> ValidationResult:
    input_path = Path(path).resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Content file not found: {input_path}")

    raw_bytes = input_path.read_bytes()
    source_checksum = hashlib.sha256(raw_bytes).hexdigest()
    validator = _schema_validator()
    records: list[dict] = []

    with input_path.open("r", encoding="utf-8-sig") as source:
        for line_number, raw_line in enumerate(source, start=1):
            line = raw_line.strip()
            if not line:
                continue
            errors: list[dict] = []
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                records.append(
                    {
                        "line_number": line_number,
                        "data": {},
                        "warnings": [],
                        "errors": [
                            _issue(
                                "invalid_json",
                                f"Invalid JSON at column {exc.colno}: {exc.msg}",
                            )
                        ],
                    }
                )
                continue

            if isinstance(data, dict):
                if isinstance(data.get("external_id"), str):
                    data["external_id"] = data["external_id"].strip().lower()
                if isinstance(data.get("answer"), list):
                    data["answer"] = [str(label).strip().upper() for label in data["answer"]]
                if isinstance(data.get("options"), list):
                    for option in data["options"]:
                        if isinstance(option, dict) and isinstance(option.get("label"), str):
                            option["label"] = option["label"].strip().upper()

            schema_errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
            for error in schema_errors:
                error_path = ".".join(str(part) for part in error.absolute_path)
                errors.append(_issue("schema_error", error.message, error_path))
            errors.extend(_semantic_errors(data, input_path))
            records.append(
                {
                    "line_number": line_number,
                    "data": data,
                    "warnings": _normalized_warnings(data),
                    "errors": errors,
                }
            )

    valid_records = [record for record in records if not record["errors"]]
    duplicate_groups = detect_duplicate_candidates(valid_records)
    warning_codes = warning_codes_for_lines(duplicate_groups)
    for record in valid_records:
        existing_codes = {
            warning.get("code") if isinstance(warning, dict) else str(warning)
            for warning in record["warnings"]
        }
        for code in sorted(warning_codes.get(record["line_number"], set()) - existing_codes):
            record["warnings"].append(
                {"code": code, "message": "Conservative duplicate review candidate."}
            )

    chapters = Counter(str(record["data"]["chapter"]) for record in valid_records)
    question_types = Counter(record["data"]["question_type"] for record in valid_records)
    report = {
        "source_name": input_path.name,
        "source_checksum": source_checksum,
        "total_count": len(records),
        "valid_count": len(valid_records),
        "warning_count": sum(bool(record["warnings"]) for record in valid_records),
        "error_count": sum(bool(record["errors"]) for record in records),
        "chapter_counts": dict(sorted(chapters.items(), key=lambda item: int(item[0]))),
        "question_type_counts": dict(sorted(question_types.items())),
        "duplicate_candidate_count": len(duplicate_groups),
        "answer_conflict_count": sum(
            group["type"] in {"same_stem_answer_conflict", "external_id_content_conflict"}
            for group in duplicate_groups
        ),
        "duplicate_groups": duplicate_groups,
        "issues": [
            {
                "line_number": record["line_number"],
                "external_id": record["data"].get("external_id", ""),
                "warnings": record["warnings"],
                "errors": record["errors"],
            }
            for record in records
            if record["warnings"] or record["errors"]
        ],
    }
    return ValidationResult(input_path, source_checksum, records, report)


def _subject_code(title: str) -> str:
    return f"subject-{hashlib.sha256(title.encode('utf-8')).hexdigest()[:12]}"


def _source_external_id(file_name: str) -> str:
    return f"source-{hashlib.sha256(file_name.encode('utf-8')).hexdigest()[:24]}"


def _review_status(data: dict) -> str:
    if not data.get("public_repo_allowed", False) or data.get("content_origin") != "original":
        return QuestionVersion.ReviewStatus.PENDING_REVIEW
    requested = data.get("review_status", "pending_review")
    return {
        "pending": QuestionVersion.ReviewStatus.PENDING_REVIEW,
        "pending_review": QuestionVersion.ReviewStatus.PENDING_REVIEW,
        "reviewed": QuestionVersion.ReviewStatus.REVIEWED,
        "disputed": QuestionVersion.ReviewStatus.DISPUTED,
    }.get(requested, QuestionVersion.ReviewStatus.PENDING_REVIEW)


def _plan_actions(result: ValidationResult) -> list[dict]:
    valid_records = [record for record in result.records if not record["errors"]]
    external_ids = {record["data"]["external_id"] for record in valid_records}
    questions = Question.objects.filter(external_id__in=external_ids).prefetch_related("versions")
    state = {
        question.external_id: (
            question.versions.order_by("-version_number").first().content_checksum,
            question.versions.count(),
        )
        for question in questions
        if question.versions.exists()
    }
    actions = []
    for record in valid_records:
        external_id = record["data"]["external_id"]
        checksum = content_checksum(record["data"])
        if external_id not in state:
            action = "created"
            state[external_id] = (checksum, 1)
        elif state[external_id][0] == checksum:
            action = "skipped"
        else:
            action = "versioned"
            state[external_id] = (checksum, state[external_id][1] + 1)
        actions.append(
            {
                "line_number": record["line_number"],
                "external_id": external_id,
                "action": action,
                "warnings": record["warnings"],
            }
        )
    return actions


def _source_material(data: dict) -> SourceMaterial:
    file_name = data["source_file"]
    external_id = _source_external_id(file_name)
    source, _ = SourceMaterial.objects.get_or_create(
        external_id=external_id,
        defaults={
            "file_name": file_name,
            "source_type": data["source_type"],
            "institution": data.get("institution", ""),
            "title": data.get("source_title", Path(file_name).stem),
            "year": data.get("year"),
            "rights_scope": data["rights_scope"],
            "public_repo_allowed": data["public_repo_allowed"],
            "private_reference": external_id,
            "extraction_method": data["extraction_method"],
            "metadata": {},
        },
    )
    source.full_clean()
    return source


def _curriculum(data: dict) -> tuple[Subject, Chapter, Section, list[dict]]:
    warnings: list[dict] = []
    subject, _ = Subject.objects.get_or_create(
        code=_subject_code(data["subject"]),
        defaults={"title": data["subject"]},
    )
    chapter, _ = Chapter.objects.get_or_create(
        subject=subject,
        number=data["chapter"],
        defaults={"title": data.get("chapter_title", f"第{data['chapter']}章")},
    )
    section, _ = Section.objects.get_or_create(
        chapter=chapter,
        number=data["section"],
        defaults={"title": data.get("section_title", f"第{data['section']}节")},
    )
    supplied_section_title = data.get("section_title")
    if supplied_section_title and supplied_section_title != section.title:
        warnings.append(
            {
                "code": "section_title_conflict",
                "message": (
                    "Section title differs from the existing curriculum and was not overwritten."
                ),
            }
        )
    return subject, chapter, section, warnings


def _import_record(record: dict, batch: ContentImportBatch) -> str:
    data = record["data"]
    checksum = content_checksum(data)
    question = Question.objects.filter(external_id=data["external_id"]).first()
    latest_version = (
        question.versions.order_by("-version_number").first() if question is not None else None
    )
    if latest_version and latest_version.content_checksum == checksum:
        ContentImportItem.objects.create(
            batch=batch,
            external_id=data["external_id"],
            status=ContentImportItem.Status.SKIPPED,
            action="skipped",
            warnings=record["warnings"],
        )
        return "skipped"

    subject, chapter, section, curriculum_warnings = _curriculum(data)
    warnings = [*record["warnings"], *curriculum_warnings]
    if question is None:
        question = Question(
            external_id=data["external_id"],
            subject=subject,
            chapter=chapter,
            section=section,
            question_type=data["question_type"],
            status=Question.Status.PENDING_REVIEW,
        )
        question.full_clean()
        question.save()
        action = "created"
        version_number = 1
    else:
        action = "versioned"
        version_number = (latest_version.version_number if latest_version else 0) + 1

    option_order = [str(option["label"]).strip().upper() for option in data["options"]]
    source_answer = [str(label).strip().upper() for label in data["answer"]]
    canonical_answer = sorted(source_answer)
    version = QuestionVersion(
        question=question,
        version_number=version_number,
        stem=data["stem"],
        answer_schema={"type": data["question_type"], "answers": canonical_answer},
        canonical_answer=canonical_answer,
        presented_option_order=option_order,
        source_answer=source_answer,
        analysis=data.get("analysis", ""),
        difficulty=data.get("difficulty", ""),
        content_checksum=checksum,
        source_type=data["source_type"],
        year=data.get("year"),
        applicable_exam_edition=data.get("applicable_exam_edition", ""),
        review_status=_review_status(data),
        warnings=warnings,
    )
    version.full_clean()
    version.save()
    for sort_order, option in enumerate(data["options"], start=1):
        QuestionOption.objects.create(
            question_version=version,
            label=option["label"],
            text=option["text"],
            sort_order=sort_order,
        )

    if question.status != Question.Status.PUBLISHED:
        Question.objects.filter(pk=question.pk).update(
            current_version=version,
            status=Question.Status.PENDING_REVIEW,
        )

    source = _source_material(data)
    ContentProvenance.objects.create(
        content_type="question_version",
        content_object_id=version.id,
        source_material=source,
        source_page=data["source_page"],
        source_question_number=str(data.get("question_number", "")),
        extraction_confidence=data["extraction_confidence"],
        content_origin=data["content_origin"],
        notes="",
    )
    ContentImportItem.objects.create(
        batch=batch,
        external_id=data["external_id"],
        status=(
            ContentImportItem.Status.CREATED
            if action == "created"
            else ContentImportItem.Status.VERSIONED
        ),
        action=action,
        warnings=warnings,
    )
    return action


def _action_summary(actions: list[dict], validation_report: dict) -> dict:
    counts = Counter(action["action"] for action in actions)
    return {
        **validation_report,
        "created": counts["created"],
        "versioned": counts["versioned"],
        "skipped": counts["skipped"],
        "warning": sum(bool(action["warnings"]) for action in actions),
        "error": validation_report["error_count"],
        "actions": actions,
    }


def dry_run_import(result: ValidationResult) -> dict:
    actions = _plan_actions(result)
    return _action_summary(actions, result.report)


def commit_import(
    result: ValidationResult, batch_id: uuid.UUID | None = None
) -> tuple[ContentImportBatch, dict]:
    if result.has_errors:
        raise ContentValidationError(result.report)

    with transaction.atomic():
        chosen_batch_id = batch_id or uuid.uuid4()
        if ContentImportBatch.objects.filter(pk=chosen_batch_id).exists():
            raise ValidationError("Content import batch ID already exists and cannot be reused.")
        batch = ContentImportBatch.objects.create(
            id=chosen_batch_id,
            source_name=result.path.name,
            source_checksum=result.source_checksum,
            status=ContentImportBatch.Status.RUNNING,
            started_at=timezone.now(),
        )
        actions = []
        for record in (item for item in result.records if not item["errors"]):
            with transaction.atomic():
                action = _import_record(record, batch)
            actions.append(
                {
                    "line_number": record["line_number"],
                    "external_id": record["data"]["external_id"],
                    "action": action,
                    "warnings": record["warnings"],
                }
            )

        report = _action_summary(actions, result.report)
        batch.status = ContentImportBatch.Status.COMPLETED
        batch.completed_at = timezone.now()
        batch.created_count = report["created"]
        batch.updated_count = report["versioned"]
        batch.skipped_count = report["skipped"]
        batch.error_count = report["error"]
        batch.report = report
        batch.save()
        return batch, report


def write_report(report: dict, path: str | Path | None, report_name: str) -> Path:
    report_path = Path(path).resolve() if path else PRIVATE_REPORT_ROOT / report_name
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path


def terminal_summary(report: dict) -> str:
    return "\n".join(
        (
            f"total={report['total_count']}",
            f"valid={report['valid_count']}",
            f"warning={report.get('warning', report['warning_count'])}",
            f"error={report.get('error', report['error_count'])}",
            f"created={report.get('created', 0)}",
            f"versioned={report.get('versioned', 0)}",
            f"skipped={report.get('skipped', 0)}",
            f"chapters={json.dumps(report['chapter_counts'], ensure_ascii=False, sort_keys=True)}",
            "question_types="
            + json.dumps(report["question_type_counts"], ensure_ascii=False, sort_keys=True),
            f"duplicate_candidates={report['duplicate_candidate_count']}",
            f"answer_conflicts={report['answer_conflict_count']}",
        )
    )
