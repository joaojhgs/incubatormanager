"""Tests for GET /api/auth/users/ — Director-only user list (gateway header pass-through)."""

from __future__ import annotations

import uuid

import pytest
from rest_framework.test import APIClient
from users.models import User


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def director() -> User:
    return User.objects.create_user(
        "director@test.local",
        "secret123",
        role=User.Role.DIRECTOR,
        first_name="Dir",
        last_name="Ector",
    )


@pytest.fixture
def staff_user() -> User:
    return User.objects.create_user(
        "staff@test.local",
        "secret123",
        role=User.Role.STAFF,
        first_name="Sta",
        last_name="FF",
    )


@pytest.fixture
def client_user() -> User:
    return User.objects.create_user(
        "client@test.local",
        "secret123",
        role=User.Role.CLIENT,
        first_name="Cli",
        last_name="Ent",
        company_id=uuid.uuid4(),
    )


@pytest.mark.django_db
def test_user_list_allows_director_role_header(
    api_client: APIClient, director: User, staff_user: User
) -> None:
    """When X-User-Role is Director, the endpoint returns 200 with user data."""
    resp = api_client.get(
        "/api/auth/users/",
        HTTP_X_USER_ROLE="Director",
        HTTP_X_USER_ID=str(director.id),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # director + staff_user


@pytest.mark.django_db
def test_user_list_rejects_staff_role_header(api_client: APIClient) -> None:
    """When X-User-Role is Staff, the endpoint returns 403."""
    resp = api_client.get(
        "/api/auth/users/",
        HTTP_X_USER_ROLE="Staff",
        HTTP_X_USER_ID=str(uuid.uuid4()),
    )
    assert resp.status_code == 403
    assert "permission" in resp.json()["detail"].lower()


@pytest.mark.django_db
def test_user_list_rejects_client_role_header(api_client: APIClient, client_user: User) -> None:
    """When X-User-Role is Client, the endpoint returns 403."""
    resp = api_client.get(
        "/api/auth/users/",
        HTTP_X_USER_ROLE="Client",
        HTTP_X_USER_ID=str(client_user.id),
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_user_list_rejects_missing_role_header(api_client: APIClient) -> None:
    """When X-User-Role header is absent, the endpoint returns 403."""
    resp = api_client.get("/api/auth/users/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_user_list_response_schema(api_client: APIClient, director: User) -> None:
    """Verify the response contains expected user fields."""
    resp = api_client.get(
        "/api/auth/users/",
        HTTP_X_USER_ROLE="Director",
        HTTP_X_USER_ID=str(director.id),
    )
    assert resp.status_code == 200
    users = resp.json()
    user = next(u for u in users if u["email"] == "director@test.local")
    assert "id" in user
    assert "email" in user
    assert "role" in user
    assert "first_name" in user
    assert "last_name" in user
    assert "company_id" in user
    assert user["role"] == "Director"
