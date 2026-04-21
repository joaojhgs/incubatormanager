"""Tests for auth_headers.parse."""

from __future__ import annotations

import uuid

import pytest
from ilb_common.auth_headers import AuthHeaders, parse


def test_parse_django_meta() -> None:
    uid = uuid.uuid4()
    cid = uuid.uuid4()
    h = parse(
        {
            "HTTP_X_USER_ID": str(uid),
            "HTTP_X_USER_ROLE": "Staff",
            "HTTP_X_COMPANY_ID": str(cid),
        }
    )
    assert h == AuthHeaders(user_id=uid, role="Staff", company_id=cid)


def test_parse_plain_headers() -> None:
    uid = uuid.uuid4()
    h = parse({"X-User-Id": str(uid), "X-User-Role": "Director"})
    assert h.company_id is None
    assert h.role == "Director"


def test_parse_missing_user() -> None:
    with pytest.raises(ValueError, match="missing X-User-Id"):
        parse({"HTTP_X_USER_ROLE": "Client"})


def test_parse_invalid_role() -> None:
    with pytest.raises(ValueError, match="invalid X-User-Role"):
        parse(
            {
                "HTTP_X_USER_ID": str(uuid.uuid4()),
                "HTTP_X_USER_ROLE": "Admin",
            }
        )


def test_parse_bad_user_uuid() -> None:
    with pytest.raises(ValueError, match="invalid X-User-Id"):
        parse({"HTTP_X_USER_ID": "not-a-uuid", "HTTP_X_USER_ROLE": "Client"})


def test_parse_bad_company_uuid() -> None:
    with pytest.raises(ValueError, match="invalid X-Company-Id"):
        parse(
            {
                "HTTP_X_USER_ID": str(uuid.uuid4()),
                "HTTP_X_USER_ROLE": "Client",
                "HTTP_X_COMPANY_ID": "nope",
            }
        )
