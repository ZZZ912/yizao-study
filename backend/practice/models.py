import uuid

from django.conf import settings
from django.db import models

from questions.models import Question, QuestionVersion


class AnswerAttempt(models.Model):
    class WrongReason(models.TextChoices):
        UNKNOWN = "", "未选择"
        CONCEPT = "concept", "概念不清"
        CONFUSION = "confusion", "选项混淆"
        CALCULATION = "calculation", "计算失误"
        READING = "reading", "审题失误"
        MEMORY = "memory", "记忆不牢"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="answer_attempts",
    )
    question_version = models.ForeignKey(
        QuestionVersion,
        on_delete=models.PROTECT,
        related_name="answer_attempts",
    )
    selected_answer = models.JSONField(default=list)
    is_correct = models.BooleanField()
    elapsed_seconds = models.PositiveIntegerField(default=0)
    wrong_reason = models.CharField(
        max_length=24,
        choices=WrongReason.choices,
        blank=True,
        default=WrongReason.UNKNOWN,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "practice_answer_attempt"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("user", "created_at")),
            models.Index(fields=("user", "is_correct")),
        ]


class WrongQuestion(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "待复习"
        MASTERED = "mastered", "已掌握"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="wrong_questions",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name="wrong_records",
    )
    wrong_count = models.PositiveIntegerField(default=1)
    correct_streak = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    next_review_at = models.DateTimeField()
    last_attempt_at = models.DateTimeField()
    last_wrong_reason = models.CharField(max_length=24, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "practice_wrong_question"
        ordering = ("next_review_at", "-wrong_count")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "question"), name="wrong_question_user_question_uq"
            )
        ]
        indexes = [models.Index(fields=("user", "status", "next_review_at"))]
