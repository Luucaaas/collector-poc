"""Integration events (contrats.md §3): envelope and publication on RabbitMQ.

POC guarantee (limit L2): the event is published right after the commit, with confirmation from the
broker. If the broker stays unavailable during the allowed time, the write is kept and
the event is lost (logged). The target is a *transactional outbox*.
"""

import asyncio
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

import aio_pika
import structlog
from aio_pika.abc import AbstractExchange, AbstractRobustConnection

EXCHANGE = "article.events"
PRODUCER = "catalog-service"
SCHEMA_VERSION = 1
ARTICLE_PUBLISHED = "article.published"
ARTICLE_PRICE_CHANGED = "article.price_changed"

logger = structlog.get_logger()


def format_instant(moment: datetime) -> str:
    """UTC date-time in RFC 3339 format (`2026-11-02T14:05:00.123456Z`)."""
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Event:
    event_id: uuid.UUID
    event_type: str
    occurred_at: datetime
    correlation_id: str
    data: dict[str, Any]

    def envelope(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "schema_version": SCHEMA_VERSION,
            "occurred_at": format_instant(self.occurred_at),
            "producer": PRODUCER,
            "correlation_id": self.correlation_id,
            "data": self.data,
        }


def build_event(event_type: str, occurred_at: datetime, data: dict[str, Any]) -> Event:
    """`correlation_id` is the `X-Request-ID` of the current request (structlog context)."""
    correlation_id = structlog.contextvars.get_contextvars().get("correlation_id")
    return Event(
        event_id=uuid.uuid4(),
        event_type=event_type,
        occurred_at=occurred_at,
        correlation_id=str(correlation_id or uuid.uuid4()),
        data=data,
    )


class EventPublisher(Protocol):
    async def start(self) -> None: ...

    async def close(self) -> None: ...

    async def publish(self, event: Event) -> bool:
        """Publishes the event; returns `False` (without raising) if the broker did not confirm."""
        ...


class RabbitPublisher:
    """aio-pika producer: robust connection, durable exchange, persistent confirmed messages.

    The service starts even if RabbitMQ is absent: the connection is then attempted on each
    publication, within `budget_seconds`. Once established, aio-pika reconnects by itself.
    """

    def __init__(
        self,
        url: str,
        *,
        budget_seconds: float = 5.0,
        retry_delay_seconds: float = 0.5,
        connect_timeout_seconds: float = 3.0,
    ) -> None:
        self._url = url
        self._budget = budget_seconds
        self._retry_delay = retry_delay_seconds
        self._connect_timeout = connect_timeout_seconds
        self._connection: AbstractRobustConnection | None = None
        self._exchange: AbstractExchange | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        try:
            await self._ensure_exchange()
        except Exception as error:
            logger.warning("amqp_unavailable_at_startup", error=type(error).__name__)

    async def close(self) -> None:
        connection, self._connection, self._exchange = self._connection, None, None
        if connection is not None:
            await connection.close()

    async def _ensure_exchange(self) -> AbstractExchange:
        async with self._lock:
            if self._exchange is None:
                connection = await aio_pika.connect_robust(
                    self._url, timeout=self._connect_timeout, reconnect_interval=1
                )
                try:
                    channel = await connection.channel(publisher_confirms=True)
                    self._exchange = await channel.declare_exchange(
                        EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True
                    )
                except BaseException:
                    await connection.close()
                    raise
                self._connection = connection
                logger.info("amqp_connected", exchange=EXCHANGE)
            return self._exchange

    async def publish(self, event: Event) -> bool:
        message = aio_pika.Message(
            body=json.dumps(event.envelope()).encode(),
            message_id=str(event.event_id),
            type=event.event_type,
            content_type="application/json",
            headers={"x-correlation-id": event.correlation_id},
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        attempts = 0
        try:
            async with asyncio.timeout(self._budget):
                while True:
                    attempts += 1
                    try:
                        exchange = await self._ensure_exchange()
                        await exchange.publish(message, routing_key=event.event_type)
                        break
                    except Exception as error:
                        logger.warning(
                            "event_publish_retry",
                            event_id=str(event.event_id),
                            attempt=attempts,
                            error=type(error).__name__,
                        )
                        await asyncio.sleep(self._retry_delay)
        except TimeoutError:
            logger.error(
                "event_publish_failed",
                event_id=str(event.event_id),
                event_type=event.event_type,
                attempts=attempts,
            )
            return False
        logger.info("event_published", event_id=str(event.event_id), event_type=event.event_type)
        return True
