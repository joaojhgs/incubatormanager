"""Tests for document metadata model."""

from __future__ import annotations

import uuid

import pytest
from core.models import Document


@pytest.mark.django_db
def test_document_create_polymorphic_company() -> None:
    company_id = uuid.uuid4()
    uploader = uuid.uuid4()
    doc = Document.objects.create(
        entity_type=Document.EntityType.COMPANY,
        entity_id=company_id,
        file_name="statutes.pdf",
        file_path="bucket/companies/abc/statutes.pdf",
        file_size=2048,
        mime_type="application/pdf",
        description="Company statutes",
        uploaded_by=uploader,
    )
    assert doc.pk is not None
    assert doc.entity_type == Document.EntityType.COMPANY
    assert doc.entity_id == company_id
    assert doc.uploaded_by == uploader
    assert "statutes" in str(doc)


@pytest.mark.django_db
def test_document_create_polymorphic_booking() -> None:
    booking_id = uuid.uuid4()
    doc = Document.objects.create(
        entity_type=Document.EntityType.BOOKING,
        entity_id=booking_id,
        file_name="booking-attachment.pdf",
        file_path="bucket/bookings/abc/booking-attachment.pdf",
        file_size=1024,
        mime_type="application/pdf",
    )
    assert doc.pk is not None
    assert doc.entity_type == Document.EntityType.BOOKING
    assert doc.entity_id == booking_id


@pytest.mark.django_db
def test_document_list_by_entity_indexed() -> None:
    eid = uuid.uuid4()
    Document.objects.create(
        entity_type=Document.EntityType.CONTRACT,
        entity_id=eid,
        file_name="a.pdf",
        file_path="p/a",
        file_size=1,
    )
    Document.objects.create(
        entity_type=Document.EntityType.CONTRACT,
        entity_id=eid,
        file_name="b.pdf",
        file_path="p/b",
        file_size=2,
    )
    other = uuid.uuid4()
    Document.objects.create(
        entity_type=Document.EntityType.CONTRACT,
        entity_id=other,
        file_name="c.pdf",
        file_path="p/c",
        file_size=3,
    )
    qs = Document.objects.filter(
        entity_type=Document.EntityType.CONTRACT,
        entity_id=eid,
    ).order_by("-uploaded_at")
    assert qs.count() == 2
