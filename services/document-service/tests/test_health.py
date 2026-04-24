"""Tests for public health endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.test import Client


@pytest.fixture
def client() -> Client:
    return Client()


def test_root_health_returns_ok(client: Client) -> None:
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_documents_health_returns_ok(client: Client) -> None:
    response = client.get("/api/documents/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_documents_health_503_when_minio_unreachable(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MINIO_ENDPOINT", "minio:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "access")
    monkeypatch.setenv("MINIO_SECRET_KEY", "secret")
    monkeypatch.setenv("MINIO_USE_SSL", "false")

    fake_client = MagicMock()
    fake_client.list_buckets.side_effect = OSError("connection refused")

    with patch("core.views.Minio", return_value=fake_client):
        response = client.get("/api/documents/health/")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "minio": "unreachable"}


def test_api_documents_health_minio_ok(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MINIO_ENDPOINT", "minio:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "access")
    monkeypatch.setenv("MINIO_SECRET_KEY", "secret")
    monkeypatch.setenv("MINIO_USE_SSL", "false")

    fake_client = MagicMock()

    with patch("core.views.Minio", return_value=fake_client):
        response = client.get("/api/documents/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "minio": "ok"}
    fake_client.list_buckets.assert_called_once()
