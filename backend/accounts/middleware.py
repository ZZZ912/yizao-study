from django.conf import settings
from django.http import HttpResponse

from .exceptions import LoginRateLimited
from .security import (
    clear_login_failures,
    enforce_login_rate_limit,
    get_client_ip,
    normalize_email,
    record_login_failure,
)


class AdminSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_admin_login = request.path == "/admin/login/" and request.method == "POST"
        email = normalize_email(request.POST.get("username", "")) if is_admin_login else ""
        ip_address = get_client_ip(request)

        if is_admin_login and email:
            try:
                enforce_login_rate_limit(scope="admin", ip_address=ip_address, email=email)
            except LoginRateLimited as exc:
                return self._rate_limited_response(exc.retry_after)

        response = self.get_response(request)

        if is_admin_login and email:
            if request.user.is_authenticated and request.user.is_staff:
                clear_login_failures(scope="admin", ip_address=ip_address, email=email)
            else:
                try:
                    record_login_failure(scope="admin", ip_address=ip_address, email=email)
                except LoginRateLimited as exc:
                    return self._rate_limited_response(exc.retry_after)

        if request.path.startswith("/admin/") and request.user.is_authenticated:
            if request.user.is_staff:
                request.session.set_expiry(settings.ADMIN_SESSION_COOKIE_AGE)

        return response

    @staticmethod
    def _rate_limited_response(retry_after: int) -> HttpResponse:
        response = HttpResponse("登录尝试过多，请稍后再试。", status=429)
        response["Retry-After"] = str(retry_after)
        return response
