"""Public health endpoints for probes and gateway routing."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


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

    serializer_class = TokenObtainPairSerializer

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
