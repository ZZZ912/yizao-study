import pytest
from django.contrib import admin
from django.core.management import call_command

from questions.admin import (
    mark_questions_disputed,
    mark_versions_reviewed,
    return_questions_pending,
)
from questions.models import Question, QuestionVersion
from tests.test_content_schema import demo_question, write_jsonl


def test_review_models_are_registered_without_a_publish_action():
    question_admin = admin.site._registry[Question]
    version_admin = admin.site._registry[QuestionVersion]

    assert mark_questions_disputed in question_admin.actions
    assert return_questions_pending in question_admin.actions
    assert mark_versions_reviewed in version_admin.actions
    assert all("publish" not in action.__name__ for action in version_admin.actions)


@pytest.mark.django_db
def test_review_action_cannot_change_a_published_version(tmp_path):
    path = write_jsonl(tmp_path / "admin.jsonl", [demo_question(external_id="admin-001")])
    call_command("import_content", path, commit=True, report=tmp_path / "report.json")
    version = QuestionVersion.objects.get()
    version.review_status = QuestionVersion.ReviewStatus.PUBLISHED
    version.save()

    mark_versions_reviewed(None, None, QuestionVersion.objects.all())

    version.refresh_from_db()
    assert version.review_status == QuestionVersion.ReviewStatus.PUBLISHED
