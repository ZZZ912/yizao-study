from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .exceptions import LoginRateLimited
from .models import LoginThrottle, User


def normalize_email(email: str) -> str:
    return User.objects.normalize_email(email.strip()).lower()


def get_client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.META.get("REMOTE_ADDR", "") or "unknown"


def _window() -> timedelta:
    return timedelta(seconds=settings.LOGIN_THROTTLE_WINDOW_SECONDS)


def _lock_duration() -> timedelta:
    return timedelta(seconds=settings.LOGIN_THROTTLE_LOCK_SECONDS)


def enforce_login_rate_limit(*, scope: str, ip_address: str, email: str) -> None:
    now = timezone.now()
    throttle = LoginThrottle.objects.filter(
        scope=scope,
        ip_address=ip_address,
        email=normalize_email(email),
    ).first()
    if throttle and throttle.locked_until and throttle.locked_until > now:
        retry_after = int((throttle.locked_until - now).total_seconds()) + 1
        raise LoginRateLimited(retry_after)


def record_login_failure(*, scope: str, ip_address: str, email: str) -> None:
    now = timezone.now()
    normalized_email = normalize_email(email)
    with transaction.atomic():
        throttle, _ = LoginThrottle.objects.select_for_update().get_or_create(
            scope=scope,
            ip_address=ip_address,
            email=normalized_email,
            defaults={"window_started_at": now},
        )
        if throttle.window_started_at < now - _window():
            throttle.failure_count = 0
            throttle.window_started_at = now
            throttle.locked_until = None

        throttle.failure_count += 1
        if throttle.failure_count >= settings.LOGIN_THROTTLE_FAILURE_LIMIT:
            throttle.locked_until = now + _lock_duration()

        throttle.save(
            update_fields=("failure_count", "window_started_at", "locked_until", "updated_at")
        )

    if throttle.locked_until and throttle.locked_until > now:
        retry_after = int((throttle.locked_until - now).total_seconds()) + 1
        raise LoginRateLimited(retry_after)


def clear_login_failures(*, scope: str, ip_address: str, email: str) -> None:
    LoginThrottle.objects.filter(
        scope=scope,
        ip_address=ip_address,
        email=normalize_email(email),
    ).delete()
