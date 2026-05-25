"""Booking lifecycle and company scoping tests."""

from __future__ import annotations

import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from core.models import Booking
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient


def _client(role: str, company_id: uuid.UUID | None = None) -> APIClient:
    client = APIClient()
    headers = {
        "HTTP_X_USER_ID": str(uuid.uuid4()),
        "HTTP_X_USER_ROLE": role,
    }
    if company_id is not None:
        headers["HTTP_X_COMPANY_ID"] = str(company_id)
    client.credentials(**headers)
    return client


def _payload(company_id: uuid.UUID | None = None) -> dict[str, object]:
    start = timezone.now() + timedelta(days=1)
    payload: dict[str, object] = {
        "space_id": str(uuid.uuid4()),
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(hours=2)).isoformat(),
        "quoted_price": "25.00",
        "equipment_ids": [str(uuid.uuid4())],
        "notes": "demo booking",
    }
    if company_id is not None:
        payload["company_id"] = str(company_id)
    return payload


@pytest.mark.django_db
@override_settings(RABBITMQ_URL="amqp://rabbit")
def test_staff_create_and_approve_booking_publishes_event() -> None:
    company_id = uuid.uuid4()
    response = _client("Staff").post("/api/bookings/", data=_payload(company_id), format="json")
    assert response.status_code == 201
    booking = Booking.objects.get(company_id=company_id)
    assert booking.company_id == company_id

    with patch("core.services.transaction.on_commit") as on_commit, patch("core.services.publish") as publish:
        approve = _client("Staff").patch(f"/api/bookings/{booking.id}/approve/")
        assert approve.status_code == 200
        assert approve.json()["status"] == Booking.Status.APPROVED
        on_commit.call_args.args[0]()
        assert publish.call_args.args[1] == "booking.approved"
        assert publish.call_args.args[2]["booking_id"] == str(booking.id)


@pytest.mark.django_db
@pytest.mark.parametrize("include_company", [False, True])
def test_client_create_booking_uses_header_company(include_company: bool) -> None:
    company_id = uuid.uuid4()
    payload = _payload(uuid.uuid4() if include_company else None)
    response = _client("Client", company_id).post("/api/bookings/", data=payload, format="json")
    assert response.status_code == 201
    assert response.json()["company_id"] == str(company_id)


@pytest.mark.django_db
@pytest.mark.parametrize("endpoint", ["reject", "complete"])
def test_staff_only_lifecycle_endpoints_reject_clients(endpoint: str) -> None:
    company_id = uuid.uuid4()
    booking = Booking.objects.create(
        company_id=company_id,
        space_id=uuid.uuid4(),
        start_time=timezone.now() + timedelta(days=1),
        end_time=timezone.now() + timedelta(days=1, hours=1),
        quoted_price="10.00",
    )
    response = _client("Client", company_id).patch(f"/api/bookings/{booking.id}/{endpoint}/")
    assert response.status_code == 403
