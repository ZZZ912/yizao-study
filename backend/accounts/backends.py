from django.contrib.auth.backends import ModelBackend

from .models import User


class CaseInsensitiveEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username or kwargs.pop(User.USERNAME_FIELD, None)
        if email:
            email = User.objects.normalize_email(email.strip()).lower()
        return super().authenticate(
            request,
            username=email,
            password=password,
            **kwargs,
        )
