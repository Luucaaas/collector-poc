"""Consumption on a real RabbitMQ (testcontainers, image of experiment 1).

Events are injected into the `article.events` exchange as `catalog-service` would do,
then read through `GET /me/notifications`: this is the complete chain of US-05 (AC2 and AC3).
"""

import asyncio
import json
import socket
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from dataclasses import dataclass
from typing import Any

import aio_pika
import httpx
import pytest
from aio_pika.abc import AbstractExchange
from fastapi import FastAPI
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from notification.auth import JwksCache, TokenVerifier
from notification.main import create_app
from tests.conftest import (
    AUDIENCE,
    ISSUER,
    JWKS_URL,
    JwksServer,
    TokenFactory,
    build_settings,
    roles_headers,
)
from tests.factory import BASKETS, FIGURINES, price_changed_event, published_event

RABBITMQ_IMAGE = "rabbitmq:4.3.5-management"  # version of experiment 1
USER = PASSWORD = "collector-test"
INTERESTS = "/api/v1/me/interests"
PREFERENCES = "/api/v1/me/preferences"
NOTIFICATIONS = "/api/v1/me/notifications"
QUEUE = "notification.article-events"


@dataclass
class Broker:
    container: DockerContainer
    amqp_url: str
    management_url: str


def start_broker(amqp_port: int | None = None) -> DockerContainer:
    container = (
        DockerContainer(RABBITMQ_IMAGE)
        .with_env("RABBITMQ_DEFAULT_USER", USER)
        .with_env("RABBITMQ_DEFAULT_PASS", PASSWORD)
        .with_exposed_ports(5672, 15672)
        .waiting_for(LogMessageWaitStrategy("Server startup complete").with_startup_timeout(120))
    )
    if amqp_port is not None:
        container = container.with_bind_ports(5672, amqp_port)
    container.start()
    return container


def describe(container: DockerContainer) -> Broker:
    host = container.get_container_host_ip()
    return Broker(
        container,
        f"amqp://{USER}:{PASSWORD}@{host}:{container.get_exposed_port(5672)}/",
        f"http://{host}:{container.get_exposed_port(15672)}",
    )


@pytest.fixture(scope="module")
def broker() -> Iterator[Broker]:
    container = start_broker()
    try:
        yield describe(container)
    finally:
        container.stop()


def build_app(db_url: str, jwks_server: JwksServer, amqp_url: str, retry: float = 0.2) -> FastAPI:
    settings = build_settings(db_url).model_copy(
        update={"rabbitmq_url": amqp_url, "amqp_retry_seconds": retry}
    )
    application = create_app(settings)
    jwks = JwksCache(JWKS_URL, 600, 30, transport=httpx.MockTransport(jwks_server.handler))
    application.state.verifier = TokenVerifier(ISSUER, AUDIENCE, jwks)
    return application


def http_client(application: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application, raise_app_exceptions=False),
        base_url="http://testserver",
    )


@dataclass
class Stack:
    app: FastAPI
    client: httpx.AsyncClient

    def consumed(self, event_type: str, outcome: str) -> float:
        counter = self.app.state.business_metrics.events_consumed
        return float(counter.labels(event_type=event_type, outcome=outcome)._value.get())


@pytest.fixture
async def stack(broker: Broker, db_url: str, jwks_server: JwksServer) -> AsyncIterator[Stack]:
    """Complete application (consumer started by the lifespan), connected to the real broker."""
    application = build_app(db_url, jwks_server, broker.amqp_url)
    async with application.router.lifespan_context(application):
        await asyncio.wait_for(application.state.consumer.connected.wait(), timeout=20)
        async with http_client(application) as client:
            yield Stack(application, client)


Publish = Callable[..., Awaitable[None]]


