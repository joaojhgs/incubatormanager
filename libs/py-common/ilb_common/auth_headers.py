"""Parse trusted gateway headers injected after JWT introspection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, cast
from uuid import UUID

Role = Literal["Director", "Staff", "Client"]
_VALID_ROLES: frozenset[str] = frozenset({"Director", "Staff", "Client"})


@dataclass(frozen=True, slots=True)
class AuthHeaders:
    """Trusted identity forwarded by Nginx from ``auth_request``."""

    user_id: UUID
    role: Role
    company_id: UUID | None


def _first(meta: Mapping[str, str | None], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        raw = meta.get(key)
        if raw is not None and str(raw).strip() != "":
            return str(raw).strip()
    return None


def parse(meta: Mapping[str, str | None]) -> AuthHeaders:
    """
    Parse user identity from WSGI/ASGI-style header maps.

    Accepts Django ``request.META`` keys (``HTTP_*``) and plain header names.
    """
    user_s = _first(meta, ("HTTP_X_USER_ID", "X-User-Id"))
    role_s = _first(meta, ("HTTP_X_USER_ROLE", "X-User-Role"))
    company_s = _first(meta, ("HTTP_X_COMPANY_ID", "X-Company-Id"))

    if not user_s:
        msg = "missing X-User-Id"
        raise ValueError(msg)
    if not role_s:
        msg = "missing X-User-Role"
        raise ValueError(msg)
    if role_s not in _VALID_ROLES:
        msg = f"invalid X-User-Role: {role_s!r}"
        raise ValueError(msg)

    try:
        user_id = UUID(user_s)
    except ValueError as exc:
        msg = "invalid X-User-Id UUID"
        raise ValueError(msg) from exc

    company_id: UUID | None
    if company_s is None:
        company_id = None
    else:
        try:
            company_id = UUID(company_s)
        except ValueError as exc:
            msg = "invalid X-Company-Id UUID"
            raise ValueError(msg) from exc

    return AuthHeaders(user_id=user_id, role=cast(Role, role_s), company_id=company_id)
