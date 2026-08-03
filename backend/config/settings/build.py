from .base import *  # noqa: F403

SECRET_KEY = "static-files-build-only"
ALLOWED_HOSTS = ["localhost"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
