"""Dashboard integration event handlers."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from ilb_common.event_bus import EventEnvelope

from core.models import (
    BookingProjection,
    CompanyProjection,
    ContractProjection,
    EmployeeProjection,
    PaymentProjection,
    ProcessedEvent,
)

SUPPORTED_EVENT_TYPES = (
    "company.created",
    "company.archived",
    "employee.changed",
    "contract.activated",
    "contract.expired",
    "contract.terminated",
    "booking.approved",
    "booking.rejected",
    "booking.cancelled",
    "booking.completed",
    "payment.recorded",
)


def _parse_occurred_at(value: str) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _run_once(envelope: EventEnvelope, handler: Callable[[], None]) -> None:
    """Run handler atomically once per envelope event_id."""

    try:
        with transaction.atomic():
            ProcessedEvent.objects.create(
                event_id=envelope["event_id"],
                event_type=envelope["event_type"],
                occurred_at=_parse_occurred_at(envelope["occurred_at"]),
            )
            handler()
    except IntegrityError:
        if ProcessedEvent.objects.filter(event_id=envelope["event_id"]).exists():
            return
        raise


def _uuid(payload: dict[str, object], key: str, *, required: bool = True) -> UUID | None:
    value = payload.get(key)
    if value in {None, ""}:
        if required:
            raise ValidationError(f"{key} is required")
        return None
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise ValidationError(f"{key} is not a valid UUID") from exc


def _decimal(payload: dict[str, object], key: str, default: str = "0") -> Decimal:
    value = payload.get(key, default)
    if value in {None, ""}:
        value = default
    try:
        return Decimal(str(value))
    except (ValueError, InvalidOperation) as exc:
        raise ValidationError(f"{key} is not a valid decimal") from exc


def _date(payload: dict[str, object], key: str) -> dt.date | None:
    value = payload.get(key)
    if value in {None, ""}:
        return None
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValidationError(f"{key} is not an ISO date") from exc


def _datetime(payload: dict[str, object], key: str) -> dt.datetime | None:
    value = payload.get(key)
    if value in {None, ""}:
        return None
    raw = str(value).replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValidationError(f"{key} is not an ISO datetime") from exc
    if parsed.tzinfo is None:
        return timezone.make_aware(parsed)
    return parsed


def _handle_company_created(envelope: EventEnvelope) -> None:
    payload = envelope["payload"]
    company_id = _uuid(payload, "company_id")
    assert company_id is not None

    def upsert() -> None:
        CompanyProjection.objects.update_or_create(
            company_id=company_id,
            defaults={
                "name": str(payload.get("name") or ""),
                "cae_code": str(payload.get("cae_code") or ""),
                "maturity_stage_name": str(payload.get("maturity_stage_name") or ""),
                "is_active": True,
                "archived_at": None,
            },
        )

    _run_once(envelope, upsert)


def _handle_company_archived(envelope: EventEnvelope) -> None:
    payload = envelope["payload"]
    company_id = _uuid(payload, "company_id")
    assert company_id is not None

    def archive() -> None:
        CompanyProjection.objects.update_or_create(
            company_id=company_id,
            defaults={
                "is_active": False,
                "archived_at": _datetime(payload, "archived_at"),
            },
        )

    _run_once(envelope, archive)


def _handle_employee_changed(envelope: EventEnvelope) -> None:
    payload = envelope["payload"]
    employee_id = _uuid(payload, "employee_id")
    company_id = _uuid(payload, "company_id")
    assert employee_id is not None and company_id is not None
    action = str(payload.get("action") or "updated").lower()

    def upsert() -> None:
        EmployeeProjection.objects.update_or_create(
            employee_id=employee_id,
            defaults={
                "company_id": company_id,
                "employee_type": str(payload.get("employee_type") or ""),
                "is_active": action != "deleted",
            },
        )

    _run_once(envelope, upsert)


def _handle_contract_activated(envelope: EventEnvelope) -> None:
    payload = envelope["payload"]
    contract_id = _uuid(payload, "contract_id")
    company_id = _uuid(payload, "company_id")
    assert contract_id is not None and company_id is not None

    def upsert() -> None:
        ContractProjection.objects.update_or_create(
            contract_id=contract_id,
            defaults={
                "company_id": company_id,
                "space_id": _uuid(payload, "space_id", required=False),
                "area_sqm": _decimal(payload, "area_sqm"),
                "rate_per_sqm": _decimal(payload, "rate_per_sqm"),
                "monthly_fee": _decimal(payload, "monthly_fee"),
                "start_date": _date(payload, "start_date"),
                "end_date": _date(payload, "end_date"),
                "status": "active",
                "is_active": True,
            },
        )

    _run_once(envelope, upsert)


def _handle_contract_inactive(envelope: EventEnvelope) -> None:
    payload = envelope["payload"]
    contract_id = _uuid(payload, "contract_id")
    assert contract_id is not None
    status = "terminated" if envelope["event_type"] == "contract.terminated" else "expired"

    def mark_inactive() -> None:
        defaults = {"status": status, "is_active": False}
        company_id = _uuid(payload, "company_id", required=False)
        space_id = _uuid(payload, "space_id", required=False)
        if company_id:
            defaults["company_id"] = company_id
        if space_id:
            defaults["space_id"] = space_id
        ContractProjection.objects.update_or_create(contract_id=contract_id, defaults=defaults)

    _run_once(envelope, mark_inactive)


def _handle_booking_event(envelope: EventEnvelope) -> None:
    payload = envelope["payload"]
    booking_id = _uuid(payload, "booking_id")
    assert booking_id is not None
    status = envelope["event_type"].removeprefix("booking.")

    def upsert() -> None:
        BookingProjection.objects.update_or_create(
            booking_id=booking_id,
            defaults={
                "company_id": _uuid(payload, "company_id", required=False),
                "space_id": _uuid(payload, "space_id", required=False),
                "status": status,
                "quoted_price": _decimal(payload, "quoted_price"),
                "start_time": _datetime(payload, "start_time"),
                "end_time": _datetime(payload, "end_time"),
            },
        )

    _run_once(envelope, upsert)


def _handle_payment_recorded(envelope: EventEnvelope) -> None:
    payload = envelope["payload"]
    payment_id = _uuid(payload, "payment_id")
    assert payment_id is not None
    paid_at = _datetime(payload, "paid_at")
    if paid_at is None:
        raise ValidationError("paid_at is required")

    def upsert() -> None:
        PaymentProjection.objects.update_or_create(
            payment_id=payment_id,
            defaults={
                "company_id": _uuid(payload, "company_id", required=False),
                "contract_id": _uuid(payload, "contract_id", required=False),
                "booking_id": _uuid(payload, "booking_id", required=False),
                "amount": _decimal(payload, "amount"),
                "paid_at": paid_at,
            },
        )

    _run_once(envelope, upsert)


def handle_event(envelope: EventEnvelope) -> None:
    """Dispatch one supported dashboard event envelope."""

    event_type = envelope["event_type"]
    if event_type == "company.created":
        _handle_company_created(envelope)
    elif event_type == "company.archived":
        _handle_company_archived(envelope)
    elif event_type == "employee.changed":
        _handle_employee_changed(envelope)
    elif event_type == "contract.activated":
        _handle_contract_activated(envelope)
    elif event_type in {"contract.expired", "contract.terminated"}:
        _handle_contract_inactive(envelope)
    elif event_type in {
        "booking.approved",
        "booking.rejected",
        "booking.cancelled",
        "booking.completed",
    }:
        _handle_booking_event(envelope)
    elif event_type == "payment.recorded":
        _handle_payment_recorded(envelope)
    else:
        raise ValueError(f"unsupported event type: {event_type}")
