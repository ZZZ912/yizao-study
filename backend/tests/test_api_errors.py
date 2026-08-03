from rest_framework.exceptions import PermissionDenied

from config.api import api_exception_handler


def test_permission_denied_has_stable_error_code():
    response = api_exception_handler(PermissionDenied(), {})
    assert response.status_code == 403
    assert response.data["error"]["code"] == "permission_denied"
    assert response.data["error"]["field_errors"] == {}
