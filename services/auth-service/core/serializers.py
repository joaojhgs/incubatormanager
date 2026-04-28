"""Custom JWT serializers (refresh rotation + Redis-backed blocklist)."""

from __future__ import annotations

import uuid
from typing import Any

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from core.token_blacklist import blocklist_refresh_jti, is_refresh_jti_blocklisted


def _app_role(user: Any) -> str:
    raw = getattr(user, "role", "") or ""
    if not isinstance(raw, str):
        return str(raw).lower()
    mapping = {"Director": "director", "Staff": "staff", "Client": "client"}
    return mapping.get(raw, raw.lower())


class ILBTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds incubator routing claims expected by the Next.js middleware."""

    @classmethod
    def get_token(cls, user: Any) -> Any:
        token = super().get_token(user)
        token["role"] = _app_role(user)
        company_id = getattr(user, "company_id", None)
        if company_id is not None:
            token["company_id"] = str(company_id)
        return token


class ILBTokenRefreshSerializer(TokenRefreshSerializer):
    """
    :class:`TokenRefreshSerializer` with:

    * A cache / Redis JTI check before each refresh
    * After successful rotation, the *previous* refresh JTI is blocklisted
    """

    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        try:
            refresh: RefreshToken = self.token_class(attrs["refresh"])
        except TokenError:
            raise
        jti_claim = api_settings.JTI_CLAIM
        if (
            jti_claim
            and jti_claim in refresh
            and is_refresh_jti_blocklisted(str(refresh[jti_claim]))
        ):
            raise TokenError(_("Token is blocklisted"))

        # Re-check the user is still present and active (token may pre-date deactivation).
        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
        if user_id is not None:
            User = get_user_model()
            try:
                user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
            except User.DoesNotExist:
                raise exceptions.AuthenticationFailed(
                    self.error_messages["no_active_account"],
                    "no_active_account",
                ) from None
            if not api_settings.USER_AUTHENTICATION_RULE(user):
                raise exceptions.AuthenticationFailed(
                    self.error_messages["no_active_account"],
                    "no_active_account",
                )

        data: dict[str, str] = {"access": str(refresh.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if jti_claim and jti_claim in refresh and "exp" in refresh:
                old_jti = str(refresh[jti_claim])
                old_exp = int(refresh["exp"])
            else:
                old_jti, old_exp = ("", 0)
            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()
            if old_jti and old_exp:
                blocklist_refresh_jti(old_jti, old_exp)
            data["refresh"] = str(refresh)

        return data


class LogoutRequestSerializer(serializers.Serializer):
    """Body for :meth:`core.views.LogoutView.post` — the refresh to revoke."""

    refresh = serializers.CharField(write_only=True, required=True, allow_blank=False)


class UserReadSerializer(serializers.Serializer):
    """User row returned by Director-scoped user APIs."""

    id = serializers.UUIDField()
    email = serializers.EmailField()
    role = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    company_id = serializers.UUIDField(allow_null=True)
    is_active = serializers.BooleanField()


class UserCreateSerializer(serializers.Serializer):
    """Payload for creating a user (Director only)."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    role = serializers.ChoiceField(required=True, choices=["Director", "Staff", "Client"])
    company_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        role = attrs["role"]
        company_id = attrs.get("company_id")
        if role == "Client" and company_id is None:
            raise serializers.ValidationError({"company_id": "Client users require a company_id."})
        if role != "Client" and company_id is not None:
            raise serializers.ValidationError(
                {"company_id": "company_id must be null unless role is Client."}
            )
        return attrs


class UserUpdateSerializer(serializers.Serializer):
    """Partial update of a user (Director only)."""

    first_name = serializers.CharField(required=False, max_length=150)
    last_name = serializers.CharField(required=False, max_length=150)
    role = serializers.ChoiceField(required=False, choices=["Director", "Staff", "Client"])
    company_id = serializers.UUIDField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        User = get_user_model()
        instance = self.context.get("user_instance")
        if not isinstance(instance, User):
            return attrs
        new_role = attrs.get("role", instance.role)
        if "company_id" in attrs:
            new_company: uuid.UUID | None = attrs["company_id"]
        else:
            new_company = instance.company_id
        if new_role == "Client" and new_company is None:
            raise serializers.ValidationError({"company_id": "Client users require a company_id."})
        if new_role != "Client":
            attrs["company_id"] = None
        return attrs
