"""Public health endpoints for probes and gateway routing."""

from __future__ import annotations

import os
import uuid

from django.http import HttpResponseRedirect
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import exceptions, serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core import services as user_services
from core.gateway_auth import verify_access_token_for_gateway
from core.permissions import IsGatewayDirector
from core.serializers import (
    ILBTokenObtainPairSerializer,
    ILBTokenRefreshSerializer,
    LogoutRequestSerializer,
    UserCreateSerializer,
    UserReadSerializer,
    UserUpdateSerializer,
)
from core.throttling import LoginIPRateThrottle
from core.token_blacklist import blocklist_refresh_jti

REFRESH_COOKIE_NAME = os.getenv("AUTH_REFRESH_COOKIE_NAME", "ilb.refresh_token")


def _refresh_cookie_kwargs(request: Request) -> dict[str, object]:
    return {
        "httponly": True,
        "samesite": "Lax",
        "path": "/",
        "secure": request.is_secure(),
        "max_age": int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
    }


def _set_refresh_cookie(response: Response, request: Request, refresh: str) -> None:
    response.set_cookie(REFRESH_COOKIE_NAME, refresh, **_refresh_cookie_kwargs(request))


def _delete_refresh_cookie(response: Response, request: Request) -> None:
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/", samesite="Lax")


def _refresh_from_body_or_cookie(request: Request) -> str | None:
    refresh: object = None
    if isinstance(request.data, dict) and "refresh" in request.data:
        refresh = request.data.get("refresh")
        return refresh if isinstance(refresh, str) else None
    cookie = request.COOKIES.get(REFRESH_COOKIE_NAME)
    return cookie if cookie else None


def _invalid_refresh_response(request: Request, *, status_code: int) -> Response:
    response = Response(
        {
            "detail": "Token is invalid or expired",
            "code": "token_not_valid",
        },
        status=status_code,
    )
    _delete_refresh_cookie(response, request)
    return response


def _safe_logout_redirect_target(request: Request) -> str:
    target = request.query_params.get("next") or "/login"
    if not target.startswith("/") or target.startswith("//"):
        return "/login"
    return target


class TokenPairResponseSerializer(serializers.Serializer):
    """JWT access and refresh strings returned on successful login."""

    access = serializers.CharField()
    refresh = serializers.CharField()


class RefreshCookieRequestSerializer(serializers.Serializer):
    """Optional refresh body; the httpOnly refresh cookie is used when omitted."""

    refresh = serializers.CharField(required=False, allow_blank=False)


class LoginRequestSerializer(serializers.Serializer):
    """Credentials accepted at login (matches ``TokenObtainPairSerializer`` fields)."""

    email = serializers.EmailField()
    password = serializers.CharField()


class LoginView(TokenObtainPairView):
    """Issue access (15m) and refresh (7d) JWTs after email/password verification."""

    serializer_class = ILBTokenObtainPairSerializer
    throttle_classes = [LoginIPRateThrottle]

    @extend_schema(
        summary="Login",
        description="Authenticate with email and password; returns a JWT access/refresh pair.",
        request=LoginRequestSerializer,
        responses={
            200: TokenPairResponseSerializer,
            401: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                            "example": "No active account found with the given credentials",
                        }
                    },
                },
                description=(
                    "Unknown email, wrong password, or inactive user "
                    "(same opaque message for all cases)."
                ),
            ),
            429: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                            "example": "Request was throttled. Expected available in 42 seconds.",
                        }
                    },
                },
                description="More than five login attempts per minute from this IP address.",
            ),
        },
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        response = super().post(request, *args, **kwargs)
        refresh = response.data.get("refresh") if isinstance(response.data, dict) else None
        if isinstance(refresh, str) and refresh:
            _set_refresh_cookie(response, request, refresh)
        return response


