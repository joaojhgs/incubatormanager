"""Public health endpoints for probes and gateway routing."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.serializers import (
    ILBTokenObtainPairSerializer,
    ILBTokenRefreshSerializer,
    LogoutRequestSerializer,
)
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


class IntrospectView(APIView):
    """Gateway `auth_request` stub — validates JWT in a later iteration."""

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        summary="Introspect (stub)",
        description=(
            "Internal gateway probe used with Nginx auth_request. Stub implementation "
            "returns trusted identity headers for development."
        ),
        tags=["gateway"],
        responses={
            200: OpenApiResponse(description="Token accepted (stub)."),
        },
    )
    def get(self, request: Request) -> Response:
        return Response(
            status=status.HTTP_200_OK,
            headers={
                "X-User-Id": "00000000-0000-4000-8000-000000000001",
                "X-User-Role": "Staff",
                "X-Company-Id": "",
            },
        )
