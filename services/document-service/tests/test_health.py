"""Tests for public health endpoints."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import yaml
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


def test_api_documents_health_minio_ok(client: Client, monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_openapi_schema_yaml_returns_ok(client: Client) -> None:
    response = client.get("/api/documents/schema/")
    assert response.status_code == 200
    body = response.content.decode()
    doc = yaml.safe_load(body)
    assert doc["openapi"].startswith("3.")
    paths = doc["paths"]
    assert "/api/documents/schema/" in paths
    assert "/api/documents/schema/swagger/" in paths


def test_openapi_schema_json_format(client: Client) -> None:
    response = client.get("/api/documents/schema/?format=json")
    assert response.status_code == 200
    doc = json.loads(response.content.decode())
    assert "/api/documents/schema/swagger/" in doc["paths"]


def test_swagger_ui_returns_html(client: Client) -> None:
    response = client.get("/api/documents/schema/swagger/")
    assert response.status_code == 200
    assert "text/html" in response["Content-Type"]
    assert b"swagger" in response.content.lower()
