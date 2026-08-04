from django.contrib import admin

from .models import Chapter, Section, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "title")


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("subject", "number", "title")
    list_filter = ("subject",)
    search_fields = ("title",)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("chapter", "number", "title")
    list_filter = ("chapter__subject", "chapter")
    search_fields = ("title",)
