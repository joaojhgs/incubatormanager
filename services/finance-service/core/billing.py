"""Reusable billing operations for commands and API views."""

from __future__ import annotations

import datetime as dt
from datetime import timedelta
from typing import TypedDict

from django.utils import timezone

from core.models import BillingContract, Payment


class BillingRunResult(TypedDict):
    """Counters from a monthly billing run."""

    created: int
    existing_skipped: int
    inactive_skipped: int
    period_start: str
    period_end: str


def parse_as_of(raw: str | None) -> dt.date:
    """Parse an optional ISO date for billing/overdue management commands."""

    if raw is None or raw == "":
        return timezone.now().date()
    try:
        return dt.date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"invalid --as-of date: {raw}") from exc


def month_start(on_date: dt.date) -> dt.date:
    """Return the first day of the month containing ``on_date``."""

    return on_date.replace(day=1)


def month_end(on_date: dt.date) -> dt.date:
    """Return the last day of the month containing ``on_date``."""

    next_month = (on_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month - timedelta(days=1)


def generate_monthly_billing(*, as_of: dt.date) -> BillingRunResult:
    """Create idempotent monthly contract payments for active billing contracts."""

    period_start = month_start(as_of)
    period_end = month_end(as_of)
    created = 0
    existing_skipped = 0
    inactive_skipped = 0

    for contract in BillingContract.objects.filter(is_active=True):
        if not contract.is_covered(on_date=as_of):
            inactive_skipped += 1
            continue

        _, was_created = Payment.objects.get_or_create(
            contract_id=contract.contract_id,
            source=Payment.Source.CONTRACT,
            period_start=period_start,
            defaults={
                "company_id": contract.company_id,
                "amount": contract.monthly_fee,
                "status": Payment.Status.PENDING,
                "period_end": period_end,
                "due_date": period_end,
                "reference_id": f"contract:{contract.contract_id}:{period_start.isoformat()}",
            },
        )
        if was_created:
            created += 1
        else:
            existing_skipped += 1

    return {
        "created": created,
        "existing_skipped": existing_skipped,
        "inactive_skipped": inactive_skipped,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
    }
