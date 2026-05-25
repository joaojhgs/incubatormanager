"""Inventory event bus integration."""

from __future__ import annotations

from ilb_common.event_bus import EventEnvelope

from core.services import dispatch_event


def dispatch_booking_event(envelope: EventEnvelope) -> None:
    dispatch_event(envelope)
