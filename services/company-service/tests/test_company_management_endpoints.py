"""Phase 2 company management endpoints (create/update/maturity/employee endpoints)."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from core.models import CAE, Company, Employee, MaturityStage
from django.urls import reverse
from rest_framework.test import APIClient


def _api_client(role: str, company_id: str | None = None) -> APIClient:
    headers = {
        "HTTP_X_USER_ID": str(uuid.uuid4()),
        "HTTP_X_USER_ROLE": role,
    }
    if company_id is not None:
        headers["HTTP_X_COMPANY_ID"] = company_id

    client = APIClient()
    client.credentials(**headers)
    return client


@pytest.fixture
def company_payloads(db) -> tuple[CAE, MaturityStage, MaturityStage]:
    cae = CAE.objects.create(code="X123", description="Test CAE")
    startup = MaturityStage.objects.create(
        name="Incubated", rate_per_sqm="10.00", display_order=10
    )
    growth = MaturityStage.objects.create(
        name="Startup", rate_per_sqm="20.00", display_order=20
    )
    return cae, startup, growth


@pytest.mark.django_db
def test_create_company_staff_ok(company_payloads: tuple[CAE, MaturityStage, MaturityStage]) -> None:
    cae, startup, _ = company_payloads
    payload = {
        "name": "CreateCo",
        "tax_id": "PT111111111",
        "address": "A street",
        "phone": "1234",
        "email": "a@b.com",
        "legal_representative": "Rep A",
        "description": "test",
        "cae": str(cae.id),
        "maturity_stage": str(startup.id),
    }

    client = _api_client("Staff")
    response = client.post(reverse("company-list"), data=payload, format="json")

    assert response.status_code == 201
    result = response.json()
    assert result["name"] == payload["name"]
    assert Company.objects.filter(pk=result["id"]).exists()


@pytest.mark.django_db
def test_create_company_client_forbidden(company_payloads: tuple[CAE, MaturityStage, MaturityStage]) -> None:
    cae, startup, _ = company_payloads
    payload = {
        "name": "Forbidden",
        "tax_id": "PT222222222",
        "legal_representative": "Rep B",
        "cae": str(cae.id),
        "maturity_stage": str(startup.id),
    }

    client = _api_client("Client", company_id=str(uuid.uuid4()))
    response = client.post(reverse("company-list"), data=payload, format="json")

    assert response.status_code == 403


@pytest.mark.django_db
def test_company_patch_updates_maturity_stage(company_payloads: tuple[CAE, MaturityStage, MaturityStage]) -> None:
    cae, incubated, growth = company_payloads
    target = Company.objects.create(
        name="CoM",
        tax_id="PT333333333",
        legal_representative="Rep C",
        cae=cae,
        maturity_stage=incubated,
    )

    client = _api_client("Staff")
    response = client.patch(
        f"/api/companies/{target.pk}/maturity-stage/",
        data={"maturity_stage": str(growth.id)},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["maturity_stage"]["id"] == str(growth.id)
    target.refresh_from_db()
    assert str(target.maturity_stage_id) == str(growth.id)


@pytest.mark.django_db
def test_company_soft_delete_marks_inactive(company_payloads: tuple[CAE, MaturityStage, MaturityStage]) -> None:
    cae, startup, _ = company_payloads
    target = Company.objects.create(
        name="SoftDelete",
        tax_id="PT444444444",
        legal_representative="Rep",
        cae=cae,
        maturity_stage=startup,
    )

    client = _api_client("Staff")
    response = client.delete(f"/api/companies/{target.pk}/")
    assert response.status_code == 204

    target.refresh_from_db()
    assert target.is_active is False


@pytest.mark.django_db
def test_employee_crud_for_company(company_payloads: tuple[CAE, MaturityStage, MaturityStage]) -> None:
    cae, startup, _ = company_payloads
    target = Company.objects.create(
        name="EmpCo",
        tax_id="PT555555555",
        legal_representative="Rep",
        cae=cae,
        maturity_stage=startup,
    )

    staff = _api_client("Staff")

    list_response = staff.get(f"/api/companies/{target.pk}/employees/")
    assert list_response.status_code == 200
    assert list_response.json() == []

    create_response = staff.post(
        f"/api/companies/{target.pk}/employees/",
        data={
            "name": "Ana",
            "type": "Regular",
            "start_date": "2026-01-01",
            "is_active": True,
        },
        format="json",
    )
    assert create_response.status_code == 201
    emp_id = create_response.json()["id"]
    assert create_response.json()["name"] == "Ana"

    patch_response = staff.patch(
        f"/api/companies/{target.pk}/employees/{emp_id}/",
        data={"end_date": "2026-01-31"},
        format="json",
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["end_date"] == "2026-01-31"

    del_response = staff.delete(f"/api/companies/{target.pk}/employees/{emp_id}/")
    assert del_response.status_code == 204

    assert not Employee.objects.filter(pk=emp_id).exists()


@pytest.mark.django_db
def test_employee_stats_scoped_to_company(company_payloads: tuple[CAE, MaturityStage, MaturityStage]) -> None:
    cae, startup, _ = company_payloads
    ours = Company.objects.create(
        name="StatsCo",
        tax_id="PT666666666",
        legal_representative="Rep",
        cae=cae,
        maturity_stage=startup,
    )
    theirs = Company.objects.create(
        name="OtherCo",
        tax_id="PT777777777",
        legal_representative="Rep",
        cae=cae,
        maturity_stage=startup,
    )

    Employee.objects.create(
        company=ours,
        name="Active",
        type=Employee.Type.REGULAR,
        start_date=date(2026, 1, 1),
        is_active=True,
    )
    Employee.objects.create(
        company=ours,
        name="Intern",
        type=Employee.Type.INTERN,
        start_date=date(2026, 1, 2),
        is_active=False,
    )
    Employee.objects.create(
        company=theirs,
        name="Other",
        type=Employee.Type.REGULAR,
        start_date=date(2026, 1, 3),
        is_active=True,
    )

    client = _api_client("Client", company_id=str(ours.pk))
    response = client.get(f"/api/companies/{ours.pk}/employees/stats/")
    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 2
    assert payload["active"] == 1
    assert payload["by_type"][Employee.Type.REGULAR] == 1
    assert payload["by_type"][Employee.Type.INTERN] == 1
