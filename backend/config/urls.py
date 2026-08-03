from django.contrib import admin
from django.urls import include, path

from config.health import live, ready

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/live/", live, name="health-live"),
    path("api/health/ready/", ready, name="health-ready"),
    path("api/v1/auth/", include("accounts.urls")),
]
