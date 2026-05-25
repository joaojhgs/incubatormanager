"""Create recurring contract monthly payment rows."""

from __future__ import annotations

import datetime as dt
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import BillingContract, Payment


def _to_date(raw: str | None) -> dt.date:
    if raw is None:
        return timezone.now().date()
    try:
        return dt.date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"invalid --as-of date: {raw}") from exc


def _month_start(on_date: dt.date) -> dt.date:
    return on_date.replace(day=1)


def _month_end(on_date: dt.date) -> dt.date:
    next_month = (on_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month - timedelta(days=1)


class Command(BaseCommand):
    help = "Generate monthly contract invoices for active billing contracts."

    def add_arguments(self, parser) -> None:  # type: ignore[override]
        parser.add_argument(
            "--as-of",
            default=None,
            help="ISO date used for the monthly period (defaults to today).",
        )

    def handle(self, *args: object, **options: object) -> None:
        as_of = _to_date(options["as_of"])
        period_start = _month_start(as_of)
        period_end = _month_end(as_of)

        created = 0
        skipped = 0
        for contract in BillingContract.objects.filter(is_active=True):
            if not contract.is_covered(on_date=as_of):
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
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"generate_monthly_billing: created={created} existing_skipped={skipped}"
            )
        )
