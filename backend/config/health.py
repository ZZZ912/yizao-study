from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def live(request):
    return JsonResponse({"data": {"status": "ok"}})


@require_GET
def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse(
            {
                "error": {
                    "code": "database_unavailable",
                    "message": "服务尚未就绪。",
                    "field_errors": {},
                }
            },
            status=503,
        )
    return JsonResponse({"data": {"status": "ready"}})
