from django.contrib import admin
from django.db.models import TextField
from django.db.models.functions import Cast

from provenance.models import ContentProvenance, SourceMaterial

from .models import Question, QuestionOption, QuestionVersion


class WarningFilter(admin.SimpleListFilter):
    title = "警告"
    parameter_name = "has_warnings"

    def lookups(self, request, model_admin):
        return (("yes", "有警告"), ("no", "无警告"))

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(warnings=[])
        if self.value() == "no":
            return queryset.filter(warnings=[])
        return queryset


class WarningCodeFilter(admin.SimpleListFilter):
    warning_code = ""

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.annotate(warnings_text=Cast("warnings", TextField())).filter(
                warnings_text__icontains=self.warning_code
            )
        return queryset


class AnswerConflictFilter(WarningCodeFilter):
    title = "答案冲突"
    parameter_name = "answer_conflict"
    warning_code = "answer_conflict"

    def lookups(self, request, model_admin):
        return (("yes", "有答案冲突"),)


class DuplicateCandidateFilter(WarningCodeFilter):
    title = "重复候选"
    parameter_name = "duplicate_candidate"
    warning_code = "duplicate_candidate"

    def lookups(self, request, model_admin):
        return (("yes", "有重复候选"),)


class SourceFileFilter(admin.SimpleListFilter):
    title = "来源文件"
    parameter_name = "source_file"

    def lookups(self, request, model_admin):
        return SourceMaterial.objects.order_by("file_name").values_list("id", "file_name")

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        version_ids = ContentProvenance.objects.filter(
            content_type="question_version",
            source_material_id=self.value(),
        ).values("content_object_id")
        return queryset.filter(id__in=version_ids)


@admin.action(description="标记为有争议")
def mark_questions_disputed(modeladmin, request, queryset):
    queryset.exclude(status=Question.Status.PUBLISHED).update(status=Question.Status.DISPUTED)


@admin.action(description="退回待审核")
def return_questions_pending(modeladmin, request, queryset):
    queryset.exclude(status=Question.Status.PUBLISHED).update(status=Question.Status.PENDING_REVIEW)


@admin.action(description="标记为已复核")
def mark_versions_reviewed(modeladmin, request, queryset):
    queryset.exclude(review_status=QuestionVersion.ReviewStatus.PUBLISHED).exclude(
        immutable_after_publish=True
    ).update(review_status=QuestionVersion.ReviewStatus.REVIEWED)


@admin.action(description="标记为有争议")
def mark_versions_disputed(modeladmin, request, queryset):
    queryset.exclude(review_status=QuestionVersion.ReviewStatus.PUBLISHED).exclude(
        immutable_after_publish=True
    ).update(review_status=QuestionVersion.ReviewStatus.DISPUTED)


@admin.action(description="退回待审核")
def return_versions_pending(modeladmin, request, queryset):
    queryset.exclude(review_status=QuestionVersion.ReviewStatus.PUBLISHED).exclude(
        immutable_after_publish=True
    ).update(review_status=QuestionVersion.ReviewStatus.PENDING_REVIEW)


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0

    def has_add_permission(self, request, obj=None):
        if obj and (obj.immutable_after_publish or obj.review_status == obj.ReviewStatus.PUBLISHED):
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and (obj.immutable_after_publish or obj.review_status == obj.ReviewStatus.PUBLISHED):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and (obj.immutable_after_publish or obj.review_status == obj.ReviewStatus.PUBLISHED):
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("external_id", "section", "question_type", "status", "updated_at")
    list_filter = ("subject", "chapter", "section", "question_type", "status")
    search_fields = ("external_id", "current_version__stem")
    actions = (mark_questions_disputed, return_questions_pending)
    autocomplete_fields = ("subject", "chapter", "section", "current_version")


@admin.register(QuestionVersion)
class QuestionVersionAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "version_number",
        "review_status",
        "source_type",
        "created_at",
    )
    list_filter = (
        "question__section__chapter",
        "question__section",
        "question__question_type",
        "review_status",
        "source_type",
        WarningFilter,
        AnswerConflictFilter,
        DuplicateCandidateFilter,
        SourceFileFilter,
    )
    search_fields = ("question__external_id", "stem", "content_checksum")
    actions = (mark_versions_reviewed, mark_versions_disputed, return_versions_pending)
    inlines = (QuestionOptionInline,)

    def get_readonly_fields(self, request, obj=None):
        if obj and (obj.immutable_after_publish or obj.review_status == obj.ReviewStatus.PUBLISHED):
            return tuple(field.name for field in obj._meta.fields)
        return ("content_checksum", "created_at", "immutable_after_publish")


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ("question_version", "label", "sort_order")
    search_fields = ("question_version__question__external_id", "text")
