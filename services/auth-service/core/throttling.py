"""DRF throttles scoped to specific views."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.throttling import SimpleRateThrottle


class LoginIPRateThrottle(SimpleRateThrottle):
    """
    Limit login POSTs per client IP.

    Uses Django's default cache (Redis in deployment, LocMem when ``REDIS_URL`` is unset).
    """

    scope = "login_ip"

    def get_rate(self) -> str:
        """Resolve rate from Django settings (DRF api_settings can cache too early)."""
        if not getattr(self, "scope", None):
            return super().get_rate()
        rf = getattr(settings, "REST_FRAMEWORK", None) or {}
        rates: dict[str, str] = rf.get("DEFAULT_THROTTLE_RATES") or {}
        try:
            return rates[self.scope]
        except KeyError as exc:
            raise ImproperlyConfigured(
                f"No default throttle rate set for '{self.scope}' scope"
            ) from exc

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
