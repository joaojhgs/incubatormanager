"""Director-scoped /api/auth/users CRUD: RBAC matrix and core flows."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from django.test import override_settings
from rest_framework.test import APIClient
from users.models import User

USERS_URL = "/api/auth/users/"


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def director() -> User:
    return User.objects.create_user(
        "director-crud@test.local",
        "secret12345",
        role=User.Role.DIRECTOR,
        first_name="Dir",
        last_name="Ector",
    )


@pytest.fixture
def staff_user() -> User:
    return User.objects.create_user(
        "staff-crud@test.local",
        "secret12345",
        role=User.Role.STAFF,
        first_name="Sta",
        last_name="FF",
    )


@pytest.fixture
def client_user() -> User:
    return User.objects.create_user(
        "client-crud@test.local",
        "secret12345",
        role=User.Role.CLIENT,
        first_name="Cli",
        last_name="Ent",
        company_id=uuid.uuid4(),
    )


def _headers(role: str | None, user_id: uuid.UUID | None) -> dict[str, str]:
    h: dict[str, str] = {}
    if role is not None:
        h["HTTP_X_USER_ROLE"] = role
    if user_id is not None:
        h["HTTP_X_USER_ID"] = str(user_id)
    return h


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("method", "path_fn", "role", "expect"),
    [
        ("get", lambda _u: USERS_URL, "Director", 200),
        ("post", lambda _u: USERS_URL, "Director", 400),
        ("get", lambda _u: USERS_URL, "Staff", 403),
        ("post", lambda _u: USERS_URL, "Staff", 403),
        ("get", lambda _u: USERS_URL, "Client", 403),
        ("get", lambda _u: USERS_URL, None, 403),
        ("get", lambda u: f"{USERS_URL}{u.id}/", "Director", 200),
        ("patch", lambda u: f"{USERS_URL}{u.id}/", "Director", 200),
        ("delete", lambda u: f"{USERS_URL}{u.id}/", "Director", 204),
        ("get", lambda u: f"{USERS_URL}{u.id}/", "Staff", 403),
        ("patch", lambda u: f"{USERS_URL}{u.id}/", "Staff", 403),
        ("delete", lambda u: f"{USERS_URL}{u.id}/", "Client", 403),
        ("get", lambda u: f"{USERS_URL}{u.id}/", None, 403),
    ],
)
def test_users_rbac_matrix(
    api_client: APIClient,
    director: User,
    staff_user: User,
    client_user: User,
    method: str,
    path_fn: Any,
    role: str | None,
    expect: int,
) -> None:
    """Each user-management endpoint rejects non-Director gateway roles."""
    target = staff_user
    path = path_fn(target)
    if role == "Director":
        uid: uuid.UUID | None = director.id
    elif role == "Staff":
        uid = staff_user.id
    elif role == "Client":
        uid = client_user.id
    else:
        uid = None
    kw = _headers(role, uid)
    client_method = getattr(api_client, method.lower())
    if method == "get" or method == "delete":
        resp = client_method(path, **kw)
    elif method == "post":
        if expect == 400:
            resp = client_method(path, data={"email": "x"}, format="json", **kw)
        else:
            resp = client_method(path, data={}, format="json", **kw)
    else:
        resp = client_method(path, data={}, format="json", **kw)
    assert resp.status_code == expect


@pytest.mark.django_db
def test_create_staff_and_retrieve(api_client: APIClient, director: User) -> None:
    payload = {
        "email": "newstaff@test.local",
        "password": "longenough1",
        "first_name": "New",
        "last_name": "Staff",
        "role": "Staff",
    }
    create = api_client.post(
        USERS_URL,
        data=payload,
        format="json",
        **_headers("Director", director.id),
    )
    assert create.status_code == 201
    body = create.json()
    assert body["email"] == payload["email"]
    assert body["role"] == "Staff"
    assert body["company_id"] is None
    rid = body["id"]

    got = api_client.get(
        f"{USERS_URL}{rid}/",
        **_headers("Director", director.id),
    )
    assert got.status_code == 200
    assert got.json()["email"] == payload["email"]


@pytest.mark.django_db
def test_create_client_requires_company(api_client: APIClient, director: User) -> None:
    resp = api_client.post(
        USERS_URL,
        data={
            "email": "nocorp@test.local",
            "password": "longenough1",
            "first_name": "C",
            "last_name": "Lient",
            "role": "Client",
        },
        format="json",
        **_headers("Director", director.id),
    )
    assert resp.status_code == 400
    assert "company_id" in resp.json()


@pytest.mark.django_db
def test_create_duplicate_email(api_client: APIClient, director: User, staff_user: User) -> None:
    resp = api_client.post(
        USERS_URL,
        data={
            "email": staff_user.email,
            "password": "longenough1",
            "first_name": "X",
            "last_name": "Y",
            "role": "Staff",
        },
        format="json",
        **_headers("Director", director.id),
    )
    assert resp.status_code == 400
    assert "email" in resp.json()


@pytest.mark.django_db
def test_patch_password_only_director(
    api_client: APIClient,
    director: User,
    staff_user: User,
) -> None:
    patch = api_client.patch(
        f"{USERS_URL}{staff_user.id}/",
        data={"password": "new-strong-pw-99"},
        format="json",
        **_headers("Director", director.id),
    )
    assert patch.status_code == 200
    staff_user.refresh_from_db()
    assert staff_user.check_password("new-strong-pw-99")


@pytest.mark.django_db
def test_patch_and_soft_delete(api_client: APIClient, director: User, staff_user: User) -> None:
    patch = api_client.patch(
        f"{USERS_URL}{staff_user.id}/",
        data={"first_name": "Renamed"},
        format="json",
        **_headers("Director", director.id),
    )
    assert patch.status_code == 200
    assert patch.json()["first_name"] == "Renamed"

    deleted = api_client.delete(
        f"{USERS_URL}{staff_user.id}/",
        **_headers("Director", director.id),
    )
    assert deleted.status_code == 204
    staff_user.refresh_from_db()
    assert staff_user.is_active is False

    still = api_client.get(
        f"{USERS_URL}{staff_user.id}/",
        **_headers("Director", director.id),
    )
    assert still.status_code == 200
    assert still.json()["is_active"] is False


@pytest.mark.django_db
def test_detail_not_found(api_client: APIClient, director: User) -> None:
    missing = uuid.uuid4()
    resp = api_client.get(
        f"{USERS_URL}{missing}/",
        **_headers("Director", director.id),
    )
    assert resp.status_code == 404


@pytest.mark.django_db
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
def test_user_list_query_budget(
    api_client: APIClient,
    director: User,
    django_assert_num_queries: Any,
) -> None:
    for i in range(5):
        User.objects.create_user(
            f"q{i}@test.local",
            "pw",
            role=User.Role.STAFF,
            first_name="F",
            last_name=str(i),
        )
    with django_assert_num_queries(1):
        resp = api_client.get(
            USERS_URL,
            **_headers("Director", director.id),
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 5
