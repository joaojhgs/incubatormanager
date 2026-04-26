"""DRF throttles scoped to specific views."""

from __future__ import annotations

from rest_framework.throttling import SimpleRateThrottle


class LoginIPRateThrottle(SimpleRateThrottle):
    """
    Limit login POSTs per client IP.

    Uses Django's default cache (Redis in deployment, LocMem when ``REDIS_URL`` is unset).
    """

    scope = "login_ip"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
