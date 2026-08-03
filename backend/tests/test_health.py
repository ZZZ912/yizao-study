import pytest
from django.urls import reverse
from rest_framework.test import APIClient


def test_live_health_check():
    response = APIClient().get(reverse("health-live"))
    assert response.status_code == 200
    assert response.json() == {"data": {"status": "ok"}}


@pytest.mark.django_db
def test_ready_health_check():
    response = APIClient().get(reverse("health-ready"))
    assert response.status_code == 200
    assert response.json() == {"data": {"status": "ready"}}