@pytest.fixture
async def publish(broker: Broker) -> AsyncIterator[Publish]:
    """Publishes like `catalog-service`: durable exchange, persistent message, confirmed."""
    connection = await aio_pika.connect_robust(broker.amqp_url)
    channel = await connection.channel(publisher_confirms=True)
    exchange: AbstractExchange = await channel.declare_exchange(
        "article.events", aio_pika.ExchangeType.TOPIC, durable=True
    )

    async def send(event: dict[str, Any] | bytes, routing_key: str | None = None) -> None:
        body = event if isinstance(event, bytes) else json.dumps(event).encode()
        key = routing_key or (
            event["event_type"] if isinstance(event, dict) else "article.published"
        )
        await exchange.publish(
            aio_pika.Message(
                body=body,
                message_id=event["event_id"] if isinstance(event, dict) else None,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=key,
        )

    yield send
    await connection.close()


def chloe(make_token: TokenFactory) -> dict[str, str]:
    return roles_headers(make_token, "chloe", "buyer")


def alice(make_token: TokenFactory) -> dict[str, str]:
    return roles_headers(make_token, "alice", "seller", "buyer")


async def wait_for_notifications(
    client: httpx.AsyncClient, headers: dict[str, str], total: int, wait_seconds: float = 10.0
) -> list[dict[str, Any]]:
    """Polls `GET /me/notifications` until `total` notifications; returns the items."""
    deadline = time.monotonic() + wait_seconds
    while True:
        body = (await client.get(NOTIFICATIONS, params={"limit": 100}, headers=headers)).json()
        if body["total"] >= total or time.monotonic() > deadline:
            assert body["total"] == total, f"{body['total']} notification(s) instead of {total}"
            return list(body["items"])
        await asyncio.sleep(0.05)


async def wait_until(condition: Callable[[], bool], wait_seconds: float = 10.0) -> None:
    deadline = time.monotonic() + wait_seconds
    while not condition():
        assert time.monotonic() < deadline, "condition not reached in time"
        await asyncio.sleep(0.05)


async def interested(
    client: httpx.AsyncClient, headers: dict[str, str], *categories: str, **preferences: bool
) -> None:
    assert (
        await client.put(INTERESTS, json={"category_ids": list(categories)}, headers=headers)
    ).status_code == 200
    if preferences:
        body = {"new_article": True, "price_changed": True, **preferences}
        assert (await client.put(PREFERENCES, json=body, headers=headers)).status_code == 200


async def queue_state(broker: Broker, name: str = QUEUE) -> dict[str, Any]:
    async with httpx.AsyncClient(auth=(USER, PASSWORD)) as management:
        response = await management.get(f"{broker.management_url}/api/queues/%2F/{name}")
    assert response.status_code == 200
    return dict(response.json())


# --- US-05, acceptance criteria going through RabbitMQ ------------------------------------------


async def test_us05_ca2_new_article_notifies_chloe_within_2_seconds_and_not_alice(
    stack: Stack, publish: Publish, make_token: TokenFactory, record_property: Any
) -> None:
    # chloe and alice (who also has the buyer role) are interested in "Figurines"
    await interested(stack.client, chloe(make_token), FIGURINES, new_article=True)
    await interested(stack.client, alice(make_token), FIGURINES)
    event = published_event(seller_id="alice", title="Boba Fett Kenner 1979", price="120.00")

    started = time.perf_counter()
    await publish(event)
    (notification,) = await wait_for_notifications(
        stack.client, chloe(make_token), 1, wait_seconds=2
    )
    elapsed = time.perf_counter() - started
    record_property("delai_ca2_secondes", round(elapsed, 3))
    print(f"\nAC2: notification visible {elapsed * 1000:.0f} ms after the publication")

    assert elapsed < 2.0
    assert notification["type"] == "NEW_ARTICLE"
    assert notification["article_id"] == event["data"]["article_id"]
    assert notification["content"] == {
        "title": "Boba Fett Kenner 1979",
        "price": "120.00",
        "currency": "EUR",
    }
    # The notifications of both buyers are written in the same transaction: chloe's
    # is visible, so the processing is over and alice has none.
    assert (await stack.client.get(NOTIFICATIONS, headers=alice(make_token))).json()["total"] == 0


async def test_us05_ca3_price_change_notifies_chloe_if_the_type_is_enabled(
    stack: Stack, publish: Publish, make_token: TokenFactory
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES, price_changed=True)
    await publish(price_changed_event(old_price="120.00", new_price="95.00"))

    (notification,) = await wait_for_notifications(stack.client, chloe(make_token), 1)
    assert notification["type"] == "PRICE_CHANGED"
    assert notification["content"] == {
        "title": "Boba Fett Kenner 1979",
        "old_price": "120.00",
        "new_price": "95.00",
        "currency": "EUR",
    }


async def test_us05_ca3_price_change_without_notification_if_the_type_is_disabled(
    stack: Stack, publish: Publish, make_token: TokenFactory
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES, price_changed=False)
    await publish(price_changed_event())
    await wait_until(lambda: stack.consumed("article.price_changed", "processed") == 1)
    assert (await stack.client.get(NOTIFICATIONS, headers=chloe(make_token))).json()["total"] == 0

    # the "new article" type stays active: a publication, on the other hand, notifies
    await publish(published_event())
    await wait_for_notifications(stack.client, chloe(make_token), 1)


# --- Event rules on a real broker -----------------------------------------------------


async def test_the_topology_is_declared_by_the_consumer(stack: Stack, broker: Broker) -> None:
    queue = await queue_state(broker)
    assert queue["durable"] is True
    async with httpx.AsyncClient(auth=(USER, PASSWORD)) as management:
        exchange = await management.get(f"{broker.management_url}/api/exchanges/%2F/article.events")
        bindings = await management.get(
            f"{broker.management_url}/api/bindings/%2F/e/article.events/q/{QUEUE}"
        )
    assert exchange.json()["type"] == "topic"
    assert exchange.json()["durable"] is True
    assert [b["routing_key"] for b in bindings.json()] == ["article.*"]
    # the management console statistics are refreshed every 5 s
    deadline = time.monotonic() + 20
    consumers: list[dict[str, Any]] = []
    while not consumers and time.monotonic() < deadline:
        consumers = (await queue_state(broker))["consumer_details"]
        await asyncio.sleep(0.5)
    assert len(consumers) == 1
    assert consumers[0]["prefetch_count"] == 10


async def test_the_same_event_delivered_twice_creates_only_one_notification(
    stack: Stack, publish: Publish, make_token: TokenFactory
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES)
    event = published_event()
    await publish(event)
    await publish(event)  # duplicate, same event_id (producer retry, L2)
    await wait_until(lambda: stack.consumed("article.published", "processed") == 2)

    assert len(await wait_for_notifications(stack.client, chloe(make_token), 1)) == 1


async def test_distinct_events_each_create_a_notification(
    stack: Stack, publish: Publish, make_token: TokenFactory
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES)
    for _ in range(25):  # more than the prefetch: all are processed
        await publish(published_event())
    items = await wait_for_notifications(stack.client, chloe(make_token), 25, wait_seconds=20)
    assert len({item["id"] for item in items}) == 25


async def test_the_seller_is_not_notified_on_a_real_broker(
    stack: Stack, publish: Publish, make_token: TokenFactory
) -> None:
    await interested(stack.client, alice(make_token), FIGURINES)
    await publish(published_event(seller_id="alice"))
    await publish(price_changed_event(seller_id="alice"))
    await wait_until(lambda: stack.consumed("article.price_changed", "processed") == 1)
    await wait_until(lambda: stack.consumed("article.published", "processed") == 1)
    assert (await stack.client.get(NOTIFICATIONS, headers=alice(make_token))).json()["total"] == 0


async def test_another_category_does_not_notify(
    stack: Stack, publish: Publish, make_token: TokenFactory
) -> None:
    await interested(stack.client, chloe(make_token), BASKETS)
    await publish(published_event(category_id=FIGURINES))
    await wait_until(lambda: stack.consumed("article.published", "processed") == 1)
    assert (await stack.client.get(NOTIFICATIONS, headers=chloe(make_token))).json()["total"] == 0


async def test_poison_message_processed_twice_then_rejected_without_blocking_the_next_ones(
    stack: Stack,
    publish: Publish,
    make_token: TokenFactory,
    broker: Broker,
    capsys: pytest.CaptureFixture[str],
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES)
    poison = published_event(title="Poisoned article", correlation_id="corr-poison")
    processor = stack.app.state.consumer.processor
    original = processor.process
    attempts: list[bool] = []

    async def failing(event: Any) -> int:
        if str(event.event_id) == poison["event_id"]:
            attempts.append(True)
            raise RuntimeError("simulated failure")
        return int(await original(event))

    processor.process = failing
    healthy = published_event(title="Article sain")
    await publish(poison)
    await publish(healthy)

    items = await wait_for_notifications(stack.client, chloe(make_token), 1)
    await wait_until(lambda: stack.consumed("article.published", "rejected") == 1)

    assert [i["content"]["title"] for i in items] == ["Article sain"]
    assert len(attempts) == 2  # processed exactly twice
    assert stack.consumed("article.published", "requeued") == 1
    state = await queue_state(broker)
    assert state["messages"] == 0  # rejected without requeue: the queue is empty
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if "{" in line]
    rejected = [line for line in lines if line["event"] == "message_rejected"]
    assert len(rejected) == 1
    assert rejected[0]["event_id"] == poison["event_id"]
    assert rejected[0]["correlation_id"] == "corr-poison"
    assert rejected[0]["reason"] == "processing_failed_twice"


