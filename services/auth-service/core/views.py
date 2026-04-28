"""Public health endpoints for probes and gateway routing."""

from __future__ import annotations

import uuid

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
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


class TokenPairResponseSerializer(serializers.Serializer):
    """JWT access and refresh strings returned on successful login."""

    access = serializers.CharField()
    refresh = serializers.CharField()


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
        return super().post(request, *args, **kwargs)


class RefreshView(TokenRefreshView):
    """
    New access/refresh pair; the previous refresh is blocklisted on rotation.
    """

    serializer_class = ILBTokenRefreshSerializer

    @extend_schema(
        summary="Refresh",
        description=(
            "Exchange a valid refresh for new tokens; the old refresh cannot be reused after."
        ),
        request={
            "application/json": {
                "type": "object",
                "required": ["refresh"],
                "properties": {"refresh": {"type": "string"}},
            }
        },
        responses={200: TokenPairResponseSerializer},
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    """
    Add the refresh JTI to the cache / Redis blocklist until it expires.
    """

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        summary="Logout",
        description=("Revoke the refresh; access may still be valid until its own expiry."),
        request=LogoutRequestSerializer,
        responses={
            204: OpenApiResponse(
                description="Blocklisted; further refresh attempts for this JTI fail."
            ),
            400: OpenApiResponse(
                description="Validation error, for example a missing `refresh` field."
            ),
            401: OpenApiResponse(
                description="Malformed, expired, or otherwise invalid refresh token."
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = LogoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
        except TokenError:
            # Return 401 explicitly: DRF maps AuthenticationFailed to 403 when no
            # ``WWW-Authenticate`` header exists (empty ``authentication_classes``).
            return Response(
                {
                    "detail": "Token is invalid or expired",
                    "code": "token_not_valid",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        jti_claim = api_settings.JTI_CLAIM
        if not jti_claim or jti_claim not in token:
            return Response(
                {
                    "detail": "Token has no id",
                    "code": "token_not_valid",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        blocklist_refresh_jti(str(token[jti_claim]), int(token["exp"]))
        return Response(status=status.HTTP_204_NO_CONTENT)


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
