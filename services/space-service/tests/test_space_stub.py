"""Tests for stub Space model and seed data."""

from __future__ import annotations

import uuid

import pytest
from core.models import Space

STUB_IDS: tuple[uuid.UUID, ...] = (
    uuid.UUID("22222222-2222-4222-8222-222222222201"),
    uuid.UUID("22222222-2222-4222-8222-222222222202"),
    uuid.UUID("22222222-2222-4222-8222-222222222203"),
)


@pytest.mark.django_db
def test_stub_spaces_seeded_with_stable_uuids() -> None:
    assert Space.objects.count() == 3
    for space_id in STUB_IDS:
        space = Space.objects.get(id=space_id)
        assert space.is_active is True
        assert space.name
