import copy
import uuid
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError

from curriculum.models import Chapter, Section, Subject
from provenance.ingestion import commit_import, validate_jsonl
from provenance.models import (
    ContentImportBatch,
    ContentImportItem,
    ContentProvenance,
    SourceMaterial,
)
from questions.models import Question, QuestionOption, QuestionVersion
from tests.test_content_schema import demo_question, write_jsonl


@pytest.mark.django_db
def test_default_import_is_dry_run_and_writes_nothing(tmp_path):
    path = write_jsonl(tmp_path / "dry.jsonl", [demo_question()])
    call_command("import_content", path, report=tmp_path / "report.json")
    assert Question.objects.count() == 0
    assert ContentImportBatch.objects.count() == 0
    assert SourceMaterial.objects.count() == 0


@pytest.mark.django_db
def test_commit_creates_question_version_options_provenance_and_batch(tmp_path):
    path = write_jsonl(tmp_path / "commit.jsonl", [demo_question()])
    batch_id = uuid.uuid4()
    call_command(
        "import_content",
        path,
        commit=True,
        batch_id=str(batch_id),
        report=tmp_path / "report.json",
    )
    question = Question.objects.get()
    version = QuestionVersion.objects.get()
    batch = ContentImportBatch.objects.get(pk=batch_id)
    assert question.current_version == version
    assert question.status == Question.Status.PENDING_REVIEW
    assert version.presented_option_order == ["A", "B", "C"]
    assert version.canonical_answer == ["A"]
    assert QuestionOption.objects.filter(question_version=version).count() == 3
    assert ContentProvenance.objects.get().content_object_id == version.id
    assert batch.created_count == 1
    assert batch.report["created"] == 1


@pytest.mark.django_db
def test_idempotent_repeat_skips_same_checksum(tmp_path):
    path = write_jsonl(tmp_path / "repeat.jsonl", [demo_question()])
    call_command("import_content", path, commit=True, report=tmp_path / "first.json")
    call_command("import_content", path, commit=True, report=tmp_path / "second.json")
    assert Question.objects.count() == 1
    assert QuestionVersion.objects.count() == 1
    assert ContentImportBatch.objects.order_by("started_at").last().skipped_count == 1
    assert ContentImportItem.objects.filter(action="skipped").count() == 1


@pytest.mark.django_db
def test_official_subject_title_reuses_canonical_curriculum_subject(tmp_path):
    pricing = Subject.objects.create(code="pricing", title="建设工程计价")
    record = demo_question(external_id="pricing-canonical-001")
    record["subject"] = "建设工程计价"
    path = write_jsonl(tmp_path / "pricing.jsonl", [record])

    call_command("import_content", path, commit=True, report=tmp_path / "report.json")

    question = Question.objects.get()
    assert question.subject == pricing
    assert Subject.objects.count() == 1


@pytest.mark.django_db
def test_changed_content_creates_new_version_without_overwriting_old(tmp_path):
    first = demo_question()
    path = write_jsonl(tmp_path / "first.jsonl", [first])
    call_command("import_content", path, commit=True, report=tmp_path / "first-report.json")
    old_version = QuestionVersion.objects.get()

    changed = copy.deepcopy(first)
    changed["stem"] = "原创测试题干的第二个版本"
    write_jsonl(path, [changed])
    call_command("import_content", path, commit=True, report=tmp_path / "second-report.json")

    question = Question.objects.get()
    assert question.versions.count() == 2
    assert question.current_version.version_number == 2
    old_version.refresh_from_db()
    assert old_version.stem == first["stem"]


