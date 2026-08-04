from datetime import date

from django.db.models import Count, Exists, OuterRef, Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from curriculum.models import Section, Subject
from knowledge.models import KnowledgePoint, KnowledgeVersion
from questions.models import Question, QuestionVersion

from .models import AnswerAttempt, WrongQuestion
from .services import grade_answer, question_payload

EXAM_DATE = date(2026, 10, 17)


def published_questions():
    return Question.objects.filter(
        status=Question.Status.PUBLISHED,
        current_version__review_status=QuestionVersion.ReviewStatus.PUBLISHED,
    ).select_related("subject", "chapter", "section", "current_version")


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.localtime()
        attempts = AnswerAttempt.objects.filter(user=request.user)
        today_attempts = attempts.filter(created_at__date=now.date())
        today_total = today_attempts.count()
        today_correct = today_attempts.filter(is_correct=True).count()
        due = WrongQuestion.objects.filter(
            user=request.user,
            status=WrongQuestion.Status.ACTIVE,
            next_review_at__lte=now,
        ).count()
        question_count = published_questions().count()
        next_section = (
            Section.objects.filter(questions__status=Question.Status.PUBLISHED)
            .annotate(published_count=Count("questions", distinct=True))
            .select_related("chapter__subject")
            .order_by("chapter__subject__code", "chapter__number", "number")
            .first()
        )
        return Response(
            {
                "data": {
                    "exam": {
                        "date": EXAM_DATE.isoformat(),
                        "days_remaining": max((EXAM_DATE - now.date()).days, 0),
                        "location": "湖北武汉",
                        "specialty": "土木建筑工程",
                        "syllabus": "2025年版考试大纲（2026年度考试适用）",
                    },
                    "today": {
                        "answered": today_total,
                        "correct": today_correct,
                        "accuracy": round(today_correct / today_total * 100) if today_total else 0,
                        "due_reviews": due,
                        "target_questions": 20,
                    },
                    "question_count": question_count,
                    "wrong_count": WrongQuestion.objects.filter(
                        user=request.user, status=WrongQuestion.Status.ACTIVE
                    ).count(),
                    "next_section": (
                        {
                            "id": str(next_section.id),
                            "subject": next_section.chapter.subject.title,
                            "chapter": next_section.chapter.title,
                            "title": next_section.title,
                            "question_count": next_section.published_count,
                        }
                        if next_section
                        else None
                    ),
                }
            }
        )


class SubjectListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subjects = Subject.objects.filter(is_active=True).annotate(
            published_questions=Count(
                "questions",
                filter=Q(questions__status=Question.Status.PUBLISHED),
                distinct=True,
            ),
            knowledge_count=Count(
                "chapters__sections__knowledge_points",
                filter=Q(
                    chapters__sections__knowledge_points__current_version__review_status=(
                        KnowledgeVersion.ReviewStatus.PUBLISHED
                    )
                ),
                distinct=True,
            ),
        )
        data = [
            {
                "id": str(subject.id),
                "code": subject.code,
                "title": subject.title,
                "question_count": subject.published_questions,
                "knowledge_count": subject.knowledge_count,
            }
            for subject in subjects
        ]
        return Response({"data": data})


class ChapterListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, subject_code):
        subject = Subject.objects.filter(code=subject_code, is_active=True).first()
        if not subject:
            raise NotFound("科目不存在。")
        chapters = subject.chapters.prefetch_related("sections").order_by("number")
        data = []
        for chapter in chapters:
            sections = []
            for section in chapter.sections.all():
                question_count = published_questions().filter(section=section).count()
                knowledge_count = KnowledgePoint.objects.filter(
                    section=section,
                    current_version__review_status=KnowledgeVersion.ReviewStatus.PUBLISHED,
                ).count()
                sections.append(
                    {
                        "id": str(section.id),
                        "number": section.number,
                        "title": section.title,
                        "question_count": question_count,
                        "knowledge_count": knowledge_count,
                    }
                )
            data.append(
                {
                    "number": chapter.number,
                    "title": chapter.title,
                    "sections": sections,
                }
            )
        return Response({"data": {"subject": subject.title, "chapters": data}})


class SectionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, section_id):
        section = Section.objects.select_related("chapter__subject").filter(pk=section_id).first()
        if not section:
            raise NotFound("小节不存在。")
        points = KnowledgePoint.objects.filter(
            section=section,
            current_version__review_status=KnowledgeVersion.ReviewStatus.PUBLISHED,
        ).select_related("current_version")
        return Response(
            {
                "data": {
                    "id": str(section.id),
                    "subject": {
                        "code": section.chapter.subject.code,
                        "title": section.chapter.subject.title,
                    },
                    "chapter": {
                        "number": section.chapter.number,
                        "title": section.chapter.title,
                    },
                    "number": section.number,
                    "title": section.title,
                    "question_count": published_questions().filter(section=section).count(),
                    "knowledge_points": [
                        {
                            "id": str(point.id),
                            "title": point.title,
                            "summary": point.current_version.summary,
                            "content_blocks": point.current_version.content_blocks,
                            "exam_edition": point.current_version.applicable_exam_edition,
                        }
                        for point in points.order_by("sort_order", "code")
                    ],
                }
            }
        )


class NextQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = published_questions().prefetch_related("current_version__options")
        subject_code = request.query_params.get("subject")
        section_id = request.query_params.get("section")
        mode = request.query_params.get("mode", "practice")
        if subject_code:
            queryset = queryset.filter(subject__code=subject_code)
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if mode == "review":
            due_ids = WrongQuestion.objects.filter(
                user=request.user,
                status=WrongQuestion.Status.ACTIVE,
                next_review_at__lte=timezone.now(),
            ).values("question_id")
            queryset = queryset.filter(id__in=due_ids)
        else:
            attempted = AnswerAttempt.objects.filter(
                user=request.user,
                question_version__question_id=OuterRef("pk"),
            )
            queryset = queryset.annotate(attempted=Exists(attempted)).order_by(
                "attempted", "chapter__number", "section__number", "external_id"
            )
        question = queryset.first()
        return Response({"data": question_payload(question) if question else None})


class SubmitAttemptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        version_id = request.data.get("question_version_id")
        selected = request.data.get("selected_answer")
        elapsed = request.data.get("elapsed_seconds", 0)
        reason = request.data.get("wrong_reason", "")
        if not isinstance(selected, list):
            raise ValidationError({"selected_answer": ["答案必须是数组。"]})
        if reason not in {choice for choice, _ in AnswerAttempt.WrongReason.choices}:
            raise ValidationError({"wrong_reason": ["错因类型无效。"]})
        version = (
            QuestionVersion.objects.select_related("question")
            .prefetch_related("options")
            .filter(
                pk=version_id,
                review_status=QuestionVersion.ReviewStatus.PUBLISHED,
                question__status=Question.Status.PUBLISHED,
            )
            .first()
        )
        if not version:
            raise NotFound("题目不存在或尚未发布。")
        option_labels = {option.label for option in version.options.all()}
        normalized = {str(label).strip().upper() for label in selected}
        if not normalized or not normalized.issubset(option_labels):
            raise ValidationError({"selected_answer": ["请选择有效选项。"]})
        if version.question.question_type == Question.Type.SINGLE_CHOICE and len(normalized) != 1:
            raise ValidationError({"selected_answer": ["单选题只能选择一个答案。"]})
        try:
            elapsed_value = int(elapsed)
        except (TypeError, ValueError) as exc:
            raise ValidationError({"elapsed_seconds": ["答题用时必须是整数。"]}) from exc

        attempt, wrong_record = grade_answer(
            user=request.user,
            version=version,
            selected_answer=list(normalized),
            elapsed=elapsed_value,
            reason=reason,
        )
        return Response(
            {
                "data": {
                    "attempt_id": str(attempt.id),
                    "is_correct": attempt.is_correct,
                    "selected_answer": attempt.selected_answer,
                    "correct_answer": version.canonical_answer,
                    "analysis": version.analysis,
                    "options": [
                        {
                            "label": option.label,
                            "text": option.text,
                            "is_correct": option.label in version.canonical_answer,
                        }
                        for option in version.options.order_by("sort_order")
                    ],
                    "review": (
                        {
                            "status": wrong_record.status,
                            "wrong_count": wrong_record.wrong_count,
                            "next_review_at": wrong_record.next_review_at.isoformat(),
                        }
                        if wrong_record
                        else None
                    ),
                }
            }
        )


class UpdateWrongReasonView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, attempt_id):
        reason = request.data.get("wrong_reason", "")
        allowed = {choice for choice, _ in AnswerAttempt.WrongReason.choices if choice}
        if reason not in allowed:
            raise ValidationError({"wrong_reason": ["请选择有效错因。"]})
        attempt = AnswerAttempt.objects.filter(pk=attempt_id, user=request.user).first()
        if not attempt or attempt.is_correct:
            raise NotFound("错误答题记录不存在。")
        attempt.wrong_reason = reason
        attempt.save(update_fields=("wrong_reason",))
        WrongQuestion.objects.filter(
            user=request.user,
            question=attempt.question_version.question,
        ).update(last_wrong_reason=reason)
        return Response({"data": {"wrong_reason": reason}})


class WrongQuestionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = WrongQuestion.objects.filter(user=request.user).select_related(
            "question__subject", "question__section", "question__current_version"
        )[:100]
        return Response(
            {
                "data": [
                    {
                        "id": str(record.id),
                        "question_id": str(record.question_id),
                        "stem": record.question.current_version.stem,
                        "subject": record.question.subject.title,
                        "section": record.question.section.title,
                        "wrong_count": record.wrong_count,
                        "correct_streak": record.correct_streak,
                        "status": record.status,
                        "next_review_at": record.next_review_at.isoformat(),
                        "wrong_reason": record.last_wrong_reason,
                    }
                    for record in records
                ]
            }
        )
