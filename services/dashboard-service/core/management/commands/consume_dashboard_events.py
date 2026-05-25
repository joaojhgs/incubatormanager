"""Consume dashboard projection events from RabbitMQ."""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand
from ilb_common.event_bus import subscribe

from core.handlers import SUPPORTED_EVENT_TYPES, handle_event


class Command(BaseCommand):
    help = "Consume domain events and update dashboard materialized projections."

    def handle(self, *args: object, **options: object) -> None:
        if not settings.RABBITMQ_URL:
            self.stdout.write("RABBITMQ_URL not set; no dashboard consumer started")
            return
        subscribe(
            settings.RABBITMQ_URL,
            SUPPORTED_EVENT_TYPES,
            handle_event,
            queue="dashboard.domain-events",
            durable_queue=True,
        )