class RefreshView(TokenRefreshView):
    """
    New access/refresh pair; the previous refresh is blocklisted on rotation.
    """

    serializer_class = ILBTokenRefreshSerializer

    @extend_schema(
        summary="Refresh",
        description=(
            "Exchange a valid refresh for new tokens. The refresh may be sent in the "
            "JSON body or via the ilb.refresh_token httpOnly cookie; invalid refresh "
            "attempts clear that cookie."
        ),
        request=RefreshCookieRequestSerializer,
        responses={
            200: TokenPairResponseSerializer,
            400: OpenApiResponse(description="Missing refresh body/cookie."),
            401: OpenApiResponse(
                description="Invalid, expired, blocklisted, or inactive-user refresh."
            ),
        },
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        refresh = _refresh_from_body_or_cookie(request)
        serializer = self.get_serializer(data={"refresh": refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return _invalid_refresh_response(request, status_code=status.HTTP_401_UNAUTHORIZED)
        except exceptions.AuthenticationFailed:
            return _invalid_refresh_response(request, status_code=status.HTTP_401_UNAUTHORIZED)
        except serializers.ValidationError:
            return _invalid_refresh_response(request, status_code=status.HTTP_400_BAD_REQUEST)
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        rotated = serializer.validated_data.get("refresh")
        if isinstance(rotated, str) and rotated:
            _set_refresh_cookie(response, request, rotated)
        return response


class LogoutView(APIView):
    """
    Add the refresh JTI to the cache / Redis blocklist until it expires.
    """

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        summary="Clear refresh cookie",
        description=(
            "Same-site browser fallback that clears the ilb.refresh_token httpOnly "
            "cookie and redirects to the optional safe `next` path. It does not "
            "blocklist a refresh token; use POST for revocation."
        ),
        request=None,
        responses={302: OpenApiResponse(description="Refresh cookie cleared; redirect returned.")},
    )
    def get(self, request: Request) -> HttpResponseRedirect:
        response = HttpResponseRedirect(_safe_logout_redirect_target(request))
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/", samesite="Lax")
        return response

    @extend_schema(
        summary="Logout",
        description=(
            "Revoke the refresh from the JSON body or ilb.refresh_token cookie. "
            "The refresh cookie is cleared on success and invalid-token responses."
        ),
        request=RefreshCookieRequestSerializer,
        responses={
            204: OpenApiResponse(
                description="Blocklisted; further refresh attempts for this JTI fail."
            ),
            400: OpenApiResponse(
                description="Validation error, for example a missing refresh body/cookie."
            ),
            401: OpenApiResponse(
                description="Malformed, expired, or otherwise invalid refresh token."
            ),
        },
    )
    def post(self, request: Request) -> Response:
        refresh = _refresh_from_body_or_cookie(request)
        serializer = LogoutRequestSerializer(data={"refresh": refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            response = Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            _delete_refresh_cookie(response, request)
            return response
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
        except TokenError:
            # Return 401 explicitly: DRF maps AuthenticationFailed to 403 when no
            # ``WWW-Authenticate`` header exists (empty ``authentication_classes``).
            return _invalid_refresh_response(request, status_code=status.HTTP_401_UNAUTHORIZED)
        jti_claim = api_settings.JTI_CLAIM
        if not jti_claim or jti_claim not in token:
            return _invalid_refresh_response(request, status_code=status.HTTP_401_UNAUTHORIZED)
        blocklist_refresh_jti(str(token[jti_claim]), int(token["exp"]))
        response = Response(status=status.HTTP_204_NO_CONTENT)
        _delete_refresh_cookie(response, request)
        return response


class HealthView(APIView):
    """Liveness/readiness-style health payload."""

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {"status": {"type": "string", "example": "ok"}},
            }
        }
    )
    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class VerifyView(APIView):
    """
    Nginx internal ``auth_request`` target: validate the *same* request's
    ``Authorization: Bearer <access>`` and return identity headers.
    """

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        summary="Verify (gateway auth_request)",
        description=(
            "Validates a JWT access token and returns `X-User-Id`, `X-User-Role`, and "
            "`X-Company-Id` for the Nginx gateway to pass to upstream services. "
            "The gateway must forward the `Authorization` header to this subrequest."
        ),
        tags=["gateway"],
        responses={
            200: OpenApiResponse(
                response=None,
                description="Access token valid; identity in response headers.",
            ),
            401: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string"},
                        "code": {
                            "type": "string",
                            "enum": [
                                "token_not_valid",
                                "user_not_found",
                                "user_inactive",
                            ],
                        },
                    },
                },
            ),
        },
    )
    def get(self, request: Request) -> Response:
        return verify_access_token_for_gateway(request)


