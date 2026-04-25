"""Redis- or in-memory-cached JTI blocklist for revoked refresh tokens."""

from __future__ import annotations

import time

from django.core.cache import cache

JTI_KEY_PREFIX = "auth:jti:"


def is_refresh_jti_blocklisted(jti: str) -> bool:
    return bool(cache.get(JTI_KEY_PREFIX + jti))


def blocklist_refresh_jti(jti: str, exp_epoch: int) -> None:
    """
    Mark a refresh token as revoked until the token would have expired.

    `exp_epoch` is the ``exp`` claim of that refresh (Unix seconds), used
    to bound Redis / cache TTL and avoid unbounded key growth.

    Production must use Redis (see ``CACHES`` in settings): LocMemCache evicts
    entries under memory pressure, which could allow a revoked JTI to appear
    valid again before ``exp`` (tests use LocMem intentionally).
    """
    now = int(time.time())
    ttl = max(1, exp_epoch - now)
    cache.set(JTI_KEY_PREFIX + jti, 1, timeout=ttl)
