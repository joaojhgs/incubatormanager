from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand
from ilb_common.event_bus import subscribe

from core.events import dispatch_booking_event


class Command(BaseCommand):
    help = "Consume booking events and apply equipment assignment state."

    def handle(self, *args, **options):
        if not settings.RABBITMQ_URL:
            self.stdout.write("RABBITMQ_URL not set; no consumer started")
            return
        subscribe(
            settings.RABBITMQ_URL,
            [
                "booking.approved",
                "booking.rejected",
                "booking.cancelled",
                "booking.completed",
            ],
            dispatch_booking_event,
            queue="inventory.booking-events",
            durable_queue=True,
        )
