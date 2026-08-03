import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse

from accounts.models import User


@pytest.mark.django_db
def test_create_user_normalizes_email_and_uses_uuid():
    user = User.objects.create_user(
        email="Student@EXAMPLE.COM",
        password="StrongPass123!",
    )
    assert user.email == "student@example.com"
    assert user.username is None
    assert user.check_password("StrongPass123!")


@pytest.mark.django_db
def test_create_user_requires_email():
    with pytest.raises(ValueError, match="Email is required"):
        User.objects.create_user(email="", password="StrongPass123!")


@pytest.mark.django_db
def test_direct_model_save_normalizes_email():
    user = User(email="Direct.Save@Example.COM")
    user.set_password("StrongPass123!")
    user.save()
    assert user.email == "direct.save@example.com"


@pytest.mark.django_db
def test_database_rejects_case_insensitive_duplicate_email():
    User.objects.create_user(email="Test@Example.com", password="StrongPass123!")
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.bulk_create([User(email="test@example.com", password="unusable")])


@pytest.mark.django_db
def test_admin_created_mixed_case_email_can_login(client):
    administrator = User.objects.create_superuser(
        email="owner@example.com",
        password="StrongAdminPass123!",
    )
    client.force_login(administrator)
    response = client.post(
        reverse("admin:accounts_user_add"),
        {
            "email": "Admin.Created@Example.COM",
            "display_name": "后台创建用户",
            "password1": "AnotherStrongPass123!",
            "password2": "AnotherStrongPass123!",
        },
    )
    assert response.status_code == 302
    created_user = User.objects.get(email="admin.created@example.com")
    assert created_user.display_name == "后台创建用户"

    client.logout()
    assert client.login(
        email="ADMIN.CREATED@EXAMPLE.COM",
        password="AnotherStrongPass123!",
    )


@pytest.mark.django_db
def test_admin_login_rate_limit_and_short_session(client):
    administrator = User.objects.create_superuser(
        email="admin@example.com",
        password="StrongAdminPass123!",
    )
    login_url = reverse("admin:login")
    for _ in range(4):
        response = client.post(
            login_url,
            {"username": administrator.email.upper(), "password": "wrong-password"},
        )
        assert response.status_code == 200

    response = client.post(
        login_url,
        {"username": administrator.email, "password": "wrong-password"},
    )
    assert response.status_code == 429
    assert "Retry-After" in response

    client = client.__class__()
    client.force_login(administrator)
    assert client.get(reverse("admin:index")).status_code == 200
    assert client.session.get_expiry_age() <= 30 * 60
