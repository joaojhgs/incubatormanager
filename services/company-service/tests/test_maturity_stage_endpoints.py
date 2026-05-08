"""RBAC and API tests for maturity-stages endpoints."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from core.models import MaturityStage
from rest_framework.test import APIClient


def _client(role: str, company_id: str | None = None) -> APIClient:
    c = APIClient()
    headers = {
        "HTTP_X_USER_ID": str(uuid.uuid4()),
        "HTTP_X_USER_ROLE": role,
    }
    if company_id is not None:
        headers["HTTP_X_COMPANY_ID"] = company_id
    c.credentials(**headers)
    return c


URL = "/api/companies/maturity-stages/"
# Fixed seed id from migration 0002_maturity_stage_model
INCUBATED_ID = "11111111-1111-4111-8111-111111111111"


@pytest.mark.django_db
def test_list_maturity_stages_staff() -> None:
    response = _client("Staff").get(URL)
    assert response.status_code == 200
    assert len(response.json()) == 4


@pytest.mark.django_db
def test_list_maturity_stages_client() -> None:
    response = _client("Client", company_id=str(uuid.uuid4())).get(URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_list_maturity_stages_unauthenticated() -> None:
    response = APIClient().get(URL)
    assert response.status_code == 401


@pytest.mark.django_db
def test_list_maturity_stages_num_queries() -> None:
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    client = _client("Staff")
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(URL)
    assert response.status_code == 200
    assert len(ctx.captured_queries) <= 8


@pytest.mark.django_db
def test_retrieve_maturity_stage_director() -> None:
    response = _client("Director").get(f"{URL}{INCUBATED_ID}/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Incubated"
    assert data["id"] == INCUBATED_ID


@pytest.mark.django_db
def test_post_maturity_stage_director_after_slot_freed() -> None:
    MaturityStage.objects.filter(name="Consolidated").delete()
    payload = {
        "name": "Consolidated",
        "rate_per_sqm": "123.45",
        "description": "Re-seeded via API",
        "display_order": 4,
    }
    response = _client("Director").post(URL, data=payload, format="json")
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Consolidated"
    assert data["rate_per_sqm"] == "123.45"
    assert Decimal(str(data["rate_per_sqm"])) == Decimal("123.45")


@pytest.mark.django_db
def test_post_maturity_stage_staff_forbidden() -> None:
    MaturityStage.objects.filter(name="Consolidated").delete()
    response = _client("Staff").post(
        URL,
        data={
            "name": "Consolidated",
            "rate_per_sqm": "1.00",
            "description": "x",
            "display_order": 4,
        },
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_post_maturity_stage_duplicate_name_returns_400() -> None:
    response = _client("Director").post(
        URL,
        data={
            "name": "Incubated",
            "rate_per_sqm": "1.00",
            "description": "dup",
            "display_order": 99,
        },
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_patch_maturity_stage_director() -> None:
    response = _client("Director").patch(
        f"{URL}{INCUBATED_ID}/",
        data={"rate_per_sqm": "199.99", "description": "Updated copy"},
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rate_per_sqm"] == "199.99"
    assert data["description"] == "Updated copy"
    stage = MaturityStage.objects.get(id=INCUBATED_ID)
    assert stage.rate_per_sqm == Decimal("199.99")


@pytest.mark.django_db
def test_patch_maturity_stage_staff_forbidden() -> None:
    response = _client("Staff").patch(
        f"{URL}{INCUBATED_ID}/",
        data={"rate_per_sqm": "1.00"},
        format="json",
    )
    assert response.status_code == 403
