"""Tests for company create/update, maturity changes, and employee/stat endpoints."""

from __future__ import annotations

import uuid

from unittest.mock import patch

import pytest
from core.models import CAE, Company, Employee, MaturityStage
from rest_framework.test import APIClient


def _api_client(role: str, company_id: str | None = None) -> APIClient:
    c = APIClient()
    headers = {
        "HTTP_X_USER_ID": str(uuid.uuid4()),
        "HTTP_X_USER_ROLE": role,
    }
    if company_id is not None:
        headers["HTTP_X_COMPANY_ID"] = company_id
    c.credentials(**headers)
    return c


@pytest.fixture
def company_payloads(db) -> tuple[CAE, MaturityStage, MaturityStage]:
    token = uuid.uuid4().hex[:8]
    cae = CAE.objects.create(code=f"X{token}", description="Test CAE")
    startup = MaturityStage.objects.create(
        name=f"Incubated {token}",
        rate_per_sqm="10.00",
        display_order=10,
    )
    growth = MaturityStage.objects.create(
        name=f"Startup {token}",
        rate_per_sqm="20.00",
        display_order=20,
    )
    return cae, startup, growth


@pytest.fixture
def stage_startup(db) -> MaturityStage:
    stage, _ = MaturityStage.objects.get_or_create(
        name=MaturityStage.Name.STARTUP,
        defaults={"rate_per_sqm": "22.50", "display_order": 2},
    )
    return stage


@pytest.fixture
def stage_incubated(db) -> MaturityStage:
    stage, _ = MaturityStage.objects.get_or_create(
        name=MaturityStage.Name.INCUBATED,
        defaults={"rate_per_sqm": "100.00", "display_order": 1},
    )
    return stage


