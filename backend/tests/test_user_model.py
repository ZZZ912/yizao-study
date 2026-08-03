import pytest

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