@pytest.mark.parametrize(
    "payload",
    [
        b"this is not json",
        json.dumps({"event_type": "article.published"}).encode(),
        json.dumps({**published_event(), "schema_version": 2}).encode(),
        json.dumps({**published_event(), "data": {"category_id": FIGURINES}}).encode(),
    ],
    ids=["invalid json", "incomplete schema", "unknown version", "missing required fields"],
)
async def test_invalid_message_rejected_without_requeue_the_first_time(
    stack: Stack,
    publish: Publish,
    make_token: TokenFactory,
    broker: Broker,
    payload: bytes,
    capsys: pytest.CaptureFixture[str],
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES)
    await publish(payload)
    await wait_until(lambda: stack.consumed("unknown", "invalid") == 1)
    await publish(published_event())  # the next message goes through
    await wait_for_notifications(stack.client, chloe(make_token), 1)

    assert stack.consumed("article.published", "requeued") == 0
    assert (await queue_state(broker))["messages"] == 0
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if "{" in line]
    rejected = [line for line in lines if line["event"] == "message_rejected"]
    assert len(rejected) == 1
    assert rejected[0]["reason"] == "invalid_event"


async def test_unknown_fields_ignored_and_unknown_type_acknowledged_without_processing(
    stack: Stack,
    publish: Publish,
    make_token: TokenFactory,
    broker: Broker,
    capsys: pytest.CaptureFixture[str],
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES)
    future = published_event(title="Fields of the next version")
    future["trace_id"] = "new envelope field"
    future["data"]["state"] = "new data field"
    unknown = published_event(title="Deleted article")
    unknown["event_type"] = "article.deleted"

    await publish(unknown, routing_key="article.deleted")
    await publish(future)

    items = await wait_for_notifications(stack.client, chloe(make_token), 1)
    await wait_until(lambda: stack.consumed("unknown", "ignored") == 1)
    assert [i["content"]["title"] for i in items] == ["Fields of the next version"]
    assert stack.consumed("unknown", "invalid") == 0
    assert (await queue_state(broker))["messages"] == 0  # acknowledged: the queue is empty
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if "{" in line]
    ignored = [line for line in lines if line["event"] == "event_ignored"]
    assert len(ignored) == 1
    assert ignored[0]["event_id"] == unknown["event_id"]
    assert ignored[0]["event_type"] == "article.deleted"
    assert not [line for line in lines if line["event"] == "message_rejected"]


