"""Tests for GET /api/companies/{id}/ (detail, optimized queryset)."""

from __future__ import annotations

import time
import uuid

import pytest
from core.models import CAE, Company, Employee, MaturityStage
from django.test import Client
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
def cae(db) -> CAE:
    return CAE.objects.create(code="8888", description="Detail test CAE")


@pytest.fixture
def stage(db) -> MaturityStage:
    st, _ = MaturityStage.objects.get_or_create(
        name=MaturityStage.Name.STARTUP,
        defaults={"rate_per_sqm": "22.50", "display_order": 2},
    )
    return st


@pytest.fixture
def company(db, cae: CAE, stage: MaturityStage) -> Company:
    return Company.objects.create(
        name="DetailCo",
        tax_id="PT111111117",
        legal_representative="Rep",
        cae=cae,
        maturity_stage=stage,
    )


@pytest.fixture
def company_url(company: Company) -> str:
    return f"/api/companies/{company.pk}/"


@pytest.mark.django_db
def test_company_detail_staff_ok(company_url: str, company: Company) -> None:
    response = _api_client("Staff").get(company_url)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(company.pk)
    assert data["name"] == "DetailCo"
    assert data["tax_id"] == "PT111111117"
    assert data["cae"]["code"] == "8888"
    assert data["maturity_stage"]["name"] == MaturityStage.Name.STARTUP
    assert data["employees"] == []


@pytest.mark.django_db
def test_company_detail_director_ok(company_url: str) -> None:
    response = _api_client("Director").get(company_url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_company_detail_client_own_company(company_url: str, company: Company) -> None:
    response = _api_client("Client", company_id=str(company.pk)).get(company_url)
    assert response.status_code == 200
    assert response.json()["id"] == str(company.pk)


@pytest.mark.django_db
def test_company_detail_client_foreign_company_returns_404(
    company_url: str, company: Company
) -> None:
    other = uuid.uuid4()
    assert other != company.pk
    response = _api_client("Client", company_id=str(other)).get(company_url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_company_detail_client_without_company_returns_404(company_url: str) -> None:
    """Client header without X-Company-Id cannot resolve a scoped company row."""

    response = _api_client("Client", company_id=None).get(company_url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_company_detail_unauthenticated(company_url: str) -> None:
    client = Client()
    response = client.get(company_url)
    assert response.status_code == 401


@pytest.mark.django_db
def test_company_detail_inactive_not_visible_for_staff(company_url: str, company: Company) -> None:
    company.is_active = False
    company.save(update_fields=("is_active",))
    response = _api_client("Staff").get(company_url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_company_detail_bounded_queries_with_many_active_employees(
    django_assert_max_num_queries,
    company_url: str,
    company: Company,
    db,
) -> None:
    """Detail must not N+1 when many employees belong to the company."""

    Employee.objects.bulk_create(
        [
            Employee(
                id=uuid.uuid4(),
                company=company,
                name=f"Member {idx}",
                type=Employee.Type.REGULAR,
                start_date="2026-01-01",
                is_active=True,
            )
            for idx in range(100)
        ]
    )

    api = _api_client("Staff")

    with django_assert_max_num_queries(8):
        response = api.get(company_url)

    assert response.status_code == 200
    assert len(response.json()["employees"]) == 100


@pytest.mark.django_db
def test_company_detail_single_request_remains_fast_with_100_distinct_companies(
    company_url: str,
    company: Company,
    cae: CAE,
    stage: MaturityStage,
    db,
) -> None:
    """Wall-clock budget per NFR: detail stays under 50ms with 100 companies in the database."""

    Employee.objects.bulk_create(
        [
            Employee(
                id=uuid.uuid4(),
                company=company,
                name=f"Emp {idx}",
                type=Employee.Type.REGULAR,
                start_date="2026-01-01",
                is_active=True,
            )
            for idx in range(5)
        ]
    )

    for i in range(100):
        suffix = f"x{i:03d}"
        Company.objects.create(
            name=f"Sister {suffix}",
            tax_id=f"PTSIS{suffix}suff",
            legal_representative="X",
            cae=cae,
            maturity_stage=stage,
        )

    api = _api_client("Staff")
    budgets_ms: list[float] = []
    for _ in range(10):
        start = time.perf_counter()
        response = api.get(company_url)
        budgets_ms.append((time.perf_counter() - start) * 1000.0)
        assert response.status_code == 200

    assert sum(budgets_ms) / len(budgets_ms) < 50.0
