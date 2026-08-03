import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="student@example.com",
        password="StrongPass123!",
        display_name="测试学员",
    )


@pytest.fixture
def csrf_client():
    return APIClient(enforce_csrf_checks=True)


@pytest.mark.django_db
def test_session_login_me_and_logout(csrf_client, user):
    csrf_response = csrf_client.get(reverse("auth-csrf"))
    assert csrf_response.status_code == 200
    csrf_token = csrf_response.json()["data"]["csrf_token"]

    login_response = csrf_client.post(
        reverse("auth-login"),
        {"email": "STUDENT@example.com", "password": "StrongPass123!"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert login_response.status_code == 200
    assert login_response.json()["data"]["email"] == "student@example.com"

    me_response = csrf_client.get(reverse("auth-me"))
    assert me_response.status_code == 200
    assert me_response.json()["data"]["display_name"] == "测试学员"

    csrf_token = csrf_client.cookies["csrftoken"].value
    logout_response = csrf_client.post(
        reverse("auth-logout"),
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert logout_response.status_code == 204
    anonymous_response = csrf_client.get(reverse("auth-me"))
    assert anonymous_response.status_code == 403
    assert anonymous_response.json()["error"]["code"] == "not_authenticated"


@pytest.mark.django_db
def test_login_requires_csrf(csrf_client, user):
    response = csrf_client.post(
        reverse("auth-login"),
        {"email": user.email, "password": "StrongPass123!"},
        format="json",
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_failed"


@pytest.mark.django_db
def test_invalid_credentials_use_uniform_error(csrf_client, user):
    csrf_token = csrf_client.get(reverse("auth-csrf")).json()["data"]["csrf_token"]
    response = csrf_client.post(
        reverse("auth-login"),
        {"email": user.email, "password": "wrong-password"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 400
    assert response.json()["error"] == {
        "code": "invalid_credentials",
        "message": "邮箱或密码不正确。",
        "field_errors": {},
    }


@pytest.mark.django_db
def test_fifth_failed_login_is_rate_limited_for_fifteen_minutes(csrf_client, user):
    csrf_token = csrf_client.get(reverse("auth-csrf")).json()["data"]["csrf_token"]
    for _ in range(4):
        response = csrf_client.post(
            reverse("auth-login"),
            {"email": user.email, "password": "wrong-password"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "invalid_credentials"

    response = csrf_client.post(
        reverse("auth-login"),
        {"email": user.email.upper(), "password": "wrong-password"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "login_rate_limited"
    assert 1 <= int(response["Retry-After"]) <= 15 * 60 + 1


@pytest.mark.django_db
def test_successful_login_clears_failure_counter(csrf_client, user):
    csrf_token = csrf_client.get(reverse("auth-csrf")).json()["data"]["csrf_token"]
    for _ in range(4):
        csrf_client.post(
            reverse("auth-login"),
            {"email": user.email, "password": "wrong-password"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    response = csrf_client.post(
        reverse("auth-login"),
        {"email": user.email.upper(), "password": "StrongPass123!"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 200

    rotated_token = csrf_client.cookies["csrftoken"].value
    assert (
        csrf_client.post(reverse("auth-logout"), HTTP_X_CSRFTOKEN=rotated_token).status_code == 204
    )
    fresh_token = csrf_client.get(reverse("auth-csrf")).json()["data"]["csrf_token"]
    response = csrf_client.post(
        reverse("auth-login"),
        {"email": user.email, "password": "wrong-password"},
        format="json",
        HTTP_X_CSRFTOKEN=fresh_token,
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_credentials"


@pytest.mark.django_db
def test_public_registration_route_does_not_exist():
    response = APIClient().post(
        "/api/v1/auth/register/",
        {"email": "new@example.com", "password": "StrongPass123!"},
        format="json",
    )
    assert response.status_code == 404
