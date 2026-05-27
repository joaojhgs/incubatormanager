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


def _client(
    role: str,
    company_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> APIClient:
    client = APIClient()
    headers = {
        "HTTP_X_USER_ID": str(user_id or uuid.uuid4()),
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
@override_settings(RABBITMQ_URL="amqp://rabbit")
def test_approve_requires_quoted_price_for_rental_charge_contract() -> None:
    booking = Booking.objects.create(
        company_id=uuid.uuid4(),
        space_id=uuid.uuid4(),
        start_time=timezone.now() + timedelta(days=1),
        end_time=timezone.now() + timedelta(days=1, hours=1),
    )

    response = _client("Staff").patch(f"/api/bookings/{booking.id}/approve/")

    assert response.status_code == 400
    booking.refresh_from_db()
    assert booking.status == Booking.Status.PENDING


@pytest.mark.django_db
def test_public_external_booking_requires_requester_fields() -> None:
    claimed_company = uuid.uuid4()
    response = APIClient().post(
        "/api/bookings/external/",
        data={
            **_payload(),
            "company_id": str(claimed_company),
            "requester_name": "Public user",
            "requester_email": "public@example.test",
            "requester_phone": "+351 900 000 000",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["requester_email"] == "public@example.test"
    assert response.json()["company_id"] == str(claimed_company)


@pytest.mark.django_db
def test_public_external_booking_rejects_overlapping_space_windows() -> None:
    space_id = uuid.uuid4()
    start = timezone.now() + timedelta(days=3)
    Booking.objects.create(
        company_id=uuid.uuid4(),
        space_id=space_id,
        requester_name="Existing requester",
        requester_email="existing@example.test",
        requester_phone="+351 900 000 000",
        start_time=start,
        end_time=start + timedelta(hours=2),
        status=Booking.Status.APPROVED,
    )

    response = APIClient().post(
        "/api/bookings/external/",
        data={
            "space_id": str(space_id),
            "start_time": (start + timedelta(minutes=30)).isoformat(),
            "end_time": (start + timedelta(hours=3)).isoformat(),
            "quoted_price": "25.00",
            "requester_name": "Public user",
            "requester_email": "public@example.test",
            "requester_phone": "+351 900 000 000",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "reserved" in str(response.json()).lower()


@pytest.mark.django_db
def test_public_booking_calendar_exposes_pending_and_approved_windows() -> None:
    space_id = uuid.uuid4()
    other_space_id = uuid.uuid4()
    start = timezone.now() + timedelta(days=4)
    pending = Booking.objects.create(
        company_id=None,
        space_id=space_id,
        start_time=start,
        end_time=start + timedelta(hours=1),
        status=Booking.Status.PENDING,
    )
    approved = Booking.objects.create(
        company_id=uuid.uuid4(),
        space_id=space_id,
        start_time=start + timedelta(hours=2),
        end_time=start + timedelta(hours=3),
        status=Booking.Status.APPROVED,
    )
    Booking.objects.create(
        company_id=uuid.uuid4(),
        space_id=space_id,
        start_time=start + timedelta(hours=4),
        end_time=start + timedelta(hours=5),
        status=Booking.Status.CANCELLED,
    )
    Booking.objects.create(
        company_id=uuid.uuid4(),
        space_id=other_space_id,
        start_time=start,
        end_time=start + timedelta(hours=1),
        status=Booking.Status.APPROVED,
    )

    response = APIClient().get(
        "/api/bookings/public-calendar/",
        {
            "space_id": str(space_id),
            "start": (start - timedelta(minutes=15)).isoformat(),
            "end": (start + timedelta(hours=3, minutes=15)).isoformat(),
        },
    )

    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [str(pending.id), str(approved.id)]


@pytest.mark.django_db
def test_booking_calendar_filters_by_space_and_overlapping_window() -> None:
    company_id = uuid.uuid4()
    space_id = uuid.uuid4()
    other_space_id = uuid.uuid4()
    start = timezone.now() + timedelta(days=2)
    matching = Booking.objects.create(
        company_id=company_id,
        space_id=space_id,
        start_time=start,
        end_time=start + timedelta(hours=2),
        status=Booking.Status.APPROVED,
    )
    Booking.objects.create(
        company_id=company_id,
        space_id=other_space_id,
        start_time=start,
        end_time=start + timedelta(hours=2),
        status=Booking.Status.APPROVED,
    )
    Booking.objects.create(
        company_id=company_id,
        space_id=space_id,
        start_time=start + timedelta(days=7),
        end_time=start + timedelta(days=7, hours=2),
        status=Booking.Status.APPROVED,
    )

    response = _client("Staff").get(
        "/api/bookings/calendar/",
        {
            "space_id": str(space_id),
            "start": (start - timedelta(minutes=30)).isoformat(),
            "end": (start + timedelta(minutes=30)).isoformat(),
        },
    )

    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [str(matching.id)]


@pytest.mark.django_db
@pytest.mark.parametrize("include_company", [False, True])
def test_client_create_booking_uses_header_company(include_company: bool) -> None:
    company_id = uuid.uuid4()
    payload = _payload(uuid.uuid4() if include_company else None)
    response = _client("Client", company_id).post("/api/bookings/", data=payload, format="json")
    assert response.status_code == 201
    assert response.json()["company_id"] == str(company_id)


@pytest.mark.django_db
@override_settings(RABBITMQ_URL="amqp://rabbit")
def test_client_cancel_requires_same_company_and_original_requester() -> None:
    company_id = uuid.uuid4()
    requester_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    booking = Booking.objects.create(
        company_id=company_id,
        space_id=uuid.uuid4(),
        created_by_user_id=requester_id,
        created_by_role="Client",
        start_time=timezone.now() + timedelta(days=1),
        end_time=timezone.now() + timedelta(days=1, hours=1),
        quoted_price="10.00",
        status=Booking.Status.APPROVED,
    )

    blocked = _client("Client", company_id, other_user_id).patch(
        f"/api/bookings/{booking.id}/cancel/"
    )
    assert blocked.status_code == 403
    booking.refresh_from_db()
    assert booking.status == Booking.Status.APPROVED

    with (
        patch("core.services.transaction.on_commit") as on_commit,
        patch("core.services.publish") as publish,
    ):
        allowed = _client("Client", company_id, requester_id).patch(
            f"/api/bookings/{booking.id}/cancel/"
        )
        on_commit.call_args.args[0]()

    assert allowed.status_code == 200
    assert allowed.json()["status"] == Booking.Status.CANCELLED
    assert publish.call_args.args[1] == "booking.cancelled"


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


@pytest.mark.django_db
@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": ["ilb_common.permissions.HeaderAuthentication"],
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
        "DEFAULT_THROTTLE_RATES": {"public_booking_ip": "5/minute"},
    }
)
def test_public_external_booking_throttled_after_five_requests_per_ip() -> None:
    client = APIClient()
    for index in range(5):
        response = client.post(
            "/api/bookings/external/",
            data={
                **_payload(),
                "requester_name": f"Public user {index}",
                "requester_email": f"public{index}@example.test",
                "requester_phone": "+351 900 000 000",
            },
            format="json",
            HTTP_X_FORWARDED_FOR="203.0.113.9",
        )
        assert response.status_code == 201

    blocked = client.post(
        "/api/bookings/external/",
        data={
            **_payload(),
            "requester_name": "Public user blocked",
            "requester_email": "blocked@example.test",
            "requester_phone": "+351 900 000 000",
        },
        format="json",
        HTTP_X_FORWARDED_FOR="203.0.113.9",
    )

    assert blocked.status_code == 429
    assert "throttled" in blocked.json()["detail"].lower()


@pytest.mark.django_db
def test_public_external_booking_throttle_is_per_client_ip() -> None:
    client = APIClient()
    for index in range(5):
        response = client.post(
            "/api/bookings/external/",
            data={
                **_payload(),
                "requester_name": f"Public user {index}",
                "requester_email": f"ip-a-{index}@example.test",
                "requester_phone": "+351 900 000 000",
            },
            format="json",
            HTTP_X_FORWARDED_FOR="203.0.113.10",
        )
        assert response.status_code == 201

    other_ip = client.post(
        "/api/bookings/external/",
        data={
            **_payload(),
            "requester_name": "Public user other IP",
            "requester_email": "ip-b@example.test",
            "requester_phone": "+351 900 000 000",
        },
        format="json",
        HTTP_X_FORWARDED_FOR="203.0.113.11",
    )

    assert other_ip.status_code == 201
