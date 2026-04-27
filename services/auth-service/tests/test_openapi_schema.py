"""OpenAPI schema and Swagger UI routes."""

from __future__ import annotations

import json

import pytest
import yaml
from django.test import Client


@pytest.fixture
def client() -> Client:
    return Client()


def test_openapi_schema_yaml_returns_ok(client: Client) -> None:
    response = client.get("/api/auth/schema/")
    assert response.status_code == 200
    body = response.content.decode()
    doc = yaml.safe_load(body)
    assert doc["openapi"].startswith("3.")
    paths = doc["paths"]
    assert len(paths) == 8
    assert "/api/auth/schema/" in paths
    assert "/api/auth/schema/swagger/" in paths


def test_openapi_schema_json_format(client: Client) -> None:
    response = client.get("/api/auth/schema/?format=json")
    assert response.status_code == 200
    doc = json.loads(response.content.decode())
    assert len(doc["paths"]) == 8


def test_swagger_ui_returns_html(client: Client) -> None:
    response = client.get("/api/auth/schema/swagger/")
    assert response.status_code == 200
    assert "text/html" in response["Content-Type"]
    assert b"swagger" in response.content.lower()
