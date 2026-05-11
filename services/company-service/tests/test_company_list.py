"""Tests for GET /api/companies/ — filters, pagination, RBAC."""

from __future__ import annotations

import uuid

import pytest
from core.models import CAE, Company, MaturityStage
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient


def _api_client(role: str, company_id: str | None = None) -> APIClient:
    c = APIClient()
    headers: dict[str, str] = {
        "HTTP_X_USER_ID": str(uuid.uuid4()),
        "HTTP_X_USER_ROLE": role,
    }
    if company_id is not None:
        headers["HTTP_X_COMPANY_ID"] = company_id
    c.credentials(**headers)
    return c


@pytest.fixture
def cae_seed(db) -> CAE:
    return CAE.objects.create(code="LST7711", description="List test CAE A")


@pytest.fixture
def cae_other(db) -> CAE:
    return CAE.objects.create(code="LST7722", description="List test CAE B")


@pytest.fixture
def stage_startup(db) -> MaturityStage:
    st, _ = MaturityStage.objects.get_or_create(
        name=MaturityStage.Name.STARTUP,
        defaults={"rate_per_sqm": "22.50", "display_order": 2},
    )
    return st


@pytest.fixture
def stage_incubated(db) -> MaturityStage:
    st, _ = MaturityStage.objects.get_or_create(
        name=MaturityStage.Name.INCUBATED,
        defaults={"rate_per_sqm": "11.00", "display_order": 1},
    )
    return st


@pytest.fixture
def staff_client() -> APIClient:
    return _api_client("Staff")


@pytest.mark.django_db
def test_company_list_staff_returns_paginated_payload(
    staff_client: APIClient,
    db,
    cae_seed: CAE,
    stage_startup: MaturityStage,
) -> None:
    Company.objects.create(
        name="AlphaListCo",
        tax_id="PT111111211",
        legal_representative="A",
        cae=cae_seed,
        maturity_stage=stage_startup,
    )
    url = reverse("company-list")
    response = staff_client.get(url)
    assert response.status_code == 200
    payload = response.json()
    assert "count" in payload
    assert "results" in payload
    assert payload["count"] >= 1
    assert isinstance(payload["results"], list)
    assert payload["results"][0]["name"] == "AlphaListCo"


@pytest.mark.django_db
def test_company_list_filter_by_cae(
    staff_client: APIClient,
    db,
    cae_seed: CAE,
    cae_other: CAE,
    stage_startup: MaturityStage,
) -> None:
    Company.objects.create(
        name="OnCaeA",
        tax_id="PT222222322",
        legal_representative="R",
        cae=cae_seed,
        maturity_stage=stage_startup,
    )
    Company.objects.create(
        name="OnCaeB",
        tax_id="PT333333433",
        legal_representative="R",
        cae=cae_other,
        maturity_stage=stage_startup,
    )
    url = reverse("company-list")
    resp = staff_client.get(url, {"cae": str(cae_seed.id)})
    assert resp.status_code == 200
    names = {row["name"] for row in resp.json()["results"]}
    assert "OnCaeA" in names
    assert "OnCaeB" not in names


@pytest.mark.django_db
def test_company_list_filter_by_maturity(
    staff_client: APIClient,
    db,
    cae_seed: CAE,
    stage_startup: MaturityStage,
    stage_incubated: MaturityStage,
) -> None:
    Company.objects.create(
        name="StartupRow",
        tax_id="PT444444544",
        legal_representative="R",
        cae=cae_seed,
        maturity_stage=stage_startup,
    )
    Company.objects.create(
        name="IncubatedRow",
        tax_id="PT555555655",
        legal_representative="R",
        cae=cae_seed,
        maturity_stage=stage_incubated,
    )
    url = reverse("company-list")
    resp = staff_client.get(url, {"maturity": str(stage_incubated.id)})
    names = {row["name"] for row in resp.json()["results"]}
    assert "IncubatedRow" in names
    assert "StartupRow" not in names


@pytest.mark.django_db
def test_company_list_filter_is_active_false(
    staff_client: APIClient,
    db,
    cae_seed: CAE,
    stage_startup: MaturityStage,
) -> None:
    Company.objects.create(
        name="ArchivedCo",
        tax_id="PT666666766",
        legal_representative="R",
        cae=cae_seed,
        maturity_stage=stage_startup,
        is_active=False,
    )
    Company.objects.create(
        name="LiveCo",
        tax_id="PT777777877",
        legal_representative="R",
        cae=cae_seed,
        maturity_stage=stage_startup,
        is_active=True,
    )
    url = reverse("company-list")
    resp = staff_client.get(url, {"is_active": "false"})
    names = {row["name"] for row in resp.json()["results"]}
    assert "ArchivedCo" in names
    assert "LiveCo" not in names


@pytest.mark.django_db
def test_company_list_search_matches_name_fragment(
    staff_client: APIClient,
    db,
    cae_seed: CAE,
    stage_startup: MaturityStage,
) -> None:
    Company.objects.create(
        name="Oceanic Pineapple Ltd",
        tax_id="PT888888988",
        legal_representative="R",
        cae=cae_seed,
        maturity_stage=stage_startup,
    )
    Company.objects.create(
        name="OtherCorp",
        tax_id="PT999999099",
        legal_representative="R",
        cae=cae_seed,
        maturity_stage=stage_startup,
    )
    url = reverse("company-list")
    resp = staff_client.get(url, {"search": "Pine"})
    names = {row["name"] for row in resp.json()["results"]}
    assert "Oceanic Pineapple Ltd" in names
    assert "OtherCorp" not in names


@pytest.mark.django_db
def test_company_list_client_scope_own_company_only(
    db,
    cae_seed: CAE,
    stage_startup: MaturityStage,
) -> None:
    ours = Company.objects.create(
        name="ClientOwned",
        tax_id="PT101010101",
        legal_representative="R",
        cae=cae_seed,
        maturity_stage=stage_startup,
    )
    Company.objects.create(
        name="SomeoneElse",
        tax_id="PT202020202",
        legal_representative="R",
        cae=cae_seed,
        maturity_stage=stage_startup,
    )
    c = _api_client("Client", company_id=str(ours.id))
    url = reverse("company-list")
    resp = c.get(url)
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == str(ours.id)


@pytest.mark.django_db
def test_company_list_unauthenticated_denied(db) -> None:
    resp = APIClient().get(reverse("company-list"))
    assert resp.status_code == 401


@pytest.mark.django_db
def test_company_list_query_count_bounded_with_select_related(
    staff_client: APIClient,
    db,
    cae_seed: CAE,
    stage_startup: MaturityStage,
) -> None:
    for i in range(5):
        Company.objects.create(
            name=f"BatchCo{i}",
            tax_id=f"PT{900000001 + i:010d}",
            legal_representative="R",
            cae=cae_seed,
            maturity_stage=stage_startup,
        )
    url = reverse("company-list")
    with CaptureQueriesContext(connection) as ctx:
        response = staff_client.get(url)
    assert response.status_code == 200
    # Count + paginated SELECT with JOINs — no per-row extras.
    assert len(ctx.captured_queries) <= 4
