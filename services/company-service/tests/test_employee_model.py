"""Tests for Employee model."""

from __future__ import annotations

from datetime import date

import pytest
from core.models import CAE, Company, Employee, MaturityStage


@pytest.fixture
def cae(db) -> CAE:
    return CAE.objects.create(code="8888", description="Test CAE")


@pytest.fixture
def stage(db) -> MaturityStage:
    stage, _ = MaturityStage.objects.get_or_create(
        name=MaturityStage.Name.STARTUP,
        defaults={"rate_per_sqm": "10.00", "display_order": 98},
    )
    return stage


@pytest.fixture
def company(db, cae: CAE, stage: MaturityStage) -> Company:
    return Company.objects.create(
        name="Widget Lda",
        tax_id="PT888888888",
        legal_representative="Bob",
        cae=cae,
        maturity_stage=stage,
    )


@pytest.mark.django_db
def test_employee_creation(company: Company) -> None:
    emp = Employee.objects.create(
        company=company,
        name="Jane Doe",
        type=Employee.Type.REGULAR,
        start_date=date(2025, 1, 1),
    )
    assert emp.pk is not None
    assert emp.is_active is True
    assert emp.end_date is None
    assert "Jane Doe" in str(emp)
    assert "Widget Lda" in str(emp)


@pytest.mark.django_db
def test_employee_optional_end_date(company: Company) -> None:
    emp = Employee.objects.create(
        company=company,
        name="Temp",
        type=Employee.Type.INTERN,
        start_date=date(2025, 6, 1),
        end_date=date(2025, 8, 31),
    )
    assert emp.end_date == date(2025, 8, 31)


@pytest.mark.django_db
def test_active_manager_excludes_inactive(company: Company) -> None:
    active = Employee.objects.create(
        company=company,
        name="Active Person",
        type=Employee.Type.JUNIOR,
        start_date=date(2025, 1, 1),
    )
    inactive = Employee.objects.create(
        company=company,
        name="Left Person",
        type=Employee.Type.SENIOR,
        start_date=date(2024, 1, 1),
    )
    inactive.is_active = False
    inactive.save()

    active_pks = set(Employee.active.values_list("pk", flat=True))
    assert active.pk in active_pks
    assert inactive.pk not in active_pks


@pytest.mark.django_db
def test_company_reverse_relation(company: Company) -> None:
    Employee.objects.create(
        company=company,
        name="One",
        type=Employee.Type.PHD,
        start_date=date(2025, 1, 1),
    )
    Employee.objects.create(
        company=company,
        name="Two",
        type=Employee.Type.DESIGNER,
        start_date=date(2025, 2, 1),
    )
    assert company.employees.count() == 2
