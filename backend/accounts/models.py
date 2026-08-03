import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower

from .managers import UserManager


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField("邮箱", unique=True)
    display_name = models.CharField("显示名称", max_length=80, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        db_table = "accounts_user"
        verbose_name = "用户"
        verbose_name_plural = "用户"
        constraints = [
            models.UniqueConstraint(Lower("email"), name="accounts_user_email_ci_unique"),
        ]

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email).lower()

    def save(self, *args, **kwargs):
        self.email = self.__class__.objects.normalize_email(self.email).lower()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.display_name or self.email


class LoginThrottle(models.Model):
    scope = models.CharField(max_length=20)
    ip_address = models.CharField(max_length=64)
    email = models.EmailField()
    failure_count = models.PositiveSmallIntegerField(default=0)
    window_started_at = models.DateTimeField()
    locked_until = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_login_throttle"
        constraints = [
            models.UniqueConstraint(
                fields=("scope", "ip_address", "email"),
                name="accounts_login_throttle_identity_unique",
            ),
        ]
        indexes = [models.Index(fields=("locked_until",))]
