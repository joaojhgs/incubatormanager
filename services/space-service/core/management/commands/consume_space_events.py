from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand
from ilb_common.event_bus import subscribe

from core.events import dispatch_event


class Command(BaseCommand):
    help = "Consume contract and booking events for space projections."

    def handle(self, *args, **options):
        if not settings.RABBITMQ_URL:
            self.stdout.write("RABBITMQ_URL not set; no consumer started")
            return
        subscribe(
            settings.RABBITMQ_URL,
            ["contract.activated", "contract.terminated", "contract.expired", "booking.approved", "booking.rejected", "booking.cancelled", "booking.completed"],
            dispatch_event,
            queue="space.domain-events",
            durable_queue=True,
        )
