import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower

from curriculum.models import Chapter, Section, Subject


class Question(models.Model):
    class Type(models.TextChoices):
        SINGLE_CHOICE = "single_choice", "单选题"
        MULTIPLE_CHOICE = "multiple_choice", "多选题"

    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        PENDING_REVIEW = "pending_review", "待审核"
        PUBLISHED = "published", "已发布"
        DISPUTED = "disputed", "有争议"
        OBSOLETE = "obsolete", "已废止"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=160)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="questions")
    chapter = models.ForeignKey(Chapter, on_delete=models.PROTECT, related_name="questions")
    section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name="questions")
    question_type = models.CharField(max_length=24, choices=Type.choices)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING_REVIEW)
    current_version = models.ForeignKey(
        "QuestionVersion",
        on_delete=models.PROTECT,
        related_name="current_for_questions",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "questions_question"
        ordering = ("external_id",)
        indexes = [
            models.Index(fields=("subject", "chapter", "section")),
            models.Index(fields=("status", "question_type")),
        ]
        constraints = [
            models.UniqueConstraint(Lower("external_id"), name="question_external_id_ci_uq"),
        ]

    def save(self, *args, **kwargs):
        self.external_id = self.external_id.strip().lower()
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        errors = {}
        if self.chapter_id and self.subject_id and self.chapter.subject_id != self.subject_id:
            errors["chapter"] = "Chapter does not belong to the selected subject."
        if self.section_id and self.chapter_id and self.section.chapter_id != self.chapter_id:
            errors["section"] = "Section does not belong to the selected chapter."
        if self.current_version_id and self.current_version.question_id != self.id:
            errors["current_version"] = "Current version must belong to this question."
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return self.external_id


class QuestionVersion(models.Model):
    class ReviewStatus(models.TextChoices):
        PENDING_REVIEW = "pending_review", "待审核"
        REVIEWED = "reviewed", "已复核"
        DISPUTED = "disputed", "有争议"
        PUBLISHED = "published", "已发布"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="versions")
    version_number = models.PositiveIntegerField()
    stem = models.TextField()
    answer_schema = models.JSONField(default=dict)
    canonical_answer = models.JSONField(default=list)
    presented_option_order = models.JSONField(default=list)
    source_answer = models.JSONField(default=list)
    analysis = models.TextField(blank=True)
    difficulty = models.CharField(max_length=24, blank=True)
    content_checksum = models.CharField(max_length=64)
    source_type = models.CharField(max_length=80)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    applicable_exam_edition = models.CharField(max_length=80, blank=True)
    review_status = models.CharField(
        max_length=24,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING_REVIEW,
    )
    warnings = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    immutable_after_publish = models.BooleanField(default=False)

    class Meta:
        db_table = "questions_question_version"
        ordering = ("question", "version_number")
        constraints = [
            models.UniqueConstraint(
                fields=("question", "version_number"), name="question_version_number_uq"
            )
        ]
        indexes = [
            models.Index(fields=("review_status", "source_type")),
            models.Index(fields=("content_checksum",)),
        ]

    def clean(self):
        super().clean()
        if not isinstance(self.answer_schema, dict):
            raise ValidationError({"answer_schema": "Answer schema must be an object."})
        for field_name in (
            "canonical_answer",
            "presented_option_order",
            "source_answer",
            "warnings",
        ):
            if not isinstance(getattr(self, field_name), list):
                raise ValidationError({field_name: "Value must be an array."})

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).first()
            if previous and (
                previous.review_status == self.ReviewStatus.PUBLISHED
                or previous.immutable_after_publish
            ):
                protected_fields = (
                    "question_id",
                    "version_number",
                    "stem",
                    "answer_schema",
                    "canonical_answer",
                    "presented_option_order",
                    "source_answer",
                    "analysis",
                    "difficulty",
                    "content_checksum",
                    "source_type",
                    "year",
                    "applicable_exam_edition",
                    "review_status",
                    "warnings",
                )
                if any(
                    getattr(previous, field) != getattr(self, field) for field in protected_fields
                ):
                    raise ValidationError("Published question versions are immutable.")
        if self.review_status == self.ReviewStatus.PUBLISHED:
            self.immutable_after_publish = True
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.review_status == self.ReviewStatus.PUBLISHED or self.immutable_after_publish:
            raise ValidationError("Published question versions cannot be deleted.")
        return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.question.external_id} v{self.version_number}"


class QuestionOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_version = models.ForeignKey(
        QuestionVersion,
        on_delete=models.PROTECT,
        related_name="options",
    )
    label = models.CharField(max_length=12)
    text = models.TextField()
    sort_order = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "questions_question_option"
        ordering = ("question_version", "sort_order")
        constraints = [
            models.UniqueConstraint(
                fields=("question_version", "label"), name="question_option_label_uq"
            ),
            models.UniqueConstraint(
                fields=("question_version", "sort_order"), name="question_option_order_uq"
            ),
        ]

    def save(self, *args, **kwargs):
        if (
            self.question_version.review_status == QuestionVersion.ReviewStatus.PUBLISHED
            or self.question_version.immutable_after_publish
        ):
            raise ValidationError("Options of a published question version are immutable.")
        self.label = self.label.strip().upper()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if (
            self.question_version.review_status == QuestionVersion.ReviewStatus.PUBLISHED
            or self.question_version.immutable_after_publish
        ):
            raise ValidationError("Options of a published question version are immutable.")
        return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.label}. {self.text[:40]}"
