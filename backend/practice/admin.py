from django.contrib import admin

from .models import AnswerAttempt, WrongQuestion


@admin.register(AnswerAttempt)
class AnswerAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "question_version", "is_correct", "wrong_reason", "created_at")
    list_filter = ("is_correct", "wrong_reason", "created_at")
    search_fields = ("user__email", "question_version__question__external_id")
    readonly_fields = tuple(field.name for field in AnswerAttempt._meta.fields)


@admin.register(WrongQuestion)
class WrongQuestionAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "status", "wrong_count", "next_review_at")
    list_filter = ("status", "next_review_at")
    search_fields = ("user__email", "question__external_id")
