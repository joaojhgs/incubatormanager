"""Mark past-due pending payments as overdue."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Payment


class Command(BaseCommand):
    help = "Mark all pending payments with due date before today as overdue."

    def add_arguments(self, parser) -> None:  # type: ignore[override]
        parser.add_argument(
            "--as-of",
            default=None,
            help="ISO date for evaluating overdue payments (defaults to today).",
        )

    def handle(self, *args: object, **options: object) -> None:
        as_of = options["as_of"]
        today = timezone.datetime.fromisoformat(as_of).date() if as_of else timezone.now().date()
        count = Payment.objects.filter(
            status=Payment.Status.PENDING,
            due_date__lt=today,
        ).update(status=Payment.Status.OVERDUE)
        self.stdout.write(
            self.style.SUCCESS(f"mark_overdue_payments: updated={count}")
        )
