"""Reusable utility helpers for finance service."""

from __future__ import annotations

import os


def rabbitmq_url() -> str:
    """Return the RabbitMQ URL for optional publisher/subscriber operations."""

    return os.environ.get("RABBITMQ_URL", "").strip()
