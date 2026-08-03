from collections.abc import Mapping

from django.http import JsonResponse
from rest_framework.exceptions import ErrorDetail
from rest_framework.views import exception_handler


def _serialize_details(details: object) -> object:
    if isinstance(details, ErrorDetail):
        return str(details)
    if isinstance(details, Mapping):
        return {key: _serialize_details(value) for key, value in details.items()}
    if isinstance(details, (list, tuple)):
        return [_serialize_details(value) for value in details]
    return details


def api_exception_handler(exc: Exception, context: dict) -> object:
    response = exception_handler(exc, context)
    if response is None:
        return None

    details = _serialize_details(response.data)
    code = getattr(exc, "default_code", "request_error")
    message = "请求无法处理。"
    field_errors: object = {}

    if isinstance(details, dict) and "detail" in details:
        message = str(details["detail"])
    elif isinstance(details, dict):
        message = "请检查提交的字段。"
        field_errors = details
    elif isinstance(details, list) and details:
        message = str(details[0])

    response.data = {
        "error": {
            "code": str(code),
            "message": message,
            "field_errors": field_errors,
        }
    }
    return response


def csrf_failure(request, reason: str = "") -> JsonResponse:
    return JsonResponse(
        {
            "error": {
                "code": "csrf_failed",
                "message": "CSRF 验证失败，请刷新页面后重试。",
                "field_errors": {},
            }
        },
        status=403,
    )
