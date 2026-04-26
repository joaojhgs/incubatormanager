"""Tests for GET /auth/verify/ and /auth/introspect/ (gateway auth_request)."""

from __future__ import annotations

import uuid

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from users.models import User


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_verify_returns_401_without_bearer_token(api_client: APIClient) -> None:
    unauth = api_client.get("/auth/verify/")
    assert unauth.status_code == 401


@pytest.mark.django_db
def test_verify_returns_401_for_invalid_token(api_client: APIClient) -> None:
    bad = api_client.get(
        "/auth/verify/", HTTP_AUTHORIZATION="Bearer not-a-real-jwt.eyJhbGciOiJnone.0"
    )
    assert bad.status_code == 401
    assert bad.json().get("code") == "token_not_valid"


@pytest.mark.django_db
def test_verify_sets_identity_headers_for_valid_access_token(api_client: APIClient) -> None:
    u = User.objects.create_user(
        "staff@example.com",
        "correct-horse-battery-staple",
        role=User.Role.STAFF,
        first_name="Sam",
        last_name="Staff",
    )
    login = api_client.post(
        "/api/auth/login/",
        {"email": "staff@example.com", "password": "correct-horse-battery-staple"},
        format="json",
    )
    assert login.status_code == 200
    access = login.json()["access"]
    v = api_client.get("/auth/verify/", HTTP_AUTHORIZATION=f"Bearer {access}")
    assert v.status_code == 200
    assert v["X-User-Id"] == str(u.id)
    assert v["X-User-Role"] == "Staff"
    assert v["X-Company-Id"] == ""


@pytest.mark.django_db
def test_verify_includes_client_company_in_header(api_client: APIClient) -> None:
    co = uuid.uuid4()
    User.objects.create_user(
        "client@example.com",
        "p455w0rd",
        role=User.Role.CLIENT,
        first_name="C",
        last_name="Client",
        company_id=co,
    )
    login = api_client.post(
        "/api/auth/login/",
        {"email": "client@example.com", "password": "p455w0rd"},
        format="json",
    )
    assert login.status_code == 200
    u = User.objects.get(email="client@example.com")
    access = login.json()["access"]
    v = api_client.get("/auth/verify/", HTTP_AUTHORIZATION=f"Bearer {access}")
    assert v.status_code == 200
    assert v["X-User-Id"] == str(u.id)
    assert v["X-User-Role"] == "Client"
    assert v["X-Company-Id"] == str(co)


@pytest.mark.django_db
def test_verify_rejects_inactive_user(api_client: APIClient) -> None:
    u = User.objects.create_user(
        "x@example.com",
        "secret",
        role=User.Role.STAFF,
        first_name="X",
        last_name="Y",
    )
    u.is_active = False
    u.save(update_fields=["is_active"])
    # Token valid cryptographically, but user inactive.
    access = str(AccessToken.for_user(u))
    v = api_client.get("/auth/verify/", HTTP_AUTHORIZATION=f"Bearer {access}")
    assert v.status_code == 401
    assert v.json()["code"] == "user_inactive"


@pytest.mark.django_db
def test_introspect_matches_verify_behaviour(api_client: APIClient) -> None:
    u = User.objects.create_user(
        "both@example.com",
        "secret12",
        role=User.Role.STAFF,
        first_name="A",
        last_name="B",
    )
    access = str(RefreshToken.for_user(u).access_token)
    a = api_client.get("/auth/verify/", HTTP_AUTHORIZATION=f"Bearer {access}")
    b = api_client.get("/auth/introspect/", HTTP_AUTHORIZATION=f"Bearer {access}")
    assert a.status_code == 200
    assert b.status_code == 200
    assert a["X-User-Id"] == b["X-User-Id"] == str(u.id)
    assert a["X-User-Role"] == b["X-User-Role"] == "Staff"
    assert a["X-Company-Id"] == b["X-Company-Id"] == ""
