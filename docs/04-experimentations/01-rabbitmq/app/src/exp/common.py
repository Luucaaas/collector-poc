"""Éléments communs : connexion, topologie (identique à contrats.md §3.1) et journal JSON."""

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
    """Écrit une ligne JSON sur la sortie standard (lisible par `kubectl logs`)."""
    print(json.dumps({"ts": time.time(), "event": event, **fields}), flush=True)


async def connect() -> AbstractRobustConnection:
    """Connexion robuste : aio-pika se reconnecte seul après une coupure du broker."""
    connection = await aio_pika.connect_robust(
        host=os.environ["RABBITMQ_HOST"],
        login=os.environ["RABBITMQ_USER"],
        password=os.environ["RABBITMQ_PASS"],
        reconnect_interval=1,
    )
    connection.reconnect_callbacks.add(lambda *_: log("amqp_reconnected"))
    connection.close_callbacks.add(lambda *_: log("amqp_connection_lost"))
    return connection


async def declare_topology(channel: AbstractRobustChannel) -> AbstractQueue:
    """Déclare exchange et file durables, liés par `article.*`, plus la file des accusés."""
    exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(QUEUE, durable=True)
    await queue.bind(exchange, routing_key=BINDING_KEY)
    await channel.declare_queue(RECEIPTS_QUEUE, durable=True)
    return queue
