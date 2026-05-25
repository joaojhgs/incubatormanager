"""Space CRUD, occupancy, and event projection tests."""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from core.models import ProcessedEvent, Space, SpaceBookingRecord, SpaceContract
from core.services import apply_booking_event_dict, apply_contract_event
from django.utils import timezone
from rest_framework.test import APIClient


def _client(role: str = "Staff", company_id: uuid.UUID | None = None) -> APIClient:
    client = APIClient()
    headers = {"HTTP_X_USER_ID": str(uuid.uuid4()), "HTTP_X_USER_ROLE": role}
    if company_id is not None:
        headers["HTTP_X_COMPANY_ID"] = str(company_id)
    client.credentials(**headers)
    return client


@pytest.mark.django_db
def test_space_type_space_crud_and_occupancy_map() -> None:
    type_response = _client().post("/api/space-types/", data={"name": "Office"}, format="json")
    assert type_response.status_code == 201
    space_response = _client().post(
        "/api/spaces/",
        data={"name": "Room A", "space_type": type_response.json()["id"], "capacity": 2},
        format="json",
    )
    assert space_response.status_code == 201
    space = Space.objects.get(pk=space_response.json()["id"])
    SpaceBookingRecord.objects.create(
        booking_id=uuid.uuid4(),
        space=space,
        company_id=uuid.uuid4(),
        status=SpaceBookingRecord.Status.APPROVED,
        start_time=timezone.now() - timedelta(minutes=10),
        end_time=timezone.now() + timedelta(minutes=50),
    )

    occupancy = _client().get("/api/spaces/occupancy-map/")
    assert occupancy.status_code == 200
    assert occupancy.json()[0]["occupied"] == 1
    assert occupancy.json()[0]["occupancy_percent"] == "50.00"


@pytest.mark.django_db
def test_contract_and_booking_events_are_idempotent() -> None:
    space = Space.objects.create(name="Event room", capacity=1)
    contract_event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "contract.activated",
        "occurred_at": "",
        "payload": {
            "contract_id": str(uuid.uuid4()),
            "company_id": str(uuid.uuid4()),
            "space_id": str(space.id),
            "area_sqm": "10.00",
            "rate_per_sqm": "2.00",
            "monthly_fee": "20.00",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        },
    }
    apply_contract_event(contract_event)  # type: ignore[arg-type]
    apply_contract_event(contract_event)  # type: ignore[arg-type]
    assert SpaceContract.objects.count() == 1
    assert ProcessedEvent.objects.count() == 1
    space.refresh_from_db()
    assert space.status == Space.Status.OCCUPIED

    expired_event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "contract.expired",
        "occurred_at": "",
        "payload": {"contract_id": contract_event["payload"]["contract_id"]},
    }
    apply_contract_event(expired_event)  # type: ignore[arg-type]
    apply_contract_event(expired_event)  # type: ignore[arg-type]
    contract = SpaceContract.objects.get()
    assert contract.status == SpaceContract.Status.EXPIRED
    assert ProcessedEvent.objects.count() == 2
    space.refresh_from_db()
    assert space.status == Space.Status.AVAILABLE

    booking_event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "booking.approved",
        "occurred_at": "",
        "payload": {
            "booking_id": str(uuid.uuid4()),
            "company_id": contract_event["payload"]["company_id"],
            "space_id": str(space.id),
            "start_time": timezone.now().isoformat(),
            "end_time": (timezone.now() + timedelta(hours=1)).isoformat(),
            "quoted_price": "12.00",
            "equipment_ids": [],
        },
    }
    apply_booking_event_dict(booking_event)  # type: ignore[arg-type]
    apply_booking_event_dict(booking_event)  # type: ignore[arg-type]
    assert SpaceBookingRecord.objects.count() == 1
    assert ProcessedEvent.objects.count() == 3
    space.refresh_from_db()
    assert space.status == Space.Status.RESERVED

    cancelled_event = {
        **booking_event,
        "event_id": str(uuid.uuid4()),
        "event_type": "booking.cancelled",
        "payload": {
            **booking_event["payload"],
            "company_id": None,
        },
    }
    apply_booking_event_dict(cancelled_event)  # type: ignore[arg-type]
    space.refresh_from_db()
    assert space.status == Space.Status.AVAILABLE
