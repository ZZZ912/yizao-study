import json

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from curriculum.models import Section, Subject
from knowledge.models import KnowledgePoint, KnowledgeVersion
from practice.models import AnswerAttempt, SectionProgress, WrongQuestion
from questions.models import Question, QuestionVersion
from tests.test_content_schema import demo_question, write_jsonl


@pytest.fixture
def learner(django_user_model):
    return django_user_model.objects.create_user(
        email="learner@example.com",
        password="safe-test-password",
        display_name="学习者",
    )


@pytest.fixture
def api_client(learner):
    client = APIClient()
    client.force_authenticate(learner)
    return client


@pytest.fixture
def published_question(tmp_path):
    path = write_jsonl(tmp_path / "published.jsonl", [demo_question(external_id="learn-001")])
    call_command("import_content", path, commit=True, report=tmp_path / "report.json")
    question = Question.objects.get()
    version = question.current_version
    version.review_status = QuestionVersion.ReviewStatus.PUBLISHED
    version.save()
    question.status = Question.Status.PUBLISHED
    question.save()
    return question


@pytest.mark.django_db
def test_next_question_hides_answer_and_submit_creates_wrong_review(
    api_client, learner, published_question
):
    response = api_client.get("/api/v1/learning/questions/next/")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert "correct_answer" not in payload
    assert "analysis" not in payload

    response = api_client.post(
        "/api/v1/learning/attempts/",
        {
            "question_version_id": payload["version_id"],
            "selected_answer": ["B"],
            "elapsed_seconds": 15,
            "wrong_reason": "confusion",
        },
        format="json",
    )
    assert response.status_code == 200
    result = response.json()["data"]
    assert result["is_correct"] is False
    assert result["correct_answer"] == ["A"]
    assert AnswerAttempt.objects.filter(user=learner, is_correct=False).count() == 1
    wrong = WrongQuestion.objects.get(user=learner)
    assert wrong.wrong_count == 1
    assert wrong.last_wrong_reason == "confusion"


@pytest.mark.django_db
def test_three_correct_rereviews_mark_wrong_question_mastered(
    api_client, learner, published_question
):
    version_id = str(published_question.current_version_id)
    for answer in (["B"], ["A"], ["A"], ["A"]):
        response = api_client.post(
            "/api/v1/learning/attempts/",
            {
                "question_version_id": version_id,
                "selected_answer": answer,
                "elapsed_seconds": 5,
                "wrong_reason": "memory" if answer == ["B"] else "",
            },
            format="json",
        )
        assert response.status_code == 200
    wrong = WrongQuestion.objects.get(user=learner)
    assert wrong.correct_streak == 3
    assert wrong.status == WrongQuestion.Status.MASTERED


@pytest.mark.django_db
def test_dashboard_and_subject_endpoints_use_only_published_content(api_client, published_question):
    dashboard = api_client.get("/api/v1/learning/dashboard/")
    assert dashboard.status_code == 200
    assert dashboard.json()["data"]["question_count"] == 1
    assert dashboard.json()["data"]["exam"]["specialty"] == "土木建筑工程"
    subjects = api_client.get("/api/v1/learning/subjects/")
    assert subjects.status_code == 200
    assert subjects.json()["data"][0]["question_count"] == 1


def study_payload():
    return {
        "subjects": [
            {
                "code": "civil-measurement",
                "title": "建设工程技术与计量（土木建筑工程）",
                "chapters": [
                    {
                        "number": 1,
                        "title": "工程地质",
                        "sections": [{"number": 1, "title": "岩体特征"}],
                    }
                ],
            }
        ],
        "knowledge_points": [
            {
                "subject_code": "civil-measurement",
                "chapter": 1,
                "section": 1,
                "code": "rock-mass",
                "title": "岩体结构",
                "summary": "原创测试摘要。",
                "blocks": [{"type": "key_point", "content": "原创必背结论。"}],
            }
        ],
    }


@pytest.mark.django_db
def test_study_content_command_is_dry_by_default_and_idempotent_on_commit(tmp_path):
    path = tmp_path / "study.private.json"
    path.write_text(json.dumps(study_payload(), ensure_ascii=False), encoding="utf-8")
    call_command("import_study_content", path)
    assert KnowledgePoint.objects.count() == 0

    call_command("import_study_content", path, commit=True)
    call_command("import_study_content", path, commit=True)
    point = KnowledgePoint.objects.get()
    assert point.versions.count() == 1
    assert point.current_version.review_status == KnowledgeVersion.ReviewStatus.PUBLISHED

    updated = study_payload()
    updated["subjects"][0]["title"] = "建设工程技术与计量（土建）"
    updated["subjects"][0]["chapters"][0]["sections"][0]["title"] = "岩体工程特征"
    path.write_text(json.dumps(updated, ensure_ascii=False), encoding="utf-8")
    call_command("import_study_content", path, commit=True)
    assert Subject.objects.get().title == "建设工程技术与计量（土建）"
    assert Section.objects.get().title == "岩体工程特征"
    assert point.versions.count() == 1


@pytest.mark.django_db
def test_quick_card_and_section_progress_feed_the_daily_plan(api_client, learner, tmp_path):
    path = tmp_path / "study.private.json"
    path.write_text(json.dumps(study_payload(), ensure_ascii=False), encoding="utf-8")
    call_command("import_study_content", path, commit=True)
    point = KnowledgePoint.objects.select_related("section").get()

    card = api_client.get("/api/v1/learning/quick-card/?offset=0")
    assert card.status_code == 200
    assert card.json()["data"]["title"] == "岩体结构"
    assert card.json()["data"]["total"] == 1

    progress = api_client.post(
        f"/api/v1/learning/sections/{point.section_id}/progress/",
        {"status": "completed"},
        format="json",
    )
    assert progress.status_code == 200
    assert progress.json()["data"]["status"] == "completed"
    assert SectionProgress.objects.filter(
        user=learner,
        section=point.section,
        status=SectionProgress.Status.COMPLETED,
    ).exists()

    dashboard = api_client.get("/api/v1/learning/dashboard/").json()["data"]
    assert dashboard["knowledge_count"] == 1
    assert dashboard["section_count"] == 1
    assert dashboard["completed_section_count"] == 1
    assert dashboard["course_progress"] == 100
    assert dashboard["today"]["completed_lessons"] == 1


@pytest.mark.django_db
def test_published_knowledge_version_is_immutable(tmp_path):
    path = tmp_path / "study.private.json"
    path.write_text(json.dumps(study_payload(), ensure_ascii=False), encoding="utf-8")
    call_command("import_study_content", path, commit=True)
    version = KnowledgeVersion.objects.get()
    version.summary = "禁止原地修改"
    with pytest.raises(Exception, match="immutable"):
        version.save()
