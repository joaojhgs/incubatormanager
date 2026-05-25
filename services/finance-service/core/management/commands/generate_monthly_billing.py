"""Create recurring contract monthly payment rows."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from core.billing import generate_monthly_billing, month_end, month_start, parse_as_of

# Backwards-compatible helpers used by tests.
_to_date = parse_as_of
_month_start = month_start
_month_end = month_end


class Command(BaseCommand):
    help = "Generate monthly contract invoices for active billing contracts."

    def add_arguments(self, parser) -> None:  # type: ignore[override]
        parser.add_argument(
            "--as-of",
            default=None,
            help="ISO date used for the monthly period (defaults to today).",
        )

    def handle(self, *args: object, **options: object) -> None:
        result = generate_monthly_billing(as_of=parse_as_of(options["as_of"]))
        self.stdout.write(
            self.style.SUCCESS(
                "generate_monthly_billing: "
                f"created={result['created']} "
                f"existing_skipped={result['existing_skipped']}"
            )
        )
