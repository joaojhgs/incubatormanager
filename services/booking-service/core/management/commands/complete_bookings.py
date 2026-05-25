from __future__ import annotations

from django.core.management.base import BaseCommand

from core.services import complete_expired_if_any


class Command(BaseCommand):
    help = "Complete all approved bookings whose end_time has passed."

    def handle(self, *args, **options):
        count = complete_expired_if_any()
        self.stdout.write(self.style.SUCCESS(f"completed={count}"))
