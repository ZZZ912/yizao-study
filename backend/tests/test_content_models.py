import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from curriculum.models import Chapter, Section, Subject
from provenance.models import SourceMaterial
from questions.models import Question, QuestionVersion


@pytest.mark.django_db
def test_subject_and_question_identifiers_are_case_insensitively_unique():
    subject = Subject.objects.create(code="COST", title="原创科目")
    assert subject.code == "cost"
    with pytest.raises(IntegrityError), transaction.atomic():
        Subject.objects.bulk_create([Subject(code="Cost", title="重复科目")])

    chapter = Chapter.objects.create(subject=subject, number=1, title="原创章")
    section = Section.objects.create(chapter=chapter, number=1, title="原创节")
    Question.objects.create(
        external_id="CASE-ID",
        subject=subject,
        chapter=chapter,
        section=section,
        question_type=Question.Type.SINGLE_CHOICE,
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        Question.objects.bulk_create(
            [
                Question(
                    external_id="case-id",
                    subject=subject,
                    chapter=chapter,
                    section=section,
                    question_type=Question.Type.SINGLE_CHOICE,
                )
            ]
        )


@pytest.mark.django_db
def test_curriculum_constraints_and_json_round_trip():
    subject = Subject.objects.create(code="constraint", title="原创约束科目")
    chapter = Chapter.objects.create(subject=subject, number=1, title="原创章")
    with pytest.raises(IntegrityError), transaction.atomic():
        Chapter.objects.create(subject=subject, number=1, title="重复章")
    section = Section.objects.create(chapter=chapter, number=1, title="原创节")
    question = Question.objects.create(
        external_id="json-roundtrip",
        subject=subject,
        chapter=chapter,
        section=section,
        question_type=Question.Type.MULTIPLE_CHOICE,
    )
    version = QuestionVersion.objects.create(
        question=question,
        version_number=1,
        stem="原创JSON测试",
        answer_schema={"type": "multiple_choice", "answers": ["A", "C"]},
        canonical_answer=["A", "C"],
        presented_option_order=["C", "A", "B"],
        source_answer=["C", "A"],
        content_checksum="a" * 64,
        source_type="original_demo",
        warnings=[{"code": "原创警告", "details": {"line": 1}}],
    )
    version.refresh_from_db()
    assert version.answer_schema["answers"] == ["A", "C"]
    assert version.warnings[0]["details"] == {"line": 1}


@pytest.mark.django_db
def test_historical_version_protects_question_from_deletion():
    subject = Subject.objects.create(code="protect", title="原创保护科目")
    chapter = Chapter.objects.create(subject=subject, number=1, title="原创章")
    section = Section.objects.create(chapter=chapter, number=1, title="原创节")
    question = Question.objects.create(
        external_id="protected-question",
        subject=subject,
        chapter=chapter,
        section=section,
        question_type=Question.Type.SINGLE_CHOICE,
    )
    QuestionVersion.objects.create(
        question=question,
        version_number=1,
        stem="原创保护测试",
        answer_schema={"answers": ["A"]},
        canonical_answer=["A"],
        presented_option_order=["A", "B"],
        source_answer=["A"],
        content_checksum="b" * 64,
        source_type="original_demo",
    )
    with pytest.raises(ProtectedError):
        question.delete()


@pytest.mark.django_db
def test_private_source_rejects_public_flag_and_absolute_reference():
    with pytest.raises(IntegrityError), transaction.atomic():
        SourceMaterial.objects.create(
            external_id="private-public-conflict",
            file_name="source.pdf",
            source_type="commercial",
            rights_scope="private_personal_use",
            public_repo_allowed=True,
        )

    source = SourceMaterial(
        external_id=str(uuid.uuid4()),
        file_name="source.pdf",
        source_type="commercial",
        rights_scope="private_personal_use",
        public_repo_allowed=False,
        private_reference="C:\\private\\source.pdf",
    )
    with pytest.raises(ValidationError, match="logical identifier"):
        source.full_clean()
