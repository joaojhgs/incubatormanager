"""RabbitMQ publish/subscribe helpers using Pika and the standard event envelope."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any, TypedDict

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

EXCHANGE_DEFAULT = "incubator.events"


def ensure_event_exchange(
    channel: BlockingChannel,
    *,
    exchange: str = EXCHANGE_DEFAULT,
) -> None:
    """
    Declare the ``incubator.events`` topic exchange idempotently.

    Call this before publishing or before binding a consumer queue. It is
    safe to run on every connection: RabbitMQ accepts a matching
    ``exchange.declare`` for an existing exchange of the same type and flags.
    """
    channel.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)


class EventEnvelope(TypedDict):
    event_id: str
    event_type: str
    occurred_at: str
    payload: dict[str, Any]


def _utc_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def build_envelope(event_type: str, payload: dict[str, Any]) -> EventEnvelope:
    """Build the canonical JSON envelope (without publishing)."""
    return EventEnvelope(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        occurred_at=_utc_z(),
        payload=payload,
    )


def publish(
    rabbitmq_url: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    exchange: str = EXCHANGE_DEFAULT,
    routing_key: str | None = None,
) -> str:
    """
    Publish one message to a topic exchange.

    Returns the generated ``event_id`` (also inside the message body).
    """
    body = build_envelope(event_type, payload)
    rk = routing_key if routing_key is not None else event_type
    props = BasicProperties(
        content_type="application/json",
        delivery_mode=2,
    )
    parameters = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        ensure_event_exchange(channel, exchange=exchange)
        channel.basic_publish(
            exchange=exchange,
            routing_key=rk,
            body=json.dumps(body, separators=(",", ":")).encode("utf-8"),
            properties=props,
            mandatory=False,
        )
    finally:
        connection.close()
    return body["event_id"]


def _decode_delivery(body: bytes) -> EventEnvelope:
    data = json.loads(body.decode("utf-8"))
    if not isinstance(data, dict):
        msg = "event body must be a JSON object"
        raise ValueError(msg)
    for key in ("event_id", "event_type", "occurred_at", "payload"):
        if key not in data:
            msg = f"missing envelope field: {key}"
            raise ValueError(msg)
    if not isinstance(data["payload"], dict):
        msg = "payload must be an object"
        raise ValueError(msg)
    return EventEnvelope(
        event_id=str(data["event_id"]),
        event_type=str(data["event_type"]),
        occurred_at=str(data["occurred_at"]),
        payload=dict(data["payload"]),
    )


def subscribe(
    rabbitmq_url: str,
    routing_keys: Sequence[str],
    handler: Callable[[EventEnvelope], None],
    *,
    exchange: str = EXCHANGE_DEFAULT,
    queue: str | None = None,
    durable_queue: bool = False,
    prefetch_count: int = 1,
) -> None:
    """
    Block and consume messages from *routing_keys* on a topic exchange.

    The handler runs synchronously; acknowledge only after it returns without
    raising. On handler failure the message is nacked without requeue.
    """
    if not routing_keys:
        msg = "routing_keys must not be empty"
        raise ValueError(msg)

    parameters = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        ensure_event_exchange(channel, exchange=exchange)
        channel.basic_qos(prefetch_count=prefetch_count)

        if queue:
            channel.queue_declare(
                queue=queue,
                durable=durable_queue,
                exclusive=False,
                auto_delete=False,
            )
            qname = queue
        else:
            result = channel.queue_declare(queue="", exclusive=True, auto_delete=True)
            qname = result.method.queue

        for key in routing_keys:
            channel.queue_bind(exchange=exchange, queue=qname, routing_key=key)

        def _on_message(
            ch: BlockingChannel,
            method: Basic.Deliver,
            _properties: BasicProperties,
            body: bytes,
        ) -> None:
            try:
                envelope = _decode_delivery(body)
                handler(envelope)
            except Exception:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=qname, on_message_callback=_on_message, auto_ack=False)
        channel.start_consuming()
    finally:
        if connection.is_open:
            connection.close()
