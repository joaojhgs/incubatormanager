"""Tests for CAE baseline seed data."""

from __future__ import annotations

import pytest
from core.models import CAE

EXPECTED_CAE_CODES = {
    "0111",
    "1011",
    "1413",
    "1812",
    "2042",
    "2611",
    "6201",
    "7022",
    "7219",
    "8559",
}


@pytest.mark.django_db
def test_cae_seed_contains_expected_10_codes() -> None:
    codes = set(CAE.objects.values_list("code", flat=True))
    assert len(codes) == 10
    assert codes == EXPECTED_CAE_CODES
