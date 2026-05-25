"""Inventory CRUD, assignment, and booking event tests."""

from __future__ import annotations

import uuid

import pytest
from core.models import Equipment, EquipmentAssignment, EquipmentType, ProcessedEvent
from core.services import apply_booking_event
from rest_framework.test import APIClient


def _client(role: str = "Staff", company_id: uuid.UUID | None = None) -> APIClient:
    client = APIClient()
    headers = {"HTTP_X_USER_ID": str(uuid.uuid4()), "HTTP_X_USER_ROLE": role}
    if company_id is not None:
        headers["HTTP_X_COMPANY_ID"] = str(company_id)
    client.credentials(**headers)
    return client


@pytest.mark.django_db
def test_equipment_crud_assign_release_and_client_assignment_scope() -> None:
    company_id = uuid.uuid4()
    type_response = _client().post(
        "/api/inventory/equipment-types/", data={"name": "Projector"}, format="json"
    )
    assert type_response.status_code == 201
    equipment_response = _client().post(
        "/api/inventory/equipment/",
        data={
            "name": "Projector A",
            "equipment_type": type_response.json()["id"],
            "assigned_space_id": str(uuid.uuid4()),
            "rental_cost": "15.50",
        },
        format="json",
    )
    assert equipment_response.status_code == 201
    equipment_id = equipment_response.json()["id"]
    booking_id = uuid.uuid4()
    assigned_space_id = uuid.uuid4()

    assign = _client().post(
        f"/api/inventory/equipment/{equipment_id}/assign/",
        data={
            "booking_id": str(booking_id),
            "company_id": str(company_id),
            "assigned_space_id": str(assigned_space_id),
        },
        format="json",
    )
    assert assign.status_code == 200
    assert assign.json()["status"] == Equipment.Status.IN_USE
    assert assign.json()["assigned_space_id"] == str(assigned_space_id)
    assert assign.json()["rental_cost"] == "15.50"
    assert _client("Client", uuid.uuid4()).get("/api/inventory/my-assignments/").json() == []
    assert len(_client("Client", company_id).get("/api/inventory/my-assignments/").json()) == 1

    release = _client().post(
        f"/api/inventory/equipment/{equipment_id}/release/",
        data={"booking_id": str(booking_id)},
        format="json",
    )
    assert release.status_code == 200
    assert release.json()["status"] == Equipment.Status.AVAILABLE


@pytest.mark.django_db
def test_booking_event_assigns_equipment_once_then_releases() -> None:
    equipment_type = EquipmentType.objects.create(name="Desk")
    equipment = Equipment.objects.create(name="Desk 1", equipment_type=equipment_type)
    booking_id = uuid.uuid4()
    company_id = uuid.uuid4()
    space_id = uuid.uuid4()
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "booking.approved",
        "occurred_at": "",
        "payload": {
            "booking_id": str(booking_id),
            "company_id": str(company_id),
            "space_id": str(space_id),
            "equipment_ids": [str(equipment.id)],
        },
    }
    apply_booking_event(event)  # type: ignore[arg-type]
    apply_booking_event(event)  # type: ignore[arg-type]
    equipment.refresh_from_db()
    assert equipment.status == Equipment.Status.IN_USE
    assert equipment.assigned_space_id == space_id
    assert EquipmentAssignment.objects.count() == 1
    assert EquipmentAssignment.objects.get().assigned_space_id == space_id
    assert ProcessedEvent.objects.count() == 1

    event = {**event, "event_id": str(uuid.uuid4()), "event_type": "booking.completed"}
    apply_booking_event(event)  # type: ignore[arg-type]
    equipment.refresh_from_db()
    assert equipment.status == Equipment.Status.AVAILABLE
    assert equipment.assigned_space_id is None
    assert EquipmentAssignment.objects.get().status == EquipmentAssignment.Status.RELEASED

    rejected_event = {
        **event,
        "event_id": str(uuid.uuid4()),
        "event_type": "booking.rejected",
        "payload": {
            "booking_id": str(uuid.uuid4()),
            "company_id": None,
            "equipment_ids": [str(equipment.id)],
        },
    }
    apply_booking_event(rejected_event)  # type: ignore[arg-type]
    equipment.refresh_from_db()
    assert equipment.status == Equipment.Status.AVAILABLE

@pytest.mark.django_db
def test_booking_event_rolls_back_processed_marker_when_assignment_fails(monkeypatch) -> None:
    equipment_type = EquipmentType.objects.create(name="Monitor")
    equipment = Equipment.objects.create(name="Monitor 1", equipment_type=equipment_type)
    booking_id = uuid.uuid4()
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "booking.approved",
        "occurred_at": "",
        "payload": {
            "booking_id": str(booking_id),
            "company_id": str(uuid.uuid4()),
            "space_id": str(uuid.uuid4()),
            "equipment_ids": [str(equipment.id)],
        },
    }

    def fail_assignment(*args: object, **kwargs: object) -> None:
        raise RuntimeError("assignment failed")

    monkeypatch.setattr(EquipmentAssignment.objects, "update_or_create", fail_assignment)

    with pytest.raises(RuntimeError, match="assignment failed"):
        apply_booking_event(event)  # type: ignore[arg-type]

    equipment.refresh_from_db()
    assert equipment.status == Equipment.Status.AVAILABLE
    assert equipment.assigned_space_id is None
    assert EquipmentAssignment.objects.count() == 0
    assert ProcessedEvent.objects.count() == 0
