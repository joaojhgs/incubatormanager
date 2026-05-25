"""Tests for POST /api/auth/refresh/ and POST /api/auth/logout/."""

from __future__ import annotations

import uuid

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture(autouse=True)
def _reset_cache() -> object:
    cache.clear()
    yield
    cache.clear()


def _user_with_login(api_client: APIClient) -> tuple[User, dict[str, str]]:
    User.objects.create_user(
        "r@example.com",
        "secret-refresh-pw",
        role=User.Role.STAFF,
        first_name="R",
        last_name="User",
    )
    login = api_client.post(
        "/api/auth/login/",
        {"email": "r@example.com", "password": "secret-refresh-pw"},
        format="json",
    )
    assert login.status_code == 200, login.json()
    body: dict[str, str] = login.json()
    return (User.objects.get(email="r@example.com"), body)


def test_refresh_returns_new_tokens(api_client: APIClient) -> None:
    _user, tokens = _user_with_login(api_client)
    r = api_client.post(
        "/api/auth/refresh/",
        {"refresh": tokens["refresh"]},
        format="json",
    )
    assert r.status_code == 200, r.json()
    data = r.json()
    assert "access" in data and "refresh" in data
    assert data["access"] != tokens["access"]
    assert data["refresh"] != tokens["refresh"]


def test_refresh_uses_cookie_and_rotates_cookie(api_client: APIClient) -> None:
    _user, tokens = _user_with_login(api_client)

    r = api_client.post("/api/auth/refresh/", {}, format="json")

    assert r.status_code == 200, r.json()
    data = r.json()
    assert data["refresh"] != tokens["refresh"]
    cookie = r.cookies.get("ilb.refresh_token")
    assert cookie is not None
    assert cookie.value == data["refresh"]


def test_logout_uses_cookie_and_clears_cookie(api_client: APIClient) -> None:
    _user, tokens = _user_with_login(api_client)

    out = api_client.post("/api/auth/logout/", {}, format="json")

    assert out.status_code == 204
    cookie = out.cookies.get("ilb.refresh_token")
    assert cookie is not None
    assert cookie.value == ""
    bad = api_client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert bad.status_code == 401


def test_refresh_deleted_user_clears_cookie(api_client: APIClient) -> None:
    user, _tokens = _user_with_login(api_client)
    user.delete()

    r = api_client.post("/api/auth/refresh/", {}, format="json")

    assert r.status_code == 401
    cookie = r.cookies.get("ilb.refresh_token")
    assert cookie is not None
    assert cookie.value == ""


def test_logout_validation_error_clears_cookie(api_client: APIClient) -> None:
    _user, _tokens = _user_with_login(api_client)

    r = api_client.post("/api/auth/logout/", {"refresh": ""}, format="json")

    assert r.status_code == 400
    cookie = r.cookies.get("ilb.refresh_token")
    assert cookie is not None
    assert cookie.value == ""


def test_logout_get_clears_cookie_and_redirects(api_client: APIClient) -> None:
    _user, _tokens = _user_with_login(api_client)

    r = api_client.get("/api/auth/logout/?next=/login")

    assert r.status_code == 302
    assert r["Location"] == "/login"
    cookie = r.cookies.get("ilb.refresh_token")
    assert cookie is not None
    assert cookie.value == ""


def test_refresh_reuses_old_token_returns_401(api_client: APIClient) -> None:
    _user, tokens = _user_with_login(api_client)
    refresh_once = api_client.post(
        "/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json"
    )
    assert refresh_once.status_code == 200, refresh_once.json()
    r2 = api_client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert r2.status_code == 401
    r3 = api_client.post(
        "/api/auth/refresh/",
        {"refresh": refresh_once.json()["refresh"]},
        format="json",
    )
    assert r3.status_code == 200, r3.json()


def test_logout_blocks_further_refresh(api_client: APIClient) -> None:
    _user, tokens = _user_with_login(api_client)
    out = api_client.post("/api/auth/logout/", {"refresh": tokens["refresh"]}, format="json")
    assert out.status_code == 204
    bad = api_client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert bad.status_code == 401


def test_logout_missing_refresh_returns_400(api_client: APIClient) -> None:
    r = api_client.post("/api/auth/logout/", {}, format="json")
    assert r.status_code == 400


def test_logout_malformed_refresh_returns_401(api_client: APIClient) -> None:
    r = api_client.post(
        "/api/auth/logout/",
        {"refresh": "not-a-valid-jwt"},
        format="json",
    )
    assert r.status_code == 401


def test_logout_succeeds_for_client_with_company_id(api_client: APIClient) -> None:
    User.objects.create_user(
        "c@example.com",
        "pw-pw",
        role=User.Role.CLIENT,
        first_name="C",
        last_name="C",
        company_id=uuid.uuid4(),
    )
    login = api_client.post(
        "/api/auth/login/",
        {"email": "c@example.com", "password": "pw-pw"},
        format="json",
    )
    assert login.status_code == 200, login.json()
    tokens: dict[str, str] = login.json()
    out = api_client.post("/api/auth/logout/", {"refresh": tokens["refresh"]}, format="json")
    assert out.status_code == 204
    bad = api_client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert bad.status_code == 401
