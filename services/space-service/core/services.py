"""Domain helpers and event handlers for space service."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.utils import timezone
from ilb_common.event_bus import EventEnvelope

from core.models import ProcessedEvent, Space, SpaceBookingRecord, SpaceContract


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


def _parse_decimal(value: object) -> Decimal:
    if value in {None, ""}:
        return Decimal("0")
    return Decimal(str(value))


def occupancy_for_space(space: Space) -> dict[str, int | float]:
    now = timezone.now()
    active = SpaceBookingRecord.objects.filter(
        space=space,
        status=SpaceBookingRecord.Status.APPROVED,
        start_time__isnull=False,
        end_time__isnull=False,
        start_time__lte=now,
        end_time__gt=now,
    )
    occupied = active.count()
    capacity = max(space.capacity, 0)
    occupancy = 0.0
    if capacity:
        occupancy = (occupied / capacity) * 100

    return {
        "space_id": str(space.id),
        "space_name": space.name,
        "capacity": capacity,
        "occupied": occupied,
        "occupancy_percent": round(occupancy, 2),
    }


def apply_contract_event(envelope: EventEnvelope) -> None:
    if not _mark_processed(envelope):
        return

    event_type = envelope["event_type"]
    payload = envelope["payload"]
    space_id = UUID(payload["space_id"])
    contract_id = UUID(payload["contract_id"])
    company_id = UUID(payload["company_id"])

    try:
        space = Space.objects.get(pk=space_id)
    except ObjectDoesNotExist:
        return

    if event_type == "contract.activated":
        defaults = {
            "company_id": company_id,
            "space": space,
            "area_sqm": _parse_decimal(payload["area_sqm"]),
            "rate_per_sqm": _parse_decimal(payload["rate_per_sqm"]),
            "monthly_fee": _parse_decimal(payload["monthly_fee"]),
            "start_date": payload["start_date"],
            "end_date": payload["end_date"],
        }
        SpaceContract.objects.update_or_create(
            contract_id=contract_id,
            defaults={**defaults, "status": SpaceContract.Status.ACTIVE},
        )
        space.status = Space.Status.AVAILABLE
        space.save(update_fields=["status", "updated_at"])
        return

    status = (
        SpaceContract.Status.TERMINATED
        if event_type == "contract.terminated"
        else SpaceContract.Status.EXPIRED
    )
    contract = SpaceContract.objects.filter(contract_id=contract_id).first()
    if contract is None:
        # Minimal contract.expired events can arrive after missed/replayed history.
        # Mark them processed without inventing a projection from incomplete data.
        return

    contract.company_id = company_id
    contract.space = space
    contract.status = status
    if event_type == "contract.terminated":
        contract.termination_reason = str(payload.get("reason", ""))
    contract.save(
        update_fields=[
            "company_id",
            "space",
            "status",
            "termination_reason",
            "updated_at",
        ]
    )

    if status in {SpaceContract.Status.EXPIRED, SpaceContract.Status.TERMINATED}:
        space.status = Space.Status.MAINTENANCE
        space.save(update_fields=["status", "updated_at"])


def apply_booking_event_dict(envelope: EventEnvelope) -> None:
    if not _mark_processed(envelope):
        return

    event_type = envelope["event_type"]
    payload = envelope["payload"]
    booking_id = UUID(payload["booking_id"])
    space_id = UUID(payload["space_id"])
    company_id = UUID(payload["company_id"])

    try:
        space = Space.objects.get(pk=space_id)
    except ObjectDoesNotExist:
        return

    if event_type == "booking.approved":
        SpaceBookingRecord.objects.update_or_create(
            booking_id=booking_id,
            defaults={
                "space": space,
                "company_id": company_id,
                "status": SpaceBookingRecord.Status.APPROVED,
                "start_time": payload.get("start_time"),
                "end_time": payload.get("end_time"),
                "quoted_price": _parse_decimal(payload.get("quoted_price")),
                "equipment_ids": payload.get("equipment_ids") or [],
            },
        )
        return

    status = (
        SpaceBookingRecord.Status.CANCELLED
        if event_type == "booking.cancelled"
        else SpaceBookingRecord.Status.COMPLETED
        if event_type == "booking.completed"
        else SpaceBookingRecord.Status.REJECTED
    )

    SpaceBookingRecord.objects.filter(booking_id=booking_id).update(
        status=status,
        space=space,
        company_id=company_id,
    )


def consume_event(envelope: EventEnvelope) -> None:
    if envelope["event_type"] in {
        "contract.activated",
        "contract.expired",
        "contract.terminated",
    }:
        apply_contract_event(envelope)
        return

    if envelope["event_type"] in {
        "booking.approved",
        "booking.rejected",
        "booking.cancelled",
        "booking.completed",
    }:
        apply_booking_event_dict(envelope)
