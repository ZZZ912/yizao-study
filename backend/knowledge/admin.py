from django.contrib import admin

from .models import KnowledgePoint, KnowledgeVersion


@admin.register(KnowledgePoint)
class KnowledgePointAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "section", "is_active")
    list_filter = ("section__chapter__subject", "section__chapter", "is_active")
    search_fields = ("code", "title", "description")
    autocomplete_fields = ("section", "current_version")


@admin.register(KnowledgeVersion)
class KnowledgeVersionAdmin(admin.ModelAdmin):
    list_display = ("knowledge_point", "version_number", "review_status", "created_at")
    list_filter = ("review_status", "applicable_exam_edition", "knowledge_point__section")
    search_fields = ("knowledge_point__code", "knowledge_point__title", "summary")

    def get_readonly_fields(self, request, obj=None):
        if obj and (obj.immutable_after_publish or obj.review_status == obj.ReviewStatus.PUBLISHED):
            return tuple(field.name for field in obj._meta.fields)
        return ("content_checksum", "created_at", "immutable_after_publish")
