"""Unit tests for idempotent `incubator.events` topic exchange bootstrap."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from ilb_common.event_bus import EXCHANGE_DEFAULT, ensure_event_exchange, publish, subscribe


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
    mock_channel.queue_declare.assert_called_once()
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
