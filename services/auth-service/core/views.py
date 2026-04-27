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
from users.models import User

from core.gateway_auth import verify_access_token_for_gateway
from core.serializers import (
    ILBTokenObtainPairSerializer,
    ILBTokenRefreshSerializer,
    LogoutRequestSerializer,
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


class UserSerializer(serializers.Serializer):
    """Minimal user representation returned by :class:`UserListView`."""

    id = serializers.UUIDField()
    email = serializers.EmailField()
    role = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    company_id = serializers.UUIDField(allow_null=True)


class UserListView(APIView):
    """
    List users — Director only.

    Reads the ``X-User-Role`` header injected by the Nginx gateway after
    ``auth_request`` validation.  Returns 403 for Staff and Client roles.
    """

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        summary="List users (Director only)",
        description=(
            "Returns all users. Only accessible when the gateway-injected "
            "X-User-Role header is Director. Staff and Client receive 403."
        ),
        tags=["users"],
        responses={
            200: UserSerializer(many=True),
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
        role = request.META.get("HTTP_X_USER_ROLE", "")
        if role != "Director":
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        users = User.objects.all().order_by("email")
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
