"""Space event command wiring."""

from __future__ import annotations

from ilb_common.event_bus import EventEnvelope

from core.services import consume_event


def dispatch_event(envelope: EventEnvelope) -> None:
    consume_event(envelope)
