"""State transitions and event publishing for booking lifecycle."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from ilb_common.event_bus import EventEnvelope, publish

from core.models import Booking, ProcessedEvent


def _mark_processed(envelope: EventEnvelope) -> bool:
    try:
        ProcessedEvent.objects.create(
            event_id=UUID(envelope["event_id"]),
            event_type=envelope["event_type"],
        )
    except IntegrityError:
        return False
    return True


def booking_payload(booking: Booking) -> dict[str, str | None]:
    return {
        "booking_id": str(booking.id),
        "company_id": str(booking.company_id),
        "space_id": str(booking.space_id),
        "start_time": booking.start_time.isoformat(),
        "end_time": booking.end_time.isoformat(),
        "quoted_price": str(booking.quoted_price),
        "equipment_ids": booking.equipment_ids,
    }


def _publish_booking_event(event_type: str, booking: Booking) -> None:
    if not settings.RABBITMQ_URL:
        return
    transaction.on_commit(
        lambda: publish(settings.RABBITMQ_URL, event_type, booking_payload(booking), routing_key=event_type)
    )


def _assert_can_transition(from_status: str, to_status: str) -> None:
    if from_status == to_status:
        return
    matrix = {
        Booking.Status.PENDING: {Booking.Status.APPROVED, Booking.Status.REJECTED, Booking.Status.CANCELLED},
        Booking.Status.APPROVED: {Booking.Status.COMPLETED, Booking.Status.CANCELLED},
        Booking.Status.REJECTED: set(),
        Booking.Status.CANCELLED: set(),
        Booking.Status.COMPLETED: set(),
    }
    if to_status not in matrix.get(from_status, set()):
        raise ValidationError("Invalid booking status transition")


def set_status(booking: Booking, target: str) -> None:
    _assert_can_transition(booking.status, target)
    if booking.status == target:
        return
    booking.status = target
    booking.save(update_fields=["status", "updated_at"])
    _publish_booking_event(f"booking.{target.lower()}", booking)


def parse_booking_ids(event_ids: list[str]) -> list[UUID]:
    return [UUID(v) for v in event_ids]


def scope_bookings(request_user: object):
    role = getattr(request_user, "role", None)
    if role in {"Staff", "Director"}:
        return Booking.objects.all()
    if role == "Client":
        company_id = getattr(request_user, "company_id", None)
        if company_id is None:
            return Booking.objects.none()
        return Booking.objects.filter(company_id=company_id)
    return Booking.objects.none()


def complete_expired_if_any() -> int:
    now = timezone.now()
    to_complete = Booking.objects.filter(status=Booking.Status.APPROVED, end_time__lte=now)
    count = 0
    for booking in to_complete:
        try:
            set_status(booking, Booking.Status.COMPLETED)
            count += 1
        except ValidationError:
            continue
    return count
