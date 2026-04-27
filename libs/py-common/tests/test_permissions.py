"""Tests for ilb_common.permissions — RBAC classes and HeaderAuthentication."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from ilb_common.auth_headers import AuthHeaders
from ilb_common.permissions import (
    HeaderAuthentication,
    IsClientOwner,
    IsDirector,
    IsStaff,
    RequestUser,
)
from rest_framework.exceptions import AuthenticationFailed

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_user(
    role: str = "Staff",
    company_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> RequestUser:
    uid = user_id or uuid.uuid4()
    return RequestUser(AuthHeaders(user_id=uid, role=role, company_id=company_id))  # type: ignore[arg-type]


def _make_request(user: RequestUser) -> MagicMock:
    """Return a mock DRF request with ``.user`` set."""
    request = MagicMock()
    request.user = user
    return request


class FakeModel:
    """Minimal model with ``company_id`` for IsClientOwner tests."""

    def __init__(self, company_id: uuid.UUID | None = None) -> None:
        self.company_id = company_id


# ---------------------------------------------------------------------------
# RequestUser
# ---------------------------------------------------------------------------


class TestRequestUser:
    def test_is_authenticated_always_true(self) -> None:
        user = _make_user(role="Client")
        assert user.is_authenticated is True

    def test_str_representation(self) -> None:
        uid = uuid.UUID("11111111-1111-1111-1111-111111111111")
        user = _make_user(role="Director", user_id=uid)
        assert str(user) == f"Director:{uid}"

    def test_repr(self) -> None:
        uid = uuid.UUID("22222222-2222-2222-2222-222222222222")
        user = _make_user(role="Staff", user_id=uid)
        r = repr(user)
        assert "RequestUser" in r
        assert "Staff" in r

    def test_equality_same_id(self) -> None:
        uid = uuid.uuid4()
        u1 = _make_user(role="Staff", user_id=uid)
        u2 = _make_user(role="Director", user_id=uid)
        assert u1 == u2

    def test_equality_different_id(self) -> None:
        u1 = _make_user(role="Staff")
        u2 = _make_user(role="Staff")
        assert u1 != u2

    def test_equality_not_request_user(self) -> None:
        user = _make_user()
        assert user != "not-a-user"

    def test_hash_based_on_id(self) -> None:
        uid = uuid.uuid4()
        u1 = _make_user(role="Staff", user_id=uid)
        u2 = _make_user(role="Director", user_id=uid)
        assert hash(u1) == hash(u2)

    def test_properties(self) -> None:
        uid = uuid.uuid4()
        cid = uuid.uuid4()
        user = _make_user(role="Client", company_id=cid, user_id=uid)
        assert user.id == uid
        assert user.role == "Client"
        assert user.company_id == cid

    def test_staff_has_no_company_id(self) -> None:
        user = _make_user(role="Staff")
        assert user.company_id is None


# ---------------------------------------------------------------------------
# HeaderAuthentication
# ---------------------------------------------------------------------------


class TestHeaderAuthentication:
    def test_authenticate_valid_headers(self) -> None:
        uid = uuid.uuid4()
        cid = uuid.uuid4()
        meta = {
            "HTTP_X_USER_ID": str(uid),
            "HTTP_X_USER_ROLE": "Staff",
            "HTTP_X_COMPANY_ID": str(cid),
        }
        request = MagicMock()
        request.META = meta

        auth = HeaderAuthentication()
        user, auth_detail = auth.authenticate(request)

        assert isinstance(user, RequestUser)
        assert user.id == uid
        assert user.role == "Staff"
        assert user.company_id == cid
        assert auth_detail is None

    def test_authenticate_director_no_company(self) -> None:
        uid = uuid.uuid4()
        meta = {
            "HTTP_X_USER_ID": str(uid),
            "HTTP_X_USER_ROLE": "Director",
        }
        request = MagicMock()
        request.META = meta

        auth = HeaderAuthentication()
        user, _ = auth.authenticate(request)

        assert user.role == "Director"
        assert user.company_id is None

    def test_authenticate_missing_user_id_raises(self) -> None:
        request = MagicMock()
        request.META = {"HTTP_X_USER_ROLE": "Staff"}

        auth = HeaderAuthentication()
        with pytest.raises(AuthenticationFailed, match="missing X-User-Id"):
            auth.authenticate(request)

    def test_authenticate_invalid_role_raises(self) -> None:
        request = MagicMock()
        request.META = {
            "HTTP_X_USER_ID": str(uuid.uuid4()),
            "HTTP_X_USER_ROLE": "Admin",
        }

        auth = HeaderAuthentication()
        with pytest.raises(AuthenticationFailed, match="invalid X-User-Role"):
            auth.authenticate(request)

    def test_authenticate_invalid_uuid_raises(self) -> None:
        request = MagicMock()
        request.META = {
            "HTTP_X_USER_ID": "not-a-uuid",
            "HTTP_X_USER_ROLE": "Staff",
        }

        auth = HeaderAuthentication()
        with pytest.raises(AuthenticationFailed, match="invalid X-User-Id"):
            auth.authenticate(request)


# ---------------------------------------------------------------------------
# IsDirector
# ---------------------------------------------------------------------------


class TestIsDirector:
    def test_allows_director(self) -> None:
        user = _make_user(role="Director")
        request = _make_request(user)
        perm = IsDirector()
        assert perm.has_permission(request, None) is True

    def test_denies_staff(self) -> None:
        user = _make_user(role="Staff")
        request = _make_request(user)
        perm = IsDirector()
        assert perm.has_permission(request, None) is False

    def test_denies_client(self) -> None:
        user = _make_user(role="Client", company_id=uuid.uuid4())
        request = _make_request(user)
        perm = IsDirector()
        assert perm.has_permission(request, None) is False

    def test_denies_anonymous(self) -> None:
        """Anonymous users (no ``role`` attribute) must be denied."""
        request = MagicMock()
        request.user = MagicMock()
        del request.user.role
        perm = IsDirector()
        assert perm.has_permission(request, None) is False


# ---------------------------------------------------------------------------
# IsStaff
# ---------------------------------------------------------------------------


class TestIsStaff:
    def test_allows_staff(self) -> None:
        user = _make_user(role="Staff")
        request = _make_request(user)
        perm = IsStaff()
        assert perm.has_permission(request, None) is True

    def test_allows_director(self) -> None:
        """Directors have at least Staff-level access."""
        user = _make_user(role="Director")
        request = _make_request(user)
        perm = IsStaff()
        assert perm.has_permission(request, None) is True

    def test_denies_client(self) -> None:
        user = _make_user(role="Client", company_id=uuid.uuid4())
        request = _make_request(user)
        perm = IsStaff()
        assert perm.has_permission(request, None) is False

    def test_denies_anonymous(self) -> None:
        request = MagicMock()
        request.user = MagicMock()
        del request.user.role
        perm = IsStaff()
        assert perm.has_permission(request, None) is False


# ---------------------------------------------------------------------------
# IsClientOwner
# ---------------------------------------------------------------------------


class TestIsClientOwner:
    def test_has_permission_allows_client(self) -> None:
        user = _make_user(role="Client", company_id=uuid.uuid4())
        request = _make_request(user)
        perm = IsClientOwner()
        assert perm.has_permission(request, None) is True

    def test_has_permission_denies_staff(self) -> None:
        user = _make_user(role="Staff")
        request = _make_request(user)
        perm = IsClientOwner()
        assert perm.has_permission(request, None) is False

    def test_has_permission_denies_director(self) -> None:
        user = _make_user(role="Director")
        request = _make_request(user)
        perm = IsClientOwner()
        assert perm.has_permission(request, None) is False

    def test_has_object_permission_matching_company(self) -> None:
        cid = uuid.uuid4()
        user = _make_user(role="Client", company_id=cid)
        request = _make_request(user)
        obj = FakeModel(company_id=cid)
        perm = IsClientOwner()
        assert perm.has_object_permission(request, None, obj) is True

    def test_has_object_permission_mismatched_company(self) -> None:
        user = _make_user(role="Client", company_id=uuid.uuid4())
        request = _make_request(user)
        obj = FakeModel(company_id=uuid.uuid4())
        perm = IsClientOwner()
        assert perm.has_object_permission(request, None, obj) is False

    def test_has_object_permission_denies_non_client(self) -> None:
        user = _make_user(role="Staff")
        request = _make_request(user)
        obj = FakeModel(company_id=uuid.uuid4())
        perm = IsClientOwner()
        assert perm.has_object_permission(request, None, obj) is False

    def test_has_object_permission_denies_object_without_company_id(self) -> None:
        cid = uuid.uuid4()
        user = _make_user(role="Client", company_id=cid)
        request = _make_request(user)
        obj = FakeModel(company_id=None)
        perm = IsClientOwner()
        assert perm.has_object_permission(request, None, obj) is False

    def test_has_object_permission_string_company_id_comparison(self) -> None:
        """Object ``company_id`` may be a string UUID; comparison must still work."""
        cid = uuid.uuid4()
        user = _make_user(role="Client", company_id=cid)
        request = _make_request(user)
        obj = FakeModel(company_id=str(cid))
        perm = IsClientOwner()
        assert perm.has_object_permission(request, None, obj) is True

    def test_has_permission_denies_anonymous(self) -> None:
        request = MagicMock()
        request.user = MagicMock()
        del request.user.role
        perm = IsClientOwner()
        assert perm.has_permission(request, None) is False
