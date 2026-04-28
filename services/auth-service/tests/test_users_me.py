"""Tests for GET/PATCH /api/users/me/ — self-profile endpoints."""

from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

USERS_ME_URL = "/api/users/me/"


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def _authenticate(client: APIClient, user: User) -> None:
    """Set JWT Authorization header for *user* on *client*."""
    token = AccessToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token)}")


def _make_staff(**overrides: object) -> User:
    defaults = dict(
        email="staff@example.com",
        role=User.Role.STAFF,
        first_name="Sam",
        last_name="Staff",
    )
    defaults.update(overrides)
    return User.objects.create_user(
        defaults.pop("email"),
        "secret-pw",
        **defaults,
    )


def _make_client_user(**overrides: object) -> User:
    defaults = dict(
        email="client@example.com",
        role=User.Role.CLIENT,
        first_name="Casey",
        last_name="Client",
        company_id=uuid.uuid4(),
    )
    defaults.update(overrides)
    return User.objects.create_user(
        defaults.pop("email"),
        "secret-pw",
        **defaults,
    )


# ── GET /api/users/me/ ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_get_me_returns_authenticated_user_profile(api_client: APIClient) -> None:
    user = _make_staff()
    _authenticate(api_client, user)

    response = api_client.get(USERS_ME_URL)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user.pk)
    assert body["email"] == "staff@example.com"
    assert body["first_name"] == "Sam"
    assert body["last_name"] == "Staff"
    assert body["role"] == "Staff"
    assert body["company_id"] is None
    assert body["is_active"] is True
    assert "created_at" in body
    assert "updated_at" in body


@pytest.mark.django_db
def test_get_me_returns_company_id_for_client(api_client: APIClient) -> None:
    company_id = uuid.uuid4()
    user = _make_client_user(company_id=company_id)
    _authenticate(api_client, user)

    response = api_client.get(USERS_ME_URL)
    assert response.status_code == 200
    assert response.json()["company_id"] == str(company_id)


@pytest.mark.django_db
def test_get_me_unauthenticated_returns_401(api_client: APIClient) -> None:
    response = api_client.get(USERS_ME_URL)
    assert response.status_code == 401


@pytest.mark.django_db
def test_get_me_inactive_user_returns_401(api_client: APIClient) -> None:
    user = _make_staff()
    user.is_active = False
    user.save(update_fields=["is_active"])
    _authenticate(api_client, user)

    response = api_client.get(USERS_ME_URL)
    assert response.status_code == 401


# ── PATCH /api/users/me/ ────────────────────────────────────────────────


