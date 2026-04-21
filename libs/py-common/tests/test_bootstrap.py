"""Tests for bootstrap.shared_settings."""

from __future__ import annotations

import pytest
from ilb_common.bootstrap import shared_settings


def test_shared_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "TZ",
        "DATABASE_URL",
        "RABBITMQ_URL",
        "REDIS_URL",
        "MINIO_ENDPOINT",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
        "JWT_ISSUER",
        "JWT_AUDIENCE",
    ):
        monkeypatch.delenv(key, raising=False)

    s = shared_settings()
    assert s["TIME_ZONE"] == "Europe/Lisbon"
    assert s["DATABASE_URL"] == ""
    assert s["MINIO_BUCKET"] == "ilb-documents"
    assert s["MINIO_USE_SSL"] is False
    assert s["JWT_ACCESS_TTL_SECONDS"] == 900
    assert s["JWT_REFRESH_TTL_SECONDS"] == 604800


def test_shared_settings_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TZ", "UTC")
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@db:5432/app")
    monkeypatch.setenv("MINIO_USE_SSL", "true")

    s = shared_settings()
    assert s["TIME_ZONE"] == "UTC"
    assert s["DATABASE_URL"] == "postgres://u:p@db:5432/app"
    assert s["MINIO_USE_SSL"] is True
