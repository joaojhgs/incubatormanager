"""Consume finance-related events from RabbitMQ."""

from __future__ import annotations

import os

from django.core.management.base import BaseCommand, CommandError
from ilb_common import event_bus

from core.handlers import handle_event

DEFAULT_ROUTING_KEYS = [
    "contract.activated",
    "contract.expired",
    "contract.terminated",
    "booking.approved",
]


class Command(BaseCommand):
    help = "Consume contract/booking events required by finance service."

    def add_arguments(self, parser) -> None:  # type: ignore[override]
        parser.add_argument(
            "--rabbitmq-url",
            default=os.environ.get("RABBITMQ_URL", ""),
            help="AMQP connection URL (defaults to RABBITMQ_URL env).",
        )
        parser.add_argument(
            "--queue",
            default="finance.contract-events",
            help="Queue name to consume messages.",
        )
        parser.add_argument(
            "--routing-key",
            action="append",
            default=DEFAULT_ROUTING_KEYS,
            help="Repeated routing key for finance event bindings.",
        )

    def handle(self, *args: object, **options: object) -> None:
        rabbitmq_url = str(options["rabbitmq_url"]).strip()
        if not rabbitmq_url:
            raise CommandError("RABBITMQ_URL is required for event consumption")

        routing_keys = list(options["routing_key"])
        if not routing_keys:
            routing_keys = DEFAULT_ROUTING_KEYS

        event_bus.subscribe(
            rabbitmq_url,
            routing_keys,
            handle_event,
            queue=str(options["queue"]),
            durable_queue=True,
        )
        # subscribe blocks forever; reaching this line means the consumer stopped.
        self.stdout.write(self.style.SUCCESS("finance event consumer stopped"))