@pytest.mark.django_db
def test_patch_me_updates_first_and_last_name(api_client: APIClient) -> None:
    user = _make_staff()
    _authenticate(api_client, user)

    response = api_client.patch(
        USERS_ME_URL,
        {"first_name": "Samantha", "last_name": "Stafford"},
        format="json",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Samantha"
    assert body["last_name"] == "Stafford"

    user.refresh_from_db()
    assert user.first_name == "Samantha"
    assert user.last_name == "Stafford"


@pytest.mark.django_db
def test_patch_me_updates_first_name_only(api_client: APIClient) -> None:
    user = _make_staff()
    _authenticate(api_client, user)

    response = api_client.patch(
        USERS_ME_URL,
        {"first_name": "Samantha"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "Samantha"
    assert response.json()["last_name"] == "Staff"  # unchanged


@pytest.mark.django_db
def test_patch_me_changes_password_with_old_password(api_client: APIClient) -> None:
    user = _make_staff()
    _authenticate(api_client, user)

    response = api_client.patch(
        USERS_ME_URL,
        {"old_password": "secret-pw", "new_password": "new-strong-pw-123"},
        format="json",
    )
    assert response.status_code == 200

    user.refresh_from_db()
    assert user.check_password("new-strong-pw-123")
    assert not user.check_password("secret-pw")


@pytest.mark.django_db
def test_patch_me_password_change_rejects_wrong_old_password(
    api_client: APIClient,
) -> None:
    user = _make_staff()
    _authenticate(api_client, user)

    response = api_client.patch(
        USERS_ME_URL,
        {"old_password": "wrong-old-pw", "new_password": "new-strong-pw-123"},
        format="json",
    )
    assert response.status_code == 400
    assert "old_password" in response.json()


@pytest.mark.django_db
def test_patch_me_password_change_requires_old_password(api_client: APIClient) -> None:
    user = _make_staff()
    _authenticate(api_client, user)

    response = api_client.patch(
        USERS_ME_URL,
        {"new_password": "new-strong-pw-123"},
        format="json",
    )
    assert response.status_code == 400
    assert "old_password" in response.json()


@pytest.mark.django_db
def test_patch_me_password_change_rejects_old_password_without_new(
    api_client: APIClient,
) -> None:
    user = _make_staff()
    _authenticate(api_client, user)

    response = api_client.patch(
        USERS_ME_URL,
        {"old_password": "secret-pw"},
        format="json",
    )
    assert response.status_code == 400
    assert "new_password" in response.json()


@pytest.mark.django_db
def test_patch_me_password_change_validates_new_password(api_client: APIClient) -> None:
    """Django password validators reject short/common passwords."""
    user = _make_staff()
    _authenticate(api_client, user)

    response = api_client.patch(
        USERS_ME_URL,
        {"old_password": "secret-pw", "new_password": "123"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_patch_me_role_is_immutable(api_client: APIClient) -> None:
    user = _make_staff()
    _authenticate(api_client, user)

    response = api_client.patch(
        USERS_ME_URL,
        {"role": "Director"},
        format="json",
    )
    assert response.status_code == 200
    # role should remain unchanged
    assert response.json()["role"] == "Staff"
    user.refresh_from_db()
    assert user.role == User.Role.STAFF


@pytest.mark.django_db
def test_patch_me_company_id_is_immutable(api_client: APIClient) -> None:
    original_company = uuid.uuid4()
    user = _make_client_user(company_id=original_company)
    _authenticate(api_client, user)

    response = api_client.patch(
        USERS_ME_URL,
        {"company_id": str(uuid.uuid4())},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["company_id"] == str(original_company)
    user.refresh_from_db()
    assert user.company_id == original_company


@pytest.mark.django_db
def test_patch_me_email_is_immutable(api_client: APIClient) -> None:
    user = _make_staff()
    _authenticate(api_client, user)

    response = api_client.patch(
        USERS_ME_URL,
        {"email": "hacker@evil.com"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["email"] == "staff@example.com"
    user.refresh_from_db()
    assert user.email == "staff@example.com"


@pytest.mark.django_db
def test_patch_me_is_active_is_immutable(api_client: APIClient) -> None:
    user = _make_staff()
    _authenticate(api_client, user)

    response = api_client.patch(
        USERS_ME_URL,
        {"is_active": False},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True
    user.refresh_from_db()
    assert user.is_active is True


@pytest.mark.django_db
def test_put_me_returns_405(api_client: APIClient) -> None:
    """PUT is not allowed — only GET and PATCH."""
    user = _make_staff()
    _authenticate(api_client, user)

    response = api_client.put(
        USERS_ME_URL,
        {"first_name": "X"},
        format="json",
    )
    assert response.status_code == 405


@pytest.mark.django_db
def test_patch_me_unauthenticated_returns_401(api_client: APIClient) -> None:
    response = api_client.patch(USERS_ME_URL, {"first_name": "X"}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_patch_me_director_can_update_own_name(api_client: APIClient) -> None:
    user = User.objects.create_user(
        "director@example.com",
        "dir-pw",
        role=User.Role.DIRECTOR,
        first_name="Dir",
        last_name="Director",
    )
    _authenticate(api_client, user)

    response = api_client.patch(
        USERS_ME_URL,
        {"first_name": "Dirk"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "Dirk"


@pytest.mark.django_db
def test_patch_me_update_name_and_password_together(api_client: APIClient) -> None:
    user = _make_staff()
    _authenticate(api_client, user)

    response = api_client.patch(
        USERS_ME_URL,
        {
            "first_name": "Samantha",
            "old_password": "secret-pw",
            "new_password": "brand-new-pw-456",
        },
        format="json",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Samantha"

    user.refresh_from_db()
    assert user.first_name == "Samantha"
    assert user.check_password("brand-new-pw-456")
