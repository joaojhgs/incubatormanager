"""Inventory event handlers for booking lifecycle projection."""

from __future__ import annotations

from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction

from ilb_common.event_bus import EventEnvelope

from core.models import Equipment, EquipmentAssignment, ProcessedEvent


def _mark_processed(envelope: EventEnvelope) -> bool:
    try:
        with transaction.atomic():
            ProcessedEvent.objects.create(
                event_id=UUID(envelope["event_id"]),
                event_type=envelope["event_type"],
            )
    except IntegrityError:
        return False
    return True


def _set_equipment_status(equipment: Equipment, status: str) -> None:
    if equipment.status != status:
        equipment.status = status
        equipment.save(update_fields=["status", "updated_at"])


def apply_booking_event(envelope: EventEnvelope) -> None:
    if not _mark_processed(envelope):
        return

    event_type = envelope["event_type"]
    payload = envelope["payload"]
    booking_id = UUID(payload["booking_id"])
    company_id = UUID(payload["company_id"])
    equipment_ids = payload.get("equipment_ids", []) or []

    for raw_id in equipment_ids:
        try:
            equipment = Equipment.objects.get(pk=raw_id)
        except ObjectDoesNotExist:
            continue

        if event_type == "booking.approved":
            _, _ = EquipmentAssignment.objects.update_or_create(
                equipment=equipment,
                booking_id=booking_id,
                defaults={
                    "company_id": company_id,
                    "status": EquipmentAssignment.Status.ASSIGNED,
                },
            )
            _set_equipment_status(equipment, Equipment.Status.IN_USE)
            continue

        # For terminal booking states, mark released.
        EquipmentAssignment.objects.filter(
            equipment=equipment,
            booking_id=booking_id,
            status=EquipmentAssignment.Status.ASSIGNED,
        ).update(status=EquipmentAssignment.Status.RELEASED)
        _set_equipment_status(equipment, Equipment.Status.AVAILABLE)


def dispatch_event(envelope: EventEnvelope) -> None:
    if envelope["event_type"] in {
        "booking.approved",
        "booking.rejected",
        "booking.cancelled",
        "booking.completed",
    }:
        apply_booking_event(envelope)
