"""Tests for dashboard aggregation endpoints."""

from __future__ import annotations

import json
import uuid
from io import BytesIO
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient


def _client(role: str = "Staff") -> APIClient:
    client = APIClient()
    client.credentials(
        HTTP_X_USER_ID=str(uuid.uuid4()),
        HTTP_X_USER_ROLE=role,
    )
    return client


class _FakeHTTPResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


@pytest.mark.django_db
@patch("core.views.urlopen")
def test_dashboard_overview_returns_service_and_metric_snapshots(urlopen) -> None:
    urlopen.return_value = _FakeHTTPResponse(json.dumps({"status": "ok"}).encode())

    response = _client().get("/api/dashboard/overview/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["services"]["company"]["status"] == "up"
    assert "finance" in payload["metrics"]
    assert urlopen.call_count >= 9


@pytest.mark.django_db
def test_dashboard_overview_is_staff_only() -> None:
    response = _client("Client").get("/api/dashboard/overview/")

    assert response.status_code == 403


@pytest.mark.django_db
@patch("core.views.urlopen")
def test_dashboard_reports_handles_downstream_errors(urlopen) -> None:
    urlopen.side_effect = OSError("offline")

    response = _client().get("/api/dashboard/reports/")

    assert response.status_code == 200
    rows = response.json()["rows"]
    assert rows
    assert {row["status"] for row in rows} == {"down"}
