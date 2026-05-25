"""DRF throttles scoped to booking entrypoints."""

from __future__ import annotations

from django.conf import settings
from rest_framework.settings import api_settings
from rest_framework.throttling import SimpleRateThrottle


class PublicBookingIPRateThrottle(SimpleRateThrottle):
    """Limit anonymous public booking submissions per client IP."""

    scope = "public_booking_ip"

    def get_cache_key(self, request, view):  # type: ignore[override]
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}

    def get_rate(self) -> str:
        rates = getattr(settings, "REST_FRAMEWORK", {}).get("DEFAULT_THROTTLE_RATES") or {}
        if self.scope in rates:
            return rates[self.scope]
        return api_settings.DEFAULT_THROTTLE_RATES[self.scope]
