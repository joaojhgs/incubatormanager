"""Tests for MaturityStage model and seed data."""

import pytest
from core.models import MaturityStage


@pytest.mark.django_db
def test_maturity_stages_seeded():
    stages = MaturityStage.objects.order_by("display_order")
    assert stages.count() == 4
    names = list(stages.values_list("name", flat=True))
    assert names == ["Incubated", "Startup", "Intermediate", "Consolidated"]


@pytest.mark.django_db
def test_maturity_stage_rates_are_distinct():
    rates = list(MaturityStage.objects.values_list("rate_per_sqm", flat=True))
    assert len(rates) == len(set(rates)), "rate_per_sqm values must be distinct"


@pytest.mark.django_db
def test_maturity_stage_descriptions_populated():
    stages = MaturityStage.objects.all()
    for stage in stages:
        assert stage.description, f"Stage {stage.name} has empty description"


@pytest.mark.django_db
def test_maturity_stage_display_order():
    qs = MaturityStage.objects.order_by("display_order").values_list("display_order", flat=True)
    orders = list(qs)
    assert orders == [1, 2, 3, 4]


@pytest.mark.django_db
def test_maturity_stage_str():
    stage = MaturityStage.objects.get(name="Incubated")
    assert str(stage) == "Incubated"
