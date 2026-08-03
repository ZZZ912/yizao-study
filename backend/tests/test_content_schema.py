import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from provenance.ingestion import validate_jsonl

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPO_ROOT / "content" / "schemas"
FIXTURE_ROOT = REPO_ROOT / "content" / "fixtures"


def test_all_content_schemas_are_valid_draft_2020_12_documents():
    for schema_path in SCHEMA_ROOT.glob("*.schema.json"):
        Draft202012Validator.check_schema(json.loads(schema_path.read_text(encoding="utf-8")))


def test_source_manifest_and_question_bank_schemas_accept_original_examples():
    schemas = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in SCHEMA_ROOT.glob("*.schema.json")
    }
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
    )
    manifest = [
        {
            "file_name": "original-demo.md",
            "pages": 2,
            "sha256": "a" * 64,
            "source_kind": "original_demo",
            "rights_scope": "original_public_fixture",
            "public_repo_allowed": True,
        }
    ]
    manifest_errors = list(
        Draft202012Validator(schemas["source_manifest.schema.json"]).iter_errors(manifest)
    )
    bank_errors = list(
        Draft202012Validator(schemas["question-bank.schema.json"], registry=registry).iter_errors(
            [demo_question()]
        )
    )
    assert manifest_errors == []
    assert bank_errors == []


def test_original_valid_fixture_passes_schema_and_semantic_validation():
    result = validate_jsonl(FIXTURE_ROOT / "original_demo_valid.jsonl")
    assert result.report["total_count"] == 8
    assert result.report["valid_count"] == 8
    assert result.report["error_count"] == 0
    assert result.report["question_type_counts"] == {
        "multiple_choice": 2,
        "single_choice": 6,
    }


def test_invalid_fixture_reports_exact_jsonl_lines_and_answer_error():
    result = validate_jsonl(FIXTURE_ROOT / "original_demo_invalid.jsonl")
    assert result.report["total_count"] == 2
    assert result.report["error_count"] == 2
    assert [issue["line_number"] for issue in result.report["issues"]] == [1, 2]
    first_codes = {error["code"] for error in result.report["issues"][0]["errors"]}
    assert "answer_not_in_options" in first_codes
    second_codes = {error["code"] for error in result.report["issues"][1]["errors"]}
    assert "schema_error" in second_codes


def test_single_and_multiple_choice_answer_cardinality(tmp_path):
    single = demo_question(external_id="single-invalid", question_type="single_choice")
    single["answer"] = ["A", "B"]
    multiple = demo_question(external_id="multiple-invalid", question_type="multiple_choice")
    multiple["answer"] = ["A"]
    path = write_jsonl(tmp_path / "cardinality.jsonl", [single, multiple])
    result = validate_jsonl(path)
    assert result.report["error_count"] == 2


def test_duplicate_option_labels_are_rejected(tmp_path):
    record = demo_question(external_id="duplicate-label")
    record["options"][1]["label"] = "A"
    result = validate_jsonl(write_jsonl(tmp_path / "duplicate-label.jsonl", [record]))
    assert result.report["error_count"] == 1
    error_codes = {error["code"] for error in result.report["issues"][0]["errors"]}
    assert "duplicate_option_label" in error_codes


def test_private_record_is_rejected_from_public_fixture_directory(tmp_path):
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    record = demo_question(external_id="private-in-fixture")
    record.update(
        {
            "rights_scope": "private_personal_use",
            "public_repo_allowed": False,
            "content_origin": "third_party_commercial",
        }
    )
    result = validate_jsonl(write_jsonl(fixture_dir / "private.jsonl", [record]))
    assert result.report["error_count"] == 1
    assert result.report["issues"][0]["errors"][0]["code"] == "private_content_in_public_fixture"


def demo_question(
    *,
    external_id: str = "demo-test-001",
    question_type: str = "single_choice",
) -> dict:
    answer = ["A"] if question_type == "single_choice" else ["A", "B"]
    return {
        "external_id": external_id,
        "subject": "原创测试科目",
        "chapter": 1,
        "chapter_title": "原创章节",
        "section": 1,
        "section_title": "原创小节",
        "question_number": 1,
        "question_type": question_type,
        "stem": f"原创测试题干 {external_id}",
        "options": [
            {"label": "A", "text": "原创选项甲"},
            {"label": "B", "text": "原创选项乙"},
            {"label": "C", "text": "原创选项丙"},
        ],
        "answer": answer,
        "analysis": "原创测试解析。",
        "source_file": "original-test.md",
        "source_page": 1,
        "source_type": "original_demo",
        "rights_scope": "original_public_fixture",
        "public_repo_allowed": True,
        "content_origin": "original",
        "extraction_method": "manual_original",
        "extraction_confidence": 1.0,
        "review_status": "pending_review",
        "warnings": [],
    }


def write_jsonl(path: Path, records: list[dict]) -> Path:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )
    return path
