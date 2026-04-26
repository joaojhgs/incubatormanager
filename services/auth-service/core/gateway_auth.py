"""JWT verification for the Nginx gateway (``auth_request`` subrequest)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken

_HEADER_ROLES: dict[str, str] = {
    "director": "Director",
    "staff": "Staff",
    "client": "Client",
}


def _bearer_access_token(request: Request) -> str | None:
    h = (request.META.get("HTTP_AUTHORIZATION") or "").strip()
    if not h.lower().startswith("bearer "):
        return None
    raw = h[7:].strip()
    return raw or None


def verify_access_token_for_gateway(request: Request) -> Response:
    """
    Validate the ``Authorization: Bearer <access>`` on the *original* request,
    and return 200 with ``X-User-Id`` / ``X-User-Role`` / ``X-Company-Id`` for
    the gateway to copy to upstream, or 401.
    """
    raw = _bearer_access_token(request)
    if not raw:
        return Response(
            {"detail": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        token = AccessToken(raw)
    except TokenError:
        return Response(
            {
                "detail": "Given token not valid for any token type",
                "code": "token_not_valid",
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    user_id = token.get(api_settings.USER_ID_CLAIM)
    if user_id in (None, ""):
        return Response(
            {
                "detail": "Token contained no recognisable user identification",
                "code": "token_not_valid",
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    User = get_user_model()
    try:
        user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
    except User.DoesNotExist:
        return Response(
            {"detail": "User not found", "code": "user_not_found"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if not user.is_active:
        return Response(
            {"detail": "User is inactive", "code": "user_inactive"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    role_raw = str(token.get("role") or "staff").lower()
    x_role = _HEADER_ROLES.get(role_raw, "Staff")
    company = token.get("company_id")
    x_company = str(company) if company not in (None, "") else ""

    return Response(
        status=status.HTTP_200_OK,
        headers={
            "X-User-Id": str(user.pk),
            "X-User-Role": x_role,
            "X-Company-Id": x_company,
        },
    )