async def test_the_event_correlation_is_in_the_processing_logs(
    stack: Stack, publish: Publish, make_token: TokenFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES)
    event = published_event(correlation_id="corr-end-to-end")
    await publish(event)
    await wait_for_notifications(stack.client, chloe(make_token), 1)
    await asyncio.sleep(0.1)
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if "{" in line]
    processed = [line for line in lines if line["event"] == "event_processed"]
    assert len(processed) == 1
    assert processed[0]["correlation_id"] == "corr-end-to-end"
    assert processed[0]["event_id"] == event["event_id"]
    assert processed[0]["notifications"] == 1


async def test_the_business_metrics_are_exposed(
    stack: Stack, publish: Publish, make_token: TokenFactory
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES)
    await publish(published_event())
    await publish(price_changed_event())
    await wait_for_notifications(stack.client, chloe(make_token), 2)
    await wait_until(lambda: stack.consumed("article.price_changed", "processed") == 1)

    metrics = (await stack.client.get("/metrics")).text
    assert 'notifications_created_total{type="NEW_ARTICLE"} 1.0' in metrics
    assert 'notifications_created_total{type="PRICE_CHANGED"} 1.0' in metrics
    assert (
        'events_consumed_total{event_type="article.published",outcome="processed"} 1.0' in metrics
    )


