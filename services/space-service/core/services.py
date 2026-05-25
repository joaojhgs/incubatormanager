"""Domain helpers and event handlers for space service."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.utils import timezone
from ilb_common.event_bus import EventEnvelope

from core.models import ProcessedEvent, Space, SpaceBookingRecord, SpaceContract


def _run_once(envelope: EventEnvelope, handler: Callable[[], None]) -> None:
    try:
        with transaction.atomic():
            ProcessedEvent.objects.create(
                event_id=UUID(envelope["event_id"]),
                event_type=envelope["event_type"],
            )
            handler()
    except IntegrityError:
        if ProcessedEvent.objects.filter(event_id=UUID(envelope["event_id"])).exists():
            return
        raise


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
    event_type = envelope["event_type"]
    payload = envelope["payload"]
    contract_id = UUID(payload["contract_id"])

    if event_type == "contract.activated":
        space_id = UUID(payload["space_id"])
        company_id = UUID(payload["company_id"])
        try:
            space = Space.objects.get(pk=space_id)
        except ObjectDoesNotExist:
            return

        def activate_contract() -> None:
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

        _run_once(envelope, activate_contract)
        return

    status = (
        SpaceContract.Status.TERMINATED
        if event_type == "contract.terminated"
        else SpaceContract.Status.EXPIRED
    )

    def close_contract() -> None:
        contract = SpaceContract.objects.filter(contract_id=contract_id).first()
        if contract is None:
            # Minimal inactive events can arrive after missed/replayed history.
            # Treat the event as consumed without inventing an incomplete projection.
            return

        space = contract.space
        company_id = payload.get("company_id")
        space_id = payload.get("space_id")
        if company_id:
            contract.company_id = UUID(str(company_id))
        if space_id:
            space = Space.objects.get(pk=UUID(str(space_id)))
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
        space.status = Space.Status.MAINTENANCE
        space.save(update_fields=["status", "updated_at"])

    _run_once(envelope, close_contract)


def apply_booking_event_dict(envelope: EventEnvelope) -> None:
    event_type = envelope["event_type"]
    payload = envelope["payload"]
    booking_id = UUID(payload["booking_id"])
    space_id = UUID(payload["space_id"])
    company_id = UUID(payload["company_id"])

    try:
        space = Space.objects.get(pk=space_id)
    except ObjectDoesNotExist:
        return

    def apply_booking() -> None:
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

    _run_once(envelope, apply_booking)

        if updated == 0:
            # If a record was not present (late-arriving event), create one for auditability.
            # No time window is available for historical events with no approval payload.
            SpaceBookingRecord.objects.create(
                space=space,
                booking_id=payload.booking_id,
                company_id=payload.company_id,
                state=state,
                start_time=now(),
                end_time=now(),
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
