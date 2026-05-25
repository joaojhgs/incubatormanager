from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.events import publish_contract_expired
from core.models import Contract


class Command(BaseCommand):
    help = "Expire active contracts whose end date is in the past."

    def handle(self, *args: object, **options: object) -> None:
        today = timezone.localdate()
        queryset = Contract.objects.filter(status=Contract.Status.ACTIVE, end_date__lte=today)

        expired_count = 0
        for contract in queryset:
            contract.expire()
            publish_contract_expired(contract)
            expired_count += 1

        if expired_count:
            self.stdout.write(self.style.SUCCESS(f"Expired {expired_count} contract(s)."))
        else:
            self.stdout.write(self.style.WARNING("No contracts to expire."))
