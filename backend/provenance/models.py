import re
import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


def _validate_private_reference(value: str) -> None:
    if not value:
        return
    if "://" in value or value.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", value):
        raise ValidationError(
            "Private reference must be an internal logical identifier, not a URL or path."
        )


class SourceMaterial(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=160, unique=True)
    file_name = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64, blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    source_type = models.CharField(max_length=80)
    institution = models.CharField(max_length=160, blank=True)
    title = models.CharField(max_length=255, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    rights_scope = models.CharField(max_length=80)
    public_repo_allowed = models.BooleanField(default=False)
    private_reference = models.CharField(
        max_length=255,
        blank=True,
        validators=[_validate_private_reference],
    )
    extraction_method = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "provenance_source_material"
        ordering = ("file_name",)
        constraints = [
            models.CheckConstraint(
                condition=~Q(rights_scope="private_personal_use", public_repo_allowed=True),
                name="private_source_not_public_ck",
            )
        ]

    def clean(self):
        super().clean()
        if "/" in self.file_name or "\\" in self.file_name:
            raise ValidationError({"file_name": "Store a file name only, never a path."})
        if self.sha256 and (
            len(self.sha256) != 64 or not re.fullmatch(r"[0-9a-fA-F]{64}", self.sha256)
        ):
            raise ValidationError({"sha256": "SHA256 must contain 64 hexadecimal characters."})
        if not isinstance(self.metadata, dict):
            raise ValidationError({"metadata": "Metadata must be an object."})

    def __str__(self) -> str:
        return self.file_name


class ContentProvenance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.CharField(max_length=80)
    content_object_id = models.UUIDField()
    source_material = models.ForeignKey(
        SourceMaterial,
        on_delete=models.PROTECT,
        related_name="content_links",
    )
    source_page = models.PositiveIntegerField()
    source_question_number = models.CharField(max_length=80, blank=True)
    extraction_confidence = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    content_origin = models.CharField(max_length=80)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "provenance_content_provenance"
        ordering = ("content_type", "content_object_id", "source_page")
        indexes = [
            models.Index(fields=("content_type", "content_object_id")),
            models.Index(fields=("extraction_confidence",)),
        ]

    def __str__(self) -> str:
        return f"{self.content_type}:{self.content_object_id}"


class ContentImportBatch(models.Model):
    class Status(models.TextChoices):
        DRY_RUN = "dry_run", "试运行"
        RUNNING = "running", "运行中"
        COMPLETED = "completed", "已完成"
        FAILED = "failed", "失败"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_name = models.CharField(max_length=255)
    source_checksum = models.CharField(max_length=64)
    status = models.CharField(max_length=24, choices=Status.choices)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    report = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "provenance_content_import_batch"
        ordering = ("-started_at",)

    def __str__(self) -> str:
        return f"{self.source_name} ({self.id})"


class ContentImportItem(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "已创建"
        VERSIONED = "versioned", "已创建版本"
        SKIPPED = "skipped", "已跳过"
        WARNING = "warning", "有警告"
        ERROR = "error", "错误"

    batch = models.ForeignKey(
        ContentImportBatch,
        on_delete=models.PROTECT,
        related_name="items",
    )
    external_id = models.CharField(max_length=160)
    status = models.CharField(max_length=24, choices=Status.choices)
    action = models.CharField(max_length=40)
    warnings = models.JSONField(default=list, blank=True)
    errors = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "provenance_content_import_item"
        ordering = ("id",)
        indexes = [models.Index(fields=("batch", "status"))]

    def clean(self):
        super().clean()
        if not isinstance(self.warnings, list) or not isinstance(self.errors, list):
            raise ValidationError("Warnings and errors must be arrays.")

    def __str__(self) -> str:
        return f"{self.external_id}: {self.action}"