def _company_payload(cae: CAE, stage: MaturityStage, **overrides: str) -> dict[str, object]:
    payload = {
        "name": "Acme Nova",
        "tax_id": "PT111111111",
        "legal_representative": "Rita",
        "address": "12 Seed Way",
        "phone": "111",
        "email": "acme@example.org",
        "description": "Seed company",
        "cae": str(cae.id),
        "maturity_stage": str(stage.id),
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db(transaction=True)
def test_company_create_post_staff_publishes_event_on_commit(
    monkeypatch: pytest.MonkeyPatch,
    db,
    cae_seed: CAE,
    stage_startup: MaturityStage,
) -> None:
    monkeypatch.setenv("RABBITMQ_URL", "amqp://rabbit")

    with patch("core.views.transaction.on_commit") as on_commit, patch(
        "core.views.event_bus.publish"
    ) as publish:
        response = _api_client("Staff").post(
            "/api/companies/",
            data=_company_payload(cae_seed, stage_startup),
            format="json",
        )
        assert response.status_code == 201
        assert Company.objects.filter(name="Acme Nova").exists()
        assert on_commit.call_count == 1

        callback = on_commit.call_args.args[0]
        callback()
        assert publish.call_count == 1
        published = publish.call_args.args
        assert published[1] == "company.created"
        assert published[2]["name"] == "Acme Nova"


@pytest.mark.django_db
def test_company_post_client_forbidden(cae_seed: CAE, stage_startup: MaturityStage) -> None:
    response = _api_client("Client", company_id=str(uuid.uuid4())).post(
        "/api/companies/",
        data=_company_payload(cae_seed, stage_startup),
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_company_patch_staff_updates_fields(
    db,
    cae_seed: CAE,
    stage_startup: MaturityStage,
    stage_incubated: MaturityStage,
) -> None:
    company = Company.objects.create(
        name="Before",
        tax_id="PT111111113",
        legal_representative="A",
        cae=cae_seed,
        maturity_stage=stage_startup,
    )
    response = _api_client("Staff").patch(
        f"/api/companies/{company.id}/",
        data={"name": "After", "maturity_stage": str(stage_incubated.id)},
        format="json",
    )
    assert response.status_code == 200
    company.refresh_from_db()
    assert company.name == "After"


@pytest.mark.django_db
def test_company_delete_staff_soft_deletes(
    db,
    cae_seed: CAE,
    stage_startup: MaturityStage,
) -> None:
    company = Company.objects.create(
        name="ToRemove",
        tax_id="PT111111114",
        legal_representative="A",
        cae=cae_seed,
        maturity_stage=stage_startup,
    )
    response = _api_client("Staff").delete(f"/api/companies/{company.id}/")
    assert response.status_code == 204
    company.refresh_from_db()
    assert company.is_active is False


@pytest.mark.django_db
def test_company_maturity_stage_change_endpoint(
    db,
    cae_seed: CAE,
    stage_startup: MaturityStage,
    stage_incubated: MaturityStage,
) -> None:
    company = Company.objects.create(
        name="Mature",
        tax_id="PT111111115",
        legal_representative="A",
        cae=cae_seed,
        maturity_stage=stage_startup,
    )
    response = _api_client("Staff").patch(
        f"/api/companies/{company.id}/maturity-stage/",
        data={"maturity_stage": str(stage_incubated.id)},
        format="json",
    )
    assert response.status_code == 200
    company.refresh_from_db()
    assert str(company.maturity_stage_id) == str(stage_incubated.id)


@pytest.mark.django_db
def test_company_employee_crud_scoped(
    db,
    cae_seed: CAE,
    stage_startup: MaturityStage,
) -> None:
    company = Company.objects.create(
        name="WithStaff",
        tax_id="PT111111116",
        legal_representative="A",
        cae=cae_seed,
        maturity_stage=stage_startup,
    )

    create_payload = {
        "name": "Alice",
        "type": Employee.Type.SENIOR,
        "start_date": "2026-01-01",
    }
    list_url = f"/api/companies/{company.id}/employees/"
    response = _api_client("Staff").post(list_url, data=create_payload, format="json")
    assert response.status_code == 201

    response = _api_client("Staff").get(list_url)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    employee_id = data[0]["id"]

    patch_url = f"/api/companies/{company.id}/employees/{employee_id}/"
    response = _api_client("Staff").patch(
        patch_url,
        data={"is_active": False},
        format="json",
    )
    assert response.status_code == 200
    emp = Employee.objects.get(pk=employee_id)
    assert emp.is_active is False

    response = _api_client("Staff").delete(patch_url)
    assert response.status_code == 204
    assert not Employee.objects.filter(pk=employee_id).exists()


@pytest.mark.django_db
def test_company_employee_stats_for_company_scope(
    db,
    cae_seed: CAE,
    stage_startup: MaturityStage,
) -> None:
    company = Company.objects.create(
        name="ForStats",
        tax_id="PT111111117",
        legal_representative="A",
        cae=cae_seed,
        maturity_stage=stage_startup,
    )
    Employee.objects.create(
        id=uuid.uuid4(),
        company=company,
        name="A",
        type=Employee.Type.INTERN,
        start_date="2026-01-01",
        is_active=True,
    )
    Employee.objects.create(
        id=uuid.uuid4(),
        company=company,
        name="B",
        type=Employee.Type.SENIOR,
        start_date="2026-01-01",
        is_active=False,
    )

    response = _api_client("Staff").get(f"/api/companies/{company.id}/employees/stats/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["active"] == 1
    assert payload["inactive"] == 1
    assert payload["by_type"][Employee.Type.INTERN] == 1


@pytest.mark.django_db
def test_company_stats_scope_for_staff_and_client(
    db,
    cae_seed: CAE,
    stage_startup: MaturityStage,
) -> None:
    ours = Company.objects.create(
        name="Own",
        tax_id="PT111111118",
        legal_representative="A",
        cae=cae_seed,
        maturity_stage=stage_startup,
    )
    other = Company.objects.create(
        name="Other",
        tax_id="PT111111119",
        legal_representative="B",
        cae=cae_seed,
        maturity_stage=stage_startup,
        is_active=False,
    )

    staff_response = _api_client("Staff").get("/api/companies/stats/")
    assert staff_response.status_code == 200
    assert staff_response.json()["total"] == 2

    client_response = _api_client("Client", company_id=str(ours.id)).get(
        "/api/companies/stats/"
    )
    assert client_response.status_code == 200
    assert client_response.json() == {
        "total": 1,
        "active": 1,
        "inactive": 0,
    }
