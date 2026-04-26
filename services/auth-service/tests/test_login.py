"""Tests for POST /api/auth/login/."""

from __future__ import annotations

import uuid

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from users.models import User


@pytest.fixture(autouse=True)
def _reset_throttle_count_before_isolated_login_tests(
    request: pytest.FixtureRequest,
) -> object:
    """``LoginIPRateThrottle`` is per client IP. Other modules (e.g. verify) also POST login."""
    if request.node.name in (
        "test_login_throttled_after_five_attempts_per_ip",
        "test_login_throttle_is_per_client_ip",
    ):
        yield
        return
    cache.clear()
    yield


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_login_returns_jwt_pair_for_valid_credentials(api_client: APIClient) -> None:
    User.objects.create_user(
        "staff@example.com",
        "correct-horse-battery-staple",
        role=User.Role.STAFF,
        first_name="Sam",
        last_name="Staff",
    )
    response = api_client.post(
        "/api/auth/login/",
        {"email": "staff@example.com", "password": "correct-horse-battery-staple"},
        format="json",
    )
    assert response.status_code == 200
    body = response.json()
    assert "access" in body and "refresh" in body
    assert isinstance(body["access"], str) and len(body["access"]) > 40
    assert isinstance(body["refresh"], str) and len(body["refresh"]) > 40
    assert RefreshToken(body["refresh"])["role"] == "staff"
    assert AccessToken(body["access"])["role"] == "staff"


@pytest.mark.django_db
def test_login_rejects_wrong_password(api_client: APIClient) -> None:
    User.objects.create_user(
        "u@example.com",
        "secret-one",
        role=User.Role.STAFF,
        first_name="U",
        last_name="User",
    )
    response = api_client.post(
        "/api/auth/login/",
        {"email": "u@example.com", "password": "secret-two"},
        format="json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_rejects_unknown_email(api_client: APIClient) -> None:
    response = api_client.post(
        "/api/auth/login/",
        {"email": "missing@example.com", "password": "any"},
        format="json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_rejects_inactive_user(api_client: APIClient) -> None:
    user = User.objects.create_user(
        "inactive@example.com",
        "still-secret",
        role=User.Role.STAFF,
        first_name="Ina",
        last_name="Ctive",
    )
    user.is_active = False
    user.save(update_fields=["is_active"])
    response = api_client.post(
        "/api/auth/login/",
        {"email": "inactive@example.com", "password": "still-secret"},
        format="json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_throttled_after_five_attempts_per_ip(api_client: APIClient) -> None:
    """Sixth POST to login from the same client IP within one minute returns 429."""
    cache.clear()
    for i in range(5):
        response = api_client.post(
            "/api/auth/login/",
            {"email": "missing@example.com", "password": "wrong"},
            format="json",
        )
        assert response.status_code == 401, i

    blocked = api_client.post(
        "/api/auth/login/",
        {"email": "missing@example.com", "password": "wrong"},
        format="json",
    )
    assert blocked.status_code == 429
    assert "throttl" in blocked.json()["detail"].lower()


@pytest.mark.django_db
def test_login_throttle_is_per_client_ip(api_client: APIClient) -> None:
    """Separate limits apply per ``X-Forwarded-For`` client (first address)."""
    cache.clear()
    for _ in range(5):
        api_client.post(
            "/api/auth/login/",
            {"email": "a@example.com", "password": "x"},
            format="json",
            HTTP_X_FORWARDED_FOR="198.51.100.10",
        )
    assert (
        api_client.post(
            "/api/auth/login/",
            {"email": "a@example.com", "password": "x"},
            format="json",
            HTTP_X_FORWARDED_FOR="198.51.100.10",
        ).status_code
        == 429
    )

    other = api_client.post(
        "/api/auth/login/",
        {"email": "b@example.com", "password": "y"},
        format="json",
        HTTP_X_FORWARDED_FOR="198.51.100.20",
    )
    assert other.status_code == 401


@pytest.mark.django_db
def test_passwords_are_stored_with_bcrypt_hasher() -> None:
    user = User.objects.create_user(
        "bcrypt-check@example.com",
        "p455w0rd",
        role=User.Role.CLIENT,
        first_name="Bo",
        last_name="Bcrypt",
        company_id=uuid.uuid4(),
    )
    assert user.password.startswith("bcrypt_sha256$")
