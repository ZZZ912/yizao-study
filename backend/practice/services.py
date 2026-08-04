from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from questions.models import Question, QuestionVersion

from .models import AnswerAttempt, WrongQuestion


def question_payload(question: Question) -> dict:
    version = question.current_version
    return {
        "id": str(question.id),
        "version_id": str(version.id),
        "external_id": question.external_id,
        "question_type": question.question_type,
        "stem": version.stem,
        "options": [
            {"label": option.label, "text": option.text}
            for option in version.options.order_by("sort_order")
        ],
        "difficulty": version.difficulty,
        "subject": {"code": question.subject.code, "title": question.subject.title},
        "chapter": {"number": question.chapter.number, "title": question.chapter.title},
        "section": {
            "id": str(question.section_id),
            "number": question.section.number,
            "title": question.section.title,
        },
    }


def grade_answer(
    *, user, version: QuestionVersion, selected_answer: list[str], elapsed: int, reason: str
):
    normalized = sorted({str(label).strip().upper() for label in selected_answer})
    correct_answer = sorted(version.canonical_answer)
    is_correct = normalized == correct_answer
    now = timezone.now()

    with transaction.atomic():
        attempt = AnswerAttempt.objects.create(
            user=user,
            question_version=version,
            selected_answer=normalized,
            is_correct=is_correct,
            elapsed_seconds=max(0, min(elapsed, 7200)),
            wrong_reason="" if is_correct else reason,
        )
        wrong_record = WrongQuestion.objects.filter(
            user=user,
            question=version.question,
        ).first()
        if not is_correct:
            if wrong_record:
                wrong_record.wrong_count += 1
                wrong_record.correct_streak = 0
                wrong_record.status = WrongQuestion.Status.ACTIVE
                wrong_record.next_review_at = now + timedelta(days=1)
                wrong_record.last_attempt_at = now
                wrong_record.last_wrong_reason = reason
                wrong_record.save()
            else:
                wrong_record = WrongQuestion.objects.create(
                    user=user,
                    question=version.question,
                    next_review_at=now + timedelta(days=1),
                    last_attempt_at=now,
                    last_wrong_reason=reason,
                )
        elif wrong_record:
            wrong_record.correct_streak += 1
            intervals = (2, 4, 7)
            interval = intervals[min(wrong_record.correct_streak - 1, len(intervals) - 1)]
            wrong_record.next_review_at = now + timedelta(days=interval)
            wrong_record.last_attempt_at = now
            if wrong_record.correct_streak >= 3:
                wrong_record.status = WrongQuestion.Status.MASTERED
            wrong_record.save()

    return attempt, wrong_record
