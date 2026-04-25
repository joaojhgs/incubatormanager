"""Custom JWT serializers (refresh rotation + Redis-backed blocklist)."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from core.token_blacklist import blocklist_refresh_jti, is_refresh_jti_blocklisted


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
