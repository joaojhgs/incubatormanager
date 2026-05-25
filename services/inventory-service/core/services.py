"""Inventory event handlers for booking lifecycle projection."""

from __future__ import annotations

from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from ilb_common.event_bus import EventEnvelope

from core.models import Equipment, EquipmentAssignment, ProcessedEvent


def _set_equipment_status(equipment: Equipment, status: str) -> None:
    if equipment.status != status:
        equipment.status = status
        equipment.save(update_fields=["status", "updated_at"])


def _apply_booking_event_changes(envelope: EventEnvelope) -> None:
    event_type = envelope["event_type"]
    payload = envelope["payload"]
    booking_id = UUID(payload["booking_id"])
    equipment_ids = payload.get("equipment_ids", []) or []
    assigned_space_id = payload.get("space_id")

    for raw_id in equipment_ids:
        try:
            equipment = Equipment.objects.get(pk=raw_id)
        except ObjectDoesNotExist:
            continue

        if event_type == "booking.approved":
            company_id = UUID(payload["company_id"])
            _, _ = EquipmentAssignment.objects.update_or_create(
                equipment=equipment,
                booking_id=booking_id,
                defaults={
                    "company_id": company_id,
                    "assigned_space_id": UUID(str(assigned_space_id))
                    if assigned_space_id
                    else None,
                    "status": EquipmentAssignment.Status.ASSIGNED,
                },
            )
            if assigned_space_id:
                equipment.assigned_space_id = UUID(str(assigned_space_id))
                equipment.save(update_fields=["assigned_space_id", "updated_at"])
            _set_equipment_status(equipment, Equipment.Status.IN_USE)
            continue

        # For terminal booking states, mark released.
        released_assignments = EquipmentAssignment.objects.filter(
            equipment=equipment,
            booking_id=booking_id,
            status=EquipmentAssignment.Status.ASSIGNED,
        )
        released_space_ids = {
            assignment.assigned_space_id
            for assignment in released_assignments
            if assignment.assigned_space_id is not None
        }
        released_assignments.update(status=EquipmentAssignment.Status.RELEASED)
        remaining_assignments = EquipmentAssignment.objects.filter(
            equipment=equipment,
            status=EquipmentAssignment.Status.ASSIGNED,
        )
        if equipment.assigned_space_id in released_space_ids and not remaining_assignments.exists():
            equipment.assigned_space_id = None
            equipment.save(update_fields=["assigned_space_id", "updated_at"])
        if not remaining_assignments.exists():
            _set_equipment_status(equipment, Equipment.Status.AVAILABLE)


def apply_booking_event(envelope: EventEnvelope) -> None:
    try:
        with transaction.atomic():
            ProcessedEvent.objects.create(
                event_id=UUID(envelope["event_id"]),
                event_type=envelope["event_type"],
            )
            _apply_booking_event_changes(envelope)
    except IntegrityError:
        if ProcessedEvent.objects.filter(event_id=UUID(envelope["event_id"])).exists():
            return
        raise


def dispatch_event(envelope: EventEnvelope) -> None:
    if envelope["event_type"] in {
        "booking.approved",
        "booking.rejected",
        "booking.cancelled",
        "booking.completed",
    }:
        apply_booking_event(envelope)