async def test_messages_published_while_the_service_is_stopped_are_processed_on_restart(
    broker: Broker, db_url: str, jwks_server: JwksServer, publish: Publish, make_token: TokenFactory
) -> None:
    """Durable queue: an event published while the service is stopped is not lost."""
    first = build_app(db_url, jwks_server, broker.amqp_url)
    async with first.router.lifespan_context(first):
        await asyncio.wait_for(first.state.consumer.connected.wait(), timeout=20)
        async with http_client(first) as client:
            await interested(client, chloe(make_token), FIGURINES)
    await publish(published_event(title="Published during the stop"))

    second = build_app(db_url, jwks_server, broker.amqp_url)
    async with second.router.lifespan_context(second):
        async with http_client(second) as client:
            items = await wait_for_notifications(client, chloe(make_token), 1, wait_seconds=20)
    assert items[0]["content"]["title"] == "Published during the stop"


# --- Startup without RabbitMQ ------------------------------------------------------------


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


async def test_startup_without_rabbitmq_then_connection_when_the_broker_arrives(
    db_url: str, jwks_server: JwksServer, make_token: TokenFactory
) -> None:
    port = free_port()
    application = build_app(db_url, jwks_server, f"amqp://{USER}:{PASSWORD}@127.0.0.1:{port}/")
    consumer = application.state.consumer
    container: DockerContainer | None = None
    try:
        started = time.monotonic()
        async with application.router.lifespan_context(application):
            assert time.monotonic() - started < 2  # startup does not wait for the broker
            async with http_client(application) as client:
                await asyncio.sleep(1.0)  # several attempts fail
                assert not consumer.connected.is_set()
                assert (await client.get("/health/ready")).status_code == 200
                assert (await client.get("/health/live")).status_code == 200
                await interested(client, chloe(make_token), FIGURINES)

                container = start_broker(port)  # the broker arrives
                await asyncio.wait_for(consumer.connected.wait(), timeout=30)
                assert (await client.get("/health/ready")).status_code == 200

                connection = await aio_pika.connect_robust(describe(container).amqp_url)
                async with connection:
                    channel = await connection.channel(publisher_confirms=True)
                    exchange = await channel.declare_exchange(
                        "article.events", aio_pika.ExchangeType.TOPIC, durable=True
                    )
                    event = published_event()
                    await exchange.publish(
                        aio_pika.Message(
                            json.dumps(event).encode(),
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        ),
                        routing_key="article.published",
                    )
                await wait_for_notifications(client, chloe(make_token), 1, wait_seconds=10)
    finally:
        if container is not None:
            container.stop()
