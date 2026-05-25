"""Unit tests for idempotent `incubator.events` topic exchange bootstrap."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from ilb_common.event_bus import (
    DEAD_LETTER_EXCHANGE_DEFAULT,
    EXCHANGE_DEFAULT,
    ensure_dead_letter_queue,
    ensure_event_exchange,
    publish,
    subscribe,
)


def test_ensure_event_exchange_uses_topic_durable() -> None:
    ch = MagicMock()
    ensure_event_exchange(ch, exchange=EXCHANGE_DEFAULT)
    ch.exchange_declare.assert_called_once_with(
        exchange=EXCHANGE_DEFAULT,
        exchange_type="topic",
        durable=True,
    )


def test_ensure_event_exchange_idempotent() -> None:
    """Re-declare with the same args is the normal AMQP idempotent pattern."""
    ch = MagicMock()
    ensure_event_exchange(ch)
    ensure_event_exchange(ch)
    assert ch.exchange_declare.call_count == 2
    for call in ch.exchange_declare.call_args_list:
        assert call == (
            (),
            {
                "exchange": EXCHANGE_DEFAULT,
                "exchange_type": "topic",
                "durable": True,
            },
        )


@patch("ilb_common.event_bus.pika.BlockingConnection")
def test_subscribe_ensures_event_exchange_on_startup(mock_bc: MagicMock) -> None:
    """Consumer path must declare the exchange before queues and consumption."""
    mock_channel = MagicMock()
    # Non-blocking: real Pika blocks here until cancelled.
    mock_channel.start_consuming = MagicMock(return_value=None)
    mock_conn = MagicMock()
    mock_conn.channel.return_value = mock_channel
    mock_conn.is_open = True
    mock_bc.return_value = mock_conn

    subscribe(
        "amqp://guest:guest@localhost:5672/",
        ["evt.#"],
        lambda _e: None,
        queue="q-test",
    )

    mock_channel.exchange_declare.assert_called_once_with(
        exchange=EXCHANGE_DEFAULT,
        exchange_type="topic",
        durable=True,
    )
    main_queue_declare = mock_channel.queue_declare.call_args_list[-1]
    assert main_queue_declare.kwargs["queue"] == "q-test"
    assert main_queue_declare.kwargs["arguments"] is None
    mock_channel.basic_consume.assert_called_once()


@patch("ilb_common.event_bus.pika.BlockingConnection")
def test_publish_delegates_to_ensure_path(mock_bc: MagicMock) -> None:
    mock_channel = MagicMock()
    mock_conn = MagicMock()
    mock_conn.channel.return_value = mock_channel
    mock_conn.is_open = True
    mock_bc.return_value = mock_conn

    eid = publish("amqp://guest:guest@localhost:5672/", "a.b", {})

    assert mock_channel.exchange_declare.call_count == 1
    body = json.loads(
        mock_channel.basic_publish.call_args.kwargs["body"].decode("utf-8"),
    )
    assert body["event_id"] == eid


def test_ensure_dead_letter_queue_uses_direct_durable_path() -> None:
    ch = MagicMock()

    dlq = ensure_dead_letter_queue(ch, "inventory.booking-events")

    assert dlq == "inventory.booking-events.dead-letter"
    ch.exchange_declare.assert_called_once_with(
        exchange=DEAD_LETTER_EXCHANGE_DEFAULT,
        exchange_type="direct",
        durable=True,
    )
    ch.queue_declare.assert_called_once_with(
        queue="inventory.booking-events.dead-letter",
        durable=True,
        exclusive=False,
        auto_delete=False,
    )
    ch.queue_bind.assert_called_once_with(
        exchange=DEAD_LETTER_EXCHANGE_DEFAULT,
        queue="inventory.booking-events.dead-letter",
        routing_key="inventory.booking-events.dead-letter",
    )


@patch("ilb_common.event_bus.pika.BlockingConnection")
def test_durable_subscribe_declares_dead_letter_path(mock_bc: MagicMock) -> None:
    mock_channel = MagicMock()
    mock_channel.start_consuming = MagicMock(return_value=None)
    mock_conn = MagicMock()
    mock_conn.channel.return_value = mock_channel
    mock_conn.is_open = True
    mock_bc.return_value = mock_conn

    subscribe(
        "amqp://guest:guest@localhost:5672/",
        ["booking.approved"],
        lambda _e: None,
        queue="inventory.booking-events",
        durable_queue=True,
    )

    main_queue_declare = mock_channel.queue_declare.call_args_list[-1]
    assert main_queue_declare.kwargs["queue"] == "inventory.booking-events"
    # DLX settings are applied by RabbitMQ policies in definitions.json so
    # existing durable queues can be upgraded without redeclare precondition
    # failures. Runtime code declares only the queue and its DLQ path.
    assert main_queue_declare.kwargs["arguments"] is None
    mock_channel.queue_bind.assert_any_call(
        exchange=DEAD_LETTER_EXCHANGE_DEFAULT,
        queue="inventory.booking-events.dead-letter",
        routing_key="inventory.booking-events.dead-letter",
    )
