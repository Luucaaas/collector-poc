"""Common pieces: connection, topology (identical to contrats.md §3.1) and JSON log."""

import json
import os
import time
from typing import Any

import aio_pika
from aio_pika.abc import (
    AbstractQueue,
    AbstractRobustChannel,
    AbstractRobustConnection,
)

EXCHANGE = "article.events"
QUEUE = "notification.article-events"
BINDING_KEY = "article.*"
ROUTING_KEY = "article.published"
RECEIPTS_QUEUE = "exp.receipts"
PREFETCH = 10


def log(event: str, **fields: Any) -> None:
    """Writes a JSON line to standard output (readable with `kubectl logs`)."""
    print(json.dumps({"ts": time.time(), "event": event, **fields}), flush=True)


async def connect() -> AbstractRobustConnection:
    """Robust connection: aio-pika reconnects on its own after a broker outage."""
    connection = await aio_pika.connect_robust(
        host=os.environ["RABBITMQ_HOST"],
        login=os.environ["RABBITMQ_USER"],
        password=os.environ["RABBITMQ_PASS"],
        reconnect_interval=1,
    )
    state = {"down": False}

    def on_lost(*_: Any) -> None:
        if not state["down"]:  # aio-pika calls this hook on every failed attempt
            state["down"] = True
            log("amqp_connection_lost")

    def on_back(*_: Any) -> None:
        state["down"] = False
        log("amqp_reconnected")

    connection.reconnect_callbacks.add(on_back)
    connection.close_callbacks.add(on_lost)
    return connection


async def declare_topology(channel: AbstractRobustChannel) -> AbstractQueue:
    """Declares a durable exchange and queue, bound by `article.*`, plus the receipts queue."""
    exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(QUEUE, durable=True)
    await queue.bind(exchange, routing_key=BINDING_KEY)
    await channel.declare_queue(RECEIPTS_QUEUE, durable=True)
    return queue
