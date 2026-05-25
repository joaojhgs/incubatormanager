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

    with (
        patch("core.services.transaction.on_commit") as on_commit,
        patch("core.services.publish") as publish,
    ):
        approve = _client("Staff").patch(f"/api/bookings/{booking.id}/approve/")
        assert approve.status_code == 200
        assert approve.json()["status"] == Booking.Status.APPROVED
        on_commit.call_args.args[0]()
        assert publish.call_args.args[1] == "booking.approved"
        assert publish.call_args.args[2]["booking_id"] == str(booking.id)
        assert publish.call_args.args[2]["equipment_ids"] == booking.equipment_ids


@pytest.mark.django_db
@override_settings(RABBITMQ_URL="amqp://rabbit")
def test_staff_approve_can_set_quote_company_and_equipment_payload() -> None:
    company_id = uuid.uuid4()
    equipment_id = uuid.uuid4()
    booking = Booking.objects.create(
        company_id=None,
        space_id=uuid.uuid4(),
        requester_name="Public user",
        requester_email="public@example.test",
        requester_phone="+351 900 000 000",
        start_time=timezone.now() + timedelta(days=1),
        end_time=timezone.now() + timedelta(days=1, hours=1),
    )

    with (
        patch("core.services.transaction.on_commit") as on_commit,
        patch("core.services.publish") as publish,
    ):
        approve = _client("Staff").patch(
            f"/api/bookings/{booking.id}/approve/",
            data={
                "company_id": str(company_id),
                "quoted_price": "42.50",
                "equipment_ids": [str(equipment_id)],
            },
            format="json",
        )
        assert approve.status_code == 200
        assert approve.json()["company_id"] == str(company_id)
        assert approve.json()["quoted_price"] == "42.50"
        assert approve.json()["equipment_ids"] == [str(equipment_id)]
        on_commit.call_args.args[0]()
        assert publish.call_args.args[2]["company_id"] == str(company_id)
        assert publish.call_args.args[2]["quoted_price"] == "42.50"
        assert publish.call_args.args[2]["equipment_ids"] == [str(equipment_id)]


@pytest.mark.django_db
def test_public_external_booking_requires_requester_fields() -> None:
    response = APIClient().post(
        "/api/bookings/external/",
        data={
            **_payload(),
            "requester_name": "Public user",
            "requester_email": "public@example.test",
            "requester_phone": "+351 900 000 000",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["requester_email"] == "public@example.test"
    assert response.json()["company_id"] is None


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

@pytest.mark.django_db
@override_settings(RABBITMQ_URL="amqp://rabbit")
@pytest.mark.parametrize(
    ("endpoint", "expected_status", "expected_event"),
    [
        ("reject", Booking.Status.REJECTED, "booking.rejected"),
        ("cancel", Booking.Status.CANCELLED, "booking.cancelled"),
        ("complete", Booking.Status.COMPLETED, "booking.completed"),
    ],
)
def test_staff_lifecycle_endpoints_publish_domain_events(
    endpoint: str,
    expected_status: str,
    expected_event: str,
) -> None:
    company_id = uuid.uuid4()
    booking = Booking.objects.create(
        company_id=company_id,
        space_id=uuid.uuid4(),
        start_time=timezone.now() - timedelta(hours=2),
        end_time=timezone.now() - timedelta(hours=1),
        quoted_price="10.00",
        status=Booking.Status.APPROVED if endpoint == "complete" else Booking.Status.PENDING,
    )

    with (
        patch("core.services.transaction.on_commit") as on_commit,
        patch("core.services.publish") as publish,
    ):
        response = _client("Staff").patch(f"/api/bookings/{booking.id}/{endpoint}/")
        assert response.status_code == 200
        assert response.json()["status"] == expected_status
        on_commit.call_args.args[0]()
        assert publish.call_args.args[1] == expected_event
        assert publish.call_args.args[2]["booking_id"] == str(booking.id)


@pytest.mark.django_db
@override_settings(RABBITMQ_URL="amqp://rabbit")
def test_complete_bookings_command_is_idempotent_and_publishes_completed_event() -> None:
    expired = Booking.objects.create(
        company_id=uuid.uuid4(),
        space_id=uuid.uuid4(),
        start_time=timezone.now() - timedelta(hours=3),
        end_time=timezone.now() - timedelta(hours=1),
        quoted_price="10.00",
        status=Booking.Status.APPROVED,
    )
    Booking.objects.create(
        company_id=uuid.uuid4(),
        space_id=uuid.uuid4(),
        start_time=timezone.now() + timedelta(hours=1),
        end_time=timezone.now() + timedelta(hours=2),
        quoted_price="10.00",
        status=Booking.Status.APPROVED,
    )

    with (
        patch("core.services.transaction.on_commit", side_effect=lambda callback: callback()),
        patch("core.services.publish") as publish,
    ):
        from django.core.management import call_command

        call_command("complete_bookings")
        expired.refresh_from_db()
        assert expired.status == Booking.Status.COMPLETED
        assert publish.call_count == 1
        assert publish.call_args.args[1] == "booking.completed"

        call_command("complete_bookings")
        assert publish.call_count == 1
