from django.contrib import admin

from .models import KnowledgePoint


@admin.register(KnowledgePoint)
class KnowledgePointAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "section", "is_active")
    list_filter = ("section__chapter__subject", "section__chapter", "is_active")
    search_fields = ("code", "title", "description")
