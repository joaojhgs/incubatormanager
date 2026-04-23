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


def test_api_inventory_health_returns_ok(client: Client) -> None:
    response = client.get("/api/inventory/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
