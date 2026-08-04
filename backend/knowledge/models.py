import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower

from curriculum.models import Section


class KnowledgePoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name="knowledge_points")
    code = models.SlugField(max_length=80)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    current_version = models.ForeignKey(
        "KnowledgeVersion",
        on_delete=models.PROTECT,
        related_name="current_for_points",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "knowledge_point"
        ordering = ("section", "code")
        constraints = [
            models.UniqueConstraint(
                models.F("section"),
                Lower("code"),
                name="knowledge_section_code_ci_uq",
            )
        ]

    def save(self, *args, **kwargs):
        self.code = self.code.strip().lower()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class KnowledgeVersion(models.Model):
    class ReviewStatus(models.TextChoices):
        PENDING_REVIEW = "pending_review", "待审核"
        REVIEWED = "reviewed", "已复核"
        PUBLISHED = "published", "已发布"
        DISPUTED = "disputed", "有争议"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    knowledge_point = models.ForeignKey(
        KnowledgePoint,
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version_number = models.PositiveIntegerField()
    summary = models.TextField()
    content_blocks = models.JSONField(default=list)
    applicable_exam_edition = models.CharField(max_length=80, default="2025大纲/2026考试")
    source_type = models.CharField(max_length=80, default="original_synthesis")
    content_checksum = models.CharField(max_length=64)
    review_status = models.CharField(
        max_length=24,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING_REVIEW,
    )
    immutable_after_publish = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_version"
        ordering = ("knowledge_point", "version_number")
        constraints = [
            models.UniqueConstraint(
                fields=("knowledge_point", "version_number"),
                name="knowledge_version_number_uq",
            )
        ]

    def clean(self):
        super().clean()
        if not isinstance(self.content_blocks, list):
            raise ValidationError({"content_blocks": "Content blocks must be an array."})

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).first()
            if previous and (
                previous.review_status == self.ReviewStatus.PUBLISHED
                or previous.immutable_after_publish
            ):
                protected = (
                    "knowledge_point_id",
                    "version_number",
                    "summary",
                    "content_blocks",
                    "applicable_exam_edition",
                    "source_type",
                    "content_checksum",
                    "review_status",
                )
                if any(getattr(previous, field) != getattr(self, field) for field in protected):
                    raise ValidationError("Published knowledge versions are immutable.")
        if self.review_status == self.ReviewStatus.PUBLISHED:
            self.immutable_after_publish = True
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.review_status == self.ReviewStatus.PUBLISHED or self.immutable_after_publish:
            raise ValidationError("Published knowledge versions cannot be deleted.")
        return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.knowledge_point.code} v{self.version_number}"
