"""Tests for Company model."""

from __future__ import annotations

import pytest
from core.models import CAE, Company, MaturityStage
from django.db import IntegrityError


@pytest.fixture
def cae(db) -> CAE:
    return CAE.objects.create(code="9999", description="Test sector")


@pytest.fixture
def stage(db) -> MaturityStage:
    stage, _ = MaturityStage.objects.get_or_create(
        name=MaturityStage.Name.STARTUP,
        defaults={"rate_per_sqm": "10.00", "display_order": 99},
    )
    return stage


def _make_company(cae: CAE, stage: MaturityStage, tax_id: str = "PT123456789") -> Company:
    return Company.objects.create(
        name="Acme Lda",
        tax_id=tax_id,
        legal_representative="Alice",
        cae=cae,
        maturity_stage=stage,
    )


@pytest.mark.django_db
def test_company_creation(cae: CAE, stage: MaturityStage) -> None:
    company = _make_company(cae, stage)
    assert company.pk is not None
    assert company.is_active is True
    assert str(company) == "Acme Lda"


@pytest.mark.django_db
def test_tax_id_unique_constraint(cae: CAE, stage: MaturityStage) -> None:
    _make_company(cae, stage, tax_id="PT999999999")
    with pytest.raises(IntegrityError):
        _make_company(cae, stage, tax_id="PT999999999")


@pytest.mark.django_db
def test_active_manager_excludes_inactive(cae: CAE, stage: MaturityStage) -> None:
    active = _make_company(cae, stage, tax_id="PT111111111")
    inactive = _make_company(cae, stage, tax_id="PT222222222")
    inactive.is_active = False
    inactive.save()

    active_pks = set(Company.active.values_list("pk", flat=True))
    assert active.pk in active_pks
    assert inactive.pk not in active_pks
