"""RabbitMQ consumer (contrats.md §3.1): durable queue `notification.article-events` bound to
the `article.events` exchange by `article.*`.

POC guarantees:
- acknowledgement **after** the transaction commit ("at least once" delivery);
- a message whose processing fails is requeued once, then rejected without requeue and
  logged (`message_rejected`); an invalid message is rejected the first time;
- the service starts and stays ready without RabbitMQ: the connection is attempted in the
  background, then `aio-pika` reconnects by itself to later outages.

Failure rule measured in experiment 1 (scenario C).
"""

import asyncio
import contextlib
from collections.abc import Callable
from datetime import UTC, datetime

import aio_pika
import structlog
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustConnection
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from notification.events import (
    Event,
    InvalidEvent,
    UnknownTypeEvent,
    create_notifications,
    notification_type,
    parse_event,
)
from notification.metrics import BusinessMetrics

EXCHANGE = "article.events"
QUEUE = "notification.article-events"
BINDING_KEY = "article.*"

logger = structlog.get_logger()


class EventProcessor:
    """Processes a valid event: one transaction, one commit. Separate from the transport so it can
    be tested without a broker."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        metrics: BusinessMetrics,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._session_factory = session_factory
        self._metrics = metrics
        self._clock = clock  # injectable: the tests fix the instant the processing ends

    async def process(self, event: Event) -> int:
        """Returns the number of notifications created by this call."""
        async with self._session_factory() as session:
            notified = await create_notifications(session, event)
            await session.commit()
        # The counters only move after the commit: a failure does not skew them.
        if notified:
            self._metrics.notifications_created.labels(type=notification_type(event)).inc(
                len(notified)
            )
            self._observe_delay(event)
        return len(notified)

    def _observe_delay(self, event: Event) -> None:
        """ENF-14 delay, observed once per event that created notifications. A negative
        delay (clocks out of sync between services) is brought back to 0 and reported in the logs:
        simpler than a dedicated counter, and the anomaly stays visible without creating a series.

        Called after the commit: a measurement error must never make an already processed event
        fail (and so be requeued), it is only logged.
        """
        try:
            occurred_at = event.occurred_at
            if occurred_at.tzinfo is None:  # the contract requires UTC (`Z`): without a zone, UTC
                occurred_at = occurred_at.replace(tzinfo=UTC)
            delay = (self._clock() - occurred_at).total_seconds()
            if delay < 0:
                logger.warning("negative_notification_delay", delay_seconds=round(delay, 3))
                delay = 0.0
            self._metrics.notification_delay.labels(event_type=event.event_type).observe(delay)
        except Exception as error:
            logger.warning("notification_delay_failed", error=type(error).__name__)


class ArticleEventConsumer:
    def __init__(
        self,
        url: str,
        processor: EventProcessor,
        metrics: BusinessMetrics,
        *,
        prefetch: int = 10,
        retry_seconds: float = 1.0,
        connect_timeout_seconds: float = 3.0,
    ) -> None:
        self._url = url
        self.processor = processor
        self._metrics = metrics
        self._prefetch = prefetch
        self._retry_seconds = retry_seconds
        self._connect_timeout = connect_timeout_seconds
        self._connection: AbstractRobustConnection | None = None
        self._task: asyncio.Task[None] | None = None
        self.connected = asyncio.Event()

    async def start(self) -> None:
        """Starts the connection in the background and returns immediately."""
        self._task = asyncio.create_task(self._connect_until_ready(), name="amqp-consumer")

    async def close(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        connection, self._connection = self._connection, None
        if connection is not None:
            await connection.close()
        self.connected.clear()

    async def _connect_until_ready(self) -> None:
        attempts = 0
        while True:
            attempts += 1
            try:
                await self._connect()
            except Exception as error:
                # A single service warning, then DEBUG; aiormq also writes its own ERROR
                # line (as JSON) at each attempt while the broker is absent.
                if attempts == 1:
                    logger.warning("amqp_unavailable", error=type(error).__name__)
                else:
                    logger.debug("amqp_retry", attempt=attempts, error=type(error).__name__)
                await asyncio.sleep(self._retry_seconds)
            else:
                return

    async def _connect(self) -> None:
        connection = await aio_pika.connect_robust(
            self._url, timeout=self._connect_timeout, reconnect_interval=1
        )
        try:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=self._prefetch)
            exchange = await channel.declare_exchange(
                EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True
            )
            queue = await channel.declare_queue(QUEUE, durable=True)
            await queue.bind(exchange, routing_key=BINDING_KEY)
            await queue.consume(self.handle, no_ack=False)
        except BaseException:
            await connection.close()
            raise
        self._connection = connection
        self.connected.set()
        logger.info("amqp_consumer_started", queue=QUEUE, prefetch=self._prefetch)

    async def handle(self, message: AbstractIncomingMessage) -> None:
        """Processes a message then acknowledges it. Never raises: an unhandled exception in the
        callback must not stop the consumption."""
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(message_id=message.message_id)
        try:
            await self._handle(message)
        except Exception as error:  # the acknowledgement itself failed (connection cut)
            logger.error("message_settle_failed", error=type(error).__name__)
        finally:
            structlog.contextvars.clear_contextvars()

    async def _handle(self, message: AbstractIncomingMessage) -> None:
        try:
            event = parse_event(message.body)
        except InvalidEvent as error:
            logger.warning("message_rejected", reason="invalid_event", fields=str(error))
            self._metrics.events_consumed.labels(event_type="unknown", outcome="invalid").inc()
            await message.reject(requeue=False)
            return

        structlog.contextvars.bind_contextvars(
            correlation_id=event.correlation_id, event_id=str(event.event_id)
        )
        if isinstance(event, UnknownTypeEvent):
            # Tolerant reader (contrats.md §3.3): a future type bound by `article.*` is not an
            # error. Counter on `unknown`: the received type must not create series at will.
            logger.info("event_ignored", event_type=event.event_type)
            self._count("unknown", "ignored")
            await message.ack()
            return
        try:
            created = await self.processor.process(event)
        except Exception as error:
            if message.redelivered:
                logger.error(
                    "message_rejected",
                    reason="processing_failed_twice",
                    event_type=event.event_type,
                    error=type(error).__name__,
                )
                self._count(event.event_type, "rejected")
                await message.reject(requeue=False)
            else:
                logger.warning(
                    "message_requeued", event_type=event.event_type, error=type(error).__name__
                )
                self._count(event.event_type, "requeued")
                await message.nack(requeue=True)
            return
        await message.ack()  # after the commit
        self._count(event.event_type, "processed")
        logger.info("event_processed", event_type=event.event_type, notifications=created)

    def _count(self, event_type: str, outcome: str) -> None:
        self._metrics.events_consumed.labels(event_type=event_type, outcome=outcome).inc()