@pytest.mark.django_db
def test_published_version_is_immutable_and_new_import_does_not_replace_live_version(tmp_path):
    first = demo_question()
    path = write_jsonl(tmp_path / "published.jsonl", [first])
    call_command("import_content", path, commit=True, report=tmp_path / "first.json")
    question = Question.objects.get()
    live_version = question.current_version
    live_version.review_status = QuestionVersion.ReviewStatus.PUBLISHED
    live_version.save()
    Question.objects.filter(pk=question.pk).update(status=Question.Status.PUBLISHED)

    live_version.stem = "禁止原地修改"
    with pytest.raises(ValidationError, match="immutable"):
        live_version.save()
    option = live_version.options.first()
    option.text = "禁止修改已发布选项"
    with pytest.raises(ValidationError, match="immutable"):
        option.save()
    with pytest.raises(ValidationError, match="cannot be deleted"):
        live_version.delete()

    changed = copy.deepcopy(first)
    changed["stem"] = "等待审核的新版本"
    write_jsonl(path, [changed])
    call_command("import_content", path, commit=True, report=tmp_path / "second.json")
    question.refresh_from_db()
    assert question.current_version_id == live_version.id
    assert question.versions.count() == 2
    assert question.versions.get(version_number=2).review_status == "pending_review"


@pytest.mark.django_db
def test_commercial_content_is_forced_to_pending_review(tmp_path):
    record = demo_question(external_id="commercial-001")
    record.update(
        {
            "source_type": "commercial_section_bank",
            "rights_scope": "private_personal_use",
            "public_repo_allowed": False,
            "content_origin": "third_party_commercial",
            "review_status": "reviewed",
        }
    )
    path = write_jsonl(tmp_path / "commercial.private.jsonl", [record])
    call_command("import_content", path, commit=True, report=tmp_path / "report.json")
    assert (
        QuestionVersion.objects.get().review_status == QuestionVersion.ReviewStatus.PENDING_REVIEW
    )
    assert SourceMaterial.objects.get().public_repo_allowed is False


@pytest.mark.django_db
def test_database_error_rolls_back_entire_batch(monkeypatch, tmp_path):
    records = [
        demo_question(external_id="rollback-001"),
        demo_question(external_id="rollback-002"),
    ]
    result = validate_jsonl(write_jsonl(tmp_path / "rollback.jsonl", records))
    from provenance import ingestion

    original_import_record = ingestion._import_record
    calls = 0

    def fail_second(record, batch):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("forced batch failure")
        return original_import_record(record, batch)

    monkeypatch.setattr(ingestion, "_import_record", fail_second)
    with pytest.raises(RuntimeError, match="forced batch failure"):
        commit_import(result)
    assert Question.objects.count() == 0
    assert QuestionVersion.objects.count() == 0
    assert ContentImportBatch.objects.count() == 0


@pytest.mark.django_db
def test_validation_error_reports_jsonl_line_and_writes_no_database_content(tmp_path, capsys):
    invalid = demo_question(external_id="invalid-answer")
    invalid["answer"] = ["Z"]
    path = write_jsonl(tmp_path / "invalid.jsonl", [invalid])
    with pytest.raises(CommandError, match="no database content"):
        call_command("import_content", path, commit=True, report=tmp_path / "report.json")
    assert "line=1" in capsys.readouterr().err
    assert Question.objects.count() == 0
    assert Subject.objects.count() == 0
    assert Chapter.objects.count() == 0
    assert Section.objects.count() == 0


@pytest.mark.django_db
def test_invalid_dry_run_plans_valid_records_but_writes_nothing(tmp_path, capsys):
    invalid = demo_question(external_id="invalid-dry-run")
    invalid["answer"] = ["Z"]
    path = write_jsonl(
        tmp_path / "partially-invalid.jsonl",
        [demo_question(external_id="valid-dry-run"), invalid],
    )

    call_command("import_content", path, dry_run=True, report=tmp_path / "report.json")

    output = capsys.readouterr()
    assert "Dry-run continues with valid records only" in output.err
    assert "valid=1" in output.out
    assert "error=1" in output.out
    assert "created=1" in output.out
    assert Question.objects.count() == 0
    assert ContentImportBatch.objects.count() == 0


def test_duplicate_detection_is_conservative_and_keeps_order_and_answer_conflicts():
    fixture = (
        Path(__file__).resolve().parents[2] / "content" / "fixtures" / "original_demo_valid.jsonl"
    )
    report = validate_jsonl(fixture).report
    group_types = {group["type"] for group in report["duplicate_groups"]}
    assert "external_id_content_conflict" in group_types
    assert "same_stem_answer_conflict" in group_types
    assert "same_stem_option_order_changed" in group_types
    assert report["duplicate_candidate_count"] >= 3
