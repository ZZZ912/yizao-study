from django.urls import path

from .views import (
    ChapterListView,
    DashboardView,
    NextQuestionView,
    SectionDetailView,
    SubjectListView,
    SubmitAttemptView,
    UpdateWrongReasonView,
    WrongQuestionListView,
)

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="learning-dashboard"),
    path("subjects/", SubjectListView.as_view(), name="learning-subjects"),
    path(
        "subjects/<slug:subject_code>/chapters/",
        ChapterListView.as_view(),
        name="learning-chapters",
    ),
    path("sections/<uuid:section_id>/", SectionDetailView.as_view(), name="learning-section"),
    path("questions/next/", NextQuestionView.as_view(), name="practice-next"),
    path("attempts/", SubmitAttemptView.as_view(), name="practice-submit"),
    path(
        "attempts/<uuid:attempt_id>/wrong-reason/",
        UpdateWrongReasonView.as_view(),
        name="practice-wrong-reason",
    ),
    path("wrong-questions/", WrongQuestionListView.as_view(), name="practice-wrong"),
]
