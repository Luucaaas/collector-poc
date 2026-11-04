"""Outils des tests : observation des événements, attente d'une condition."""

import asyncio
import json
import time
from collections.abc import Callable
from typing import Any

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractIncomingMessage,
    AbstractQueue,
    AbstractRobustConnection,
)

from config import EXCHANGE


class EventSpy:
    """Écoute `article.events` par une file temporaire (exclusive, supprimée à la fermeture).

    La file est liée avant l'action testée : tout événement publié ensuite y est copié, sans
    gêner `notification.article-events` (chaque file reçoit sa propre copie, c'est le point
    d'extension de l'anti-fraude). Les méthodes sont synchrones : la boucle asyncio est privée.
    """

    def __init__(self, amqp_url: str) -> None:
        self._url = amqp_url
        self._loop = asyncio.new_event_loop()
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractChannel | None = None
        self._queue: AbstractQueue | None = None

    def start(self) -> "EventSpy":
        self._loop.run_until_complete(self._start())
        return self

    async def _start(self) -> None:
        self._connection = await aio_pika.connect_robust(self._url)
        self._channel = await self._connection.channel()
        exchange = await self._channel.declare_exchange(
            EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True
        )
        self._queue = await self._channel.declare_queue(exclusive=True, auto_delete=True)
        await self._queue.bind(exchange, routing_key="article.*")

    def collect(
        self, wait_seconds: float, stop_when: Callable[[list[dict[str, Any]]], bool] | None = None
    ) -> list[dict[str, Any]]:
        """Lit les événements reçus pendant `wait_seconds` (ou jusqu'à `stop_when`).

        Chaque élément est le corps JSON de l'événement plus `_routing_key`, `_message_id`,
        `_type`, `_delivery_mode` et `_correlation_header` lus dans les propriétés AMQP.
        """
        return self._loop.run_until_complete(self._collect(wait_seconds, stop_when))

    async def _collect(
        self, wait_seconds: float, stop_when: Callable[[list[dict[str, Any]]], bool] | None
    ) -> list[dict[str, Any]]:
        assert self._queue is not None
        events: list[dict[str, Any]] = []
        deadline = time.monotonic() + wait_seconds
        while (remaining := deadline - time.monotonic()) > 0:
            message = await self._queue.get(timeout=0.2, fail=False)
            if message is None:
                await asyncio.sleep(min(0.05, remaining))
                continue
            events.append(self._decode(message))
            await message.ack()
            if stop_when is not None and stop_when(events):
                break
        return events

    @staticmethod
    def _decode(message: AbstractIncomingMessage) -> dict[str, Any]:
        body: dict[str, Any] = json.loads(message.body)
        body["_routing_key"] = message.routing_key
        body["_message_id"] = message.message_id
        body["_type"] = message.type
        body["_delivery_mode"] = int(message.delivery_mode)
        body["_correlation_header"] = (message.headers or {}).get("x-correlation-id")
        return body

    def close(self) -> None:
        if self._connection is not None:
            self._loop.run_until_complete(self._connection.close())
        self._loop.close()


def wait_until[T](
    probe: Callable[[], T | None], timeout: float, interval: float = 0.05
) -> tuple[T | None, float]:
    """Appelle `probe` jusqu'à un résultat non vide ; renvoie (résultat, secondes écoulées)."""
    start = time.monotonic()
    while True:
        result = probe()
        elapsed = time.monotonic() - start
        if result is not None or elapsed >= timeout:
            return result, elapsed
        time.sleep(interval)