class IntrospectView(APIView):
    """
    Backwards-compatible alias; behaviour matches :class:`VerifyView`.
    Prefer ``GET /auth/verify/`` for the gateway.
    """

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(exclude=True)
    def get(self, request: Request) -> Response:
        return verify_access_token_for_gateway(request)


class UserListView(APIView):
    """
    List and create users — Director only.

    Trusts ``X-User-Role`` (and related headers) injected by the Nginx gateway
    after ``auth_request`` validation.
    """

    authentication_classes = ()
    permission_classes = [IsGatewayDirector]

    @extend_schema(
        summary="List users (Director only)",
        description=(
            "Returns all users. Only accessible when the gateway-injected "
            "X-User-Role header is Director. Staff and Client receive 403."
        ),
        tags=["users"],
        responses={
            200: UserReadSerializer(many=True),
            403: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                            "example": "You do not have permission to perform this action.",
                        }
                    },
                },
                description="Forbidden — role is not Director.",
            ),
        },
    )
    def get(self, request: Request) -> Response:
        users = user_services.list_users()
        return Response(UserReadSerializer(users, many=True).data)

    @extend_schema(
        summary="Create user (Director only)",
        description="Creates a new user account. Password is write-only and never returned.",
        tags=["users"],
        request=UserCreateSerializer,
        responses={
            201: UserReadSerializer,
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="Forbidden — role is not Director."),
        },
    )
    def post(self, request: Request) -> Response:
        ser = UserCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        try:
            user = user_services.create_user(
                email=d["email"],
                password=d["password"],
                first_name=d["first_name"],
                last_name=d["last_name"],
                role=d["role"],
                company_id=d.get("company_id"),
            )
        except user_services.DuplicateUserEmail:
            return Response(
                {"email": ["A user with this email already exists."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(UserReadSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    """Retrieve, update, or soft-delete a single user — Director only."""

    authentication_classes = ()
    permission_classes = [IsGatewayDirector]

    @extend_schema(
        summary="Retrieve user (Director only)",
        tags=["users"],
        responses={
            200: UserReadSerializer,
            403: OpenApiResponse(description="Forbidden — role is not Director."),
            404: OpenApiResponse(description="User id not found."),
        },
    )
    def get(self, request: Request, pk: str) -> Response:
        try:
            uid = uuid.UUID(str(pk))
        except ValueError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            user = user_services.get_user(uid)
        except user_services.UserNotFound:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(UserReadSerializer(user).data)

    @extend_schema(
        summary="Partially update user (Director only)",
        tags=["users"],
        request=UserUpdateSerializer,
        responses={
            200: UserReadSerializer,
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(description="Forbidden — role is not Director."),
            404: OpenApiResponse(description="User id not found."),
        },
    )
    def patch(self, request: Request, pk: str) -> Response:
        try:
            uid = uuid.UUID(str(pk))
        except ValueError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            user = user_services.get_user(uid)
        except user_services.UserNotFound:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        ser = UserUpdateSerializer(
            data=request.data,
            partial=True,
            context={"user_instance": user},
        )
        ser.is_valid(raise_exception=True)
        try:
            user_services.update_user(user, ser.validated_data)
        except user_services.DuplicateUserEmail:
            return Response(
                {"email": ["A user with this email already exists."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.refresh_from_db()
        return Response(UserReadSerializer(user).data)

    @extend_schema(
        summary="Soft-delete user (Director only)",
        description="Sets ``is_active`` to false; does not remove the row.",
        tags=["users"],
        responses={
            204: OpenApiResponse(description="User deactivated."),
            403: OpenApiResponse(description="Forbidden — role is not Director."),
            404: OpenApiResponse(description="User id not found."),
        },
    )
    def delete(self, request: Request, pk: str) -> Response:
        try:
            uid = uuid.UUID(str(pk))
        except ValueError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            user = user_services.get_user(uid)
        except user_services.UserNotFound:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        user_services.soft_delete_user(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MetricsView(APIView):
    """Minimal operational metrics endpoint for local demos and probes."""

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "example": "auth-service"},
                    "status": {"type": "string", "example": "ok"},
                    "metrics": {"type": "object"},
                },
            }
        }
    )
    def get(self, request: Request) -> Response:
        return Response({"service": "auth-service", "status": "ok", "metrics": {}})
