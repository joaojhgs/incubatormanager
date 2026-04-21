"""Environment-driven settings fragments shared across Django services."""

from __future__ import annotations

import os
from typing import Any


def shared_settings() -> dict[str, Any]:
    """
    Return common configuration read from the process environment.

    Services merge this dict into their Django settings; empty strings mean
    the variable was not set.
    """
    return {
        "TIME_ZONE": os.environ.get("TZ", "Europe/Lisbon"),
        "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
        "RABBITMQ_URL": os.environ.get("RABBITMQ_URL", ""),
        "REDIS_URL": os.environ.get("REDIS_URL", ""),
        "MINIO_ENDPOINT": os.environ.get("MINIO_ENDPOINT", ""),
        "MINIO_ACCESS_KEY": os.environ.get("MINIO_ACCESS_KEY", ""),
        "MINIO_SECRET_KEY": os.environ.get("MINIO_SECRET_KEY", ""),
        "MINIO_BUCKET": os.environ.get("MINIO_BUCKET", "ilb-documents"),
        "MINIO_USE_SSL": os.environ.get("MINIO_USE_SSL", "false").lower() in {"1", "true", "yes"},
        "JWT_ISSUER": os.environ.get("JWT_ISSUER", ""),
        "JWT_AUDIENCE": os.environ.get("JWT_AUDIENCE", ""),
        "JWT_ACCESS_TTL_SECONDS": int(os.environ.get("JWT_ACCESS_TTL_SECONDS", "900")),
        "JWT_REFRESH_TTL_SECONDS": int(os.environ.get("JWT_REFRESH_TTL_SECONDS", "604800")),
    }
