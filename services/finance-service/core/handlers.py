"""Event handlers for finance-service integration messages."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.core.exceptions import ValidationError
from ilb_common import event_bus
from ilb_common.event_bus import EventEnvelope

from core.models import BillingContract, Payment, ProcessedEvent
from core.utils import rabbitmq_url


def _already_processed(event: EventEnvelope) -> bool:
    """Return True when a processing attempt has already handled the event."""

    if ProcessedEvent.objects.filter(event_id=event["event_id"]).exists():
        return True

    return False


def _mark_processed(event: EventEnvelope) -> None:
    ProcessedEvent.objects.create(event_id=event["event_id"], event_type=event["event_type"])


def _to_uuid(payload: dict[str, object], key: str) -> UUID:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValidationError(f"{key} must be a string UUID")
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValidationError(f"{key} is not a valid UUID") from exc


def _to_decimal(payload: dict[str, object], key: str) -> Decimal:
    value = payload.get(key)
    if value is None:
        raise ValidationError(f"{key} is required")
    if isinstance(value, int | float):
        try:
            return Decimal(str(value))
        except (ValueError, InvalidOperation) as exc:
            raise ValidationError(f"{key} is not a valid decimal") from exc
    if isinstance(value, str):
        try:
            return Decimal(value)
        except (ValueError, InvalidOperation) as exc:
            raise ValidationError(f"{key} is not a valid decimal") from exc
    raise ValidationError(f"{key} is not a valid number")


def _to_date(payload: dict[str, object], key: str) -> dt.date:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValidationError(f"{key} must be an ISO date string")
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{key} is not an ISO date") from exc


def _parse_end_date(payload: dict[str, object]) -> dt.date | None:
    raw_end_date = payload.get("end_date")
    if raw_end_date is None or raw_end_date == "":
        return None

    if isinstance(raw_end_date, str):
        try:
            return dt.date.fromisoformat(raw_end_date)
        except ValueError as exc:
            raise ValidationError("end_date is not an ISO date") from exc

    raise ValidationError("end_date must be an ISO date string")


def handle_contract_activated(event: EventEnvelope) -> None:
    """Upsert a BillingContract row from a ``contract.activated`` envelope."""

    payload = event["payload"]
    contract_id = _to_uuid(payload, "contract_id")
    company_id = _to_uuid(payload, "company_id")
    space_id = _to_uuid(payload, "space_id")
    area_sqm = _to_decimal(payload, "area_sqm")
    rate_per_sqm = _to_decimal(payload, "rate_per_sqm")
    monthly_fee = _to_decimal(payload, "monthly_fee")
    start_date = _to_date(payload, "start_date")
    end_date = _parse_end_date(payload)

    if _already_processed(event):
        return

    BillingContract.objects.update_or_create(
        contract_id=contract_id,
        defaults={
            "company_id": company_id,
            "space_id": space_id,
            "area_sqm": area_sqm,
            "rate_per_sqm": rate_per_sqm,
            "monthly_fee": monthly_fee,
            "start_date": start_date,
            "end_date": end_date,
            "is_active": True,
        },
    )
    _mark_processed(event)


def handle_booking_approved(event: EventEnvelope) -> None:
    """Create a payable booking payment from a ``booking.approved`` envelope."""

    payload = event["payload"]
    booking_id = _to_uuid(payload, "booking_id")
    company_id = _to_uuid(payload, "company_id")
    amount = _to_decimal(payload, "quoted_price")

    due_date_value = payload.get("start_time")
    if isinstance(due_date_value, str):
        try:
            due_date = dt.datetime.fromisoformat(due_date_value).date()
        except ValueError:
            due_date = None
    else:
        due_date = None

    if _already_processed(event):
        return

    Payment.objects.create(
        company_id=company_id,
        booking_id=booking_id,
        source=Payment.Source.BOOKING,
        amount=amount,
        due_date=due_date,
        reference_id="booking-approval",
        status=Payment.Status.PENDING,
    )
    _mark_processed(event)


def handle_event(event: EventEnvelope) -> None:
    """Route incoming event to an individual handler by type."""

    event_type = event["event_type"]
    if event_type == "contract.activated":
        handle_contract_activated(event)
    elif event_type == "booking.approved":
        handle_booking_approved(event)
    else:
        raise ValueError(f"unsupported event type: {event_type}")


def maybe_handle_event(event: EventEnvelope) -> None:
    """Public entrypoint for command/consumer callers."""

    handle_event(event)


def publish_payment_recorded(
    *,
    payment_id: UUID,
    amount: Decimal,
    company_id: UUID,
    contract_id: UUID | None,
    booking_id: UUID | None,
    paid_at: dt.datetime,
) -> None:
    """Publish ``payment.recorded`` with a canonical payload."""

    rabbit_url = rabbitmq_url()
    if not rabbit_url:
        return

    payload = {
        "payment_id": str(payment_id),
        "company_id": str(company_id),
        "contract_id": str(contract_id) if contract_id else None,
        "booking_id": str(booking_id) if booking_id else None,
        "amount": str(amount),
        "paid_at": paid_at.isoformat(),
    }
    event_bus.publish(rabbit_url, "payment.recorded", payload)
