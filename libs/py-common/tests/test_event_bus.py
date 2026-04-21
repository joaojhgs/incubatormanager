"""Unit tests for event_bus (Pika interactions mocked)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from ilb_common.event_bus import (
    EXCHANGE_DEFAULT,
    build_envelope,
    publish,
    subscribe,
)


def test_build_envelope_shape() -> None:
    env = build_envelope("company.created", {"id": "x"})
    assert env["event_type"] == "company.created"
    assert env["payload"] == {"id": "x"}
    assert len(env["event_id"]) == 36
    assert env["occurred_at"].endswith("Z")


@patch("ilb_common.event_bus.pika.BlockingConnection")
def test_publish_serializes_envelope(mock_bc: MagicMock) -> None:
    mock_channel = MagicMock()
    mock_conn = MagicMock()
    mock_conn.channel.return_value = mock_channel
    mock_conn.is_open = True
    mock_bc.return_value = mock_conn

    eid = publish("amqp://guest:guest@localhost:5672/", "space.booked", {"a": 1})

    mock_channel.exchange_declare.assert_called_once_with(
        exchange=EXCHANGE_DEFAULT,
        exchange_type="topic",
        durable=True,
    )
    publish_kw = mock_channel.basic_publish.call_args.kwargs
    assert publish_kw["exchange"] == EXCHANGE_DEFAULT
    assert publish_kw["routing_key"] == "space.booked"
    body = json.loads(publish_kw["body"].decode())
    assert body["event_id"] == eid
    assert body["event_type"] == "space.booked"
    assert body["payload"] == {"a": 1}
    mock_conn.close.assert_called_once()


@patch("ilb_common.event_bus.pika.BlockingConnection")
def test_publish_custom_routing_key(mock_bc: MagicMock) -> None:
    mock_channel = MagicMock()
    mock_conn = MagicMock()
    mock_conn.channel.return_value = mock_channel
    mock_conn.is_open = True
    mock_bc.return_value = mock_conn

    publish(
        "amqp://guest:guest@localhost:5672/",
        "x.y",
        {},
        routing_key="custom.key",
    )

    assert mock_channel.basic_publish.call_args.kwargs["routing_key"] == "custom.key"


def test_subscribe_requires_routing_keys() -> None:
    with pytest.raises(ValueError, match="routing_keys"):
        subscribe("amqp://localhost/", [], lambda _e: None)
