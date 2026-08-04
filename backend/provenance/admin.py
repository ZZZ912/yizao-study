from django.contrib import admin

from .models import ContentImportBatch, ContentImportItem, ContentProvenance, SourceMaterial


class ConfidenceFilter(admin.SimpleListFilter):
    title = "提取置信度"
    parameter_name = "confidence"

    def lookups(self, request, model_admin):
        return (("low", "低于 0.8"), ("medium", "0.8–0.949"), ("high", "0.95 及以上"))

    def queryset(self, request, queryset):
        if self.value() == "low":
            return queryset.filter(extraction_confidence__lt=0.8)
        if self.value() == "medium":
            return queryset.filter(extraction_confidence__gte=0.8, extraction_confidence__lt=0.95)
        if self.value() == "high":
            return queryset.filter(extraction_confidence__gte=0.95)
        return queryset


@admin.register(SourceMaterial)
class SourceMaterialAdmin(admin.ModelAdmin):
    list_display = ("file_name", "source_type", "rights_scope", "public_repo_allowed", "year")
    list_filter = ("source_type", "rights_scope", "public_repo_allowed", "year")
    search_fields = ("external_id", "file_name", "institution", "title", "sha256")


@admin.register(ContentImportBatch)
class ContentImportBatchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "source_name",
        "status",
        "created_count",
        "updated_count",
        "skipped_count",
        "error_count",
        "started_at",
    )
    list_filter = ("status", "started_at")
    search_fields = ("id", "source_name", "source_checksum")
    readonly_fields = ("report",)


@admin.register(ContentImportItem)
class ContentImportItemAdmin(admin.ModelAdmin):
    list_display = ("external_id", "batch", "status", "action")
    list_filter = ("status", "action", "batch")
    search_fields = ("external_id",)


@admin.register(ContentProvenance)
class ContentProvenanceAdmin(admin.ModelAdmin):
    list_display = (
        "content_type",
        "content_object_id",
        "source_material",
        "source_page",
        "extraction_confidence",
    )
    list_filter = ("content_type", "source_material__file_name", "content_origin", ConfidenceFilter)
    search_fields = ("content_object_id", "source_question_number", "notes")
