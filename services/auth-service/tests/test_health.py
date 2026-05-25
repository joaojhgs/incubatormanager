"""Tests for public health endpoints."""

from __future__ import annotations

import pytest
from django.test import Client


@pytest.fixture
def client() -> Client:
    return Client()


def test_root_health_returns_ok(client: Client) -> None:
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_auth_health_returns_ok(client: Client) -> None:
    response = client.get("/api/auth/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_metrics_returns_stub(client: Client) -> None:
    response = client.get("/metrics/")
    assert response.status_code == 200
    assert response.json() == {"service": "auth-service", "status": "ok", "metrics": {}}


def test_api_auth_metrics_returns_stub(client: Client) -> None:
    response = client.get("/api/auth/metrics/")
    assert response.status_code == 200
    assert response.json() == {"service": "auth-service", "status": "ok", "metrics": {}}
