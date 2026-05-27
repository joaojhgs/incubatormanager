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
    other_type_response = _client().post(
        "/api/space-types/", data={"name": "Meeting Room"}, format="json"
    )
    assert other_type_response.status_code == 201
    space_response = _client().post(
        "/api/spaces/",
        data={
            "name": "Room A",
            "space_type": type_response.json()["id"],
            "capacity": 2,
            "rental_cost": "35.00",
            "rental_cost_unit": "day",
        },
        format="json",
    )
    assert space_response.status_code == 201
    other_space_response = _client().post(
        "/api/spaces/",
        data={
            "name": "Room B",
            "space_type": other_type_response.json()["id"],
            "capacity": 1,
            "status": Space.Status.MAINTENANCE,
        },
        format="json",
    )
    assert other_space_response.status_code == 201
    assert space_response.json()["rental_cost"] == "35.00"
    assert space_response.json()["rental_cost_unit"] == "day"
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

    filtered = _client().get(
        "/api/spaces/",
        {"status": Space.Status.AVAILABLE, "space_type": type_response.json()["id"]},
    )
    assert filtered.status_code == 200
    assert [row["id"] for row in filtered.json()] == [space_response.json()["id"]]


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


@pytest.mark.django_db
def test_client_space_scope_includes_own_and_available_unassigned_spaces() -> None:
    company_id = uuid.uuid4()
    own_space = Space.objects.create(
        name="Own office",
        capacity=4,
        company_id=company_id,
        status=Space.Status.OCCUPIED,
    )
    reservable_space = Space.objects.create(
        name="Shared room",
        capacity=10,
        company_id=None,
        status=Space.Status.AVAILABLE,
    )
    other_space = Space.objects.create(
        name="Other office",
        capacity=3,
        company_id=uuid.uuid4(),
        status=Space.Status.OCCUPIED,
    )
    maintenance_space = Space.objects.create(
        name="Maintenance room",
        capacity=6,
        company_id=None,
        status=Space.Status.MAINTENANCE,
    )

    response = _client("Client", company_id=company_id).get("/api/spaces/")

    assert response.status_code == 200
    ids = {row["id"] for row in response.json()}
    assert str(own_space.id) in ids
    assert str(reservable_space.id) in ids
    assert str(other_space.id) not in ids
    assert str(maintenance_space.id) not in ids


@pytest.mark.django_db
def test_public_spaces_include_available_and_timed_reservations_only() -> None:
    available = Space.objects.create(
        name="Reservable open room",
        capacity=4,
        status=Space.Status.AVAILABLE,
    )
    timed_reserved = Space.objects.create(
        name="Timed reserved room",
        capacity=6,
        status=Space.Status.RESERVED,
    )
    SpaceBookingRecord.objects.create(
        booking_id=uuid.uuid4(),
        space=timed_reserved,
        company_id=uuid.uuid4(),
        status=SpaceBookingRecord.Status.APPROVED,
        start_time=timezone.now() - timedelta(minutes=15),
        end_time=timezone.now() + timedelta(hours=2),
    )
    stale_reserved = Space.objects.create(
        name="Stale reserved room",
        capacity=6,
        status=Space.Status.RESERVED,
    )
    SpaceBookingRecord.objects.create(
        booking_id=uuid.uuid4(),
        space=stale_reserved,
        company_id=uuid.uuid4(),
        status=SpaceBookingRecord.Status.APPROVED,
        start_time=timezone.now() - timedelta(days=2),
        end_time=timezone.now() - timedelta(days=1),
    )
    Space.objects.create(
        name="Permanent company room",
        capacity=5,
        company_id=uuid.uuid4(),
        status=Space.Status.OCCUPIED,
    )
    Space.objects.create(name="Blocked room", capacity=3, status=Space.Status.BLOCKED)

    response = APIClient().get("/api/public/spaces/")

    assert response.status_code == 200
    ids = {row["id"] for row in response.json()}
    assert str(available.id) in ids
    assert str(timed_reserved.id) in ids
    assert str(stale_reserved.id) not in ids
