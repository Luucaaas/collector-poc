"""Publication des événements sur un vrai RabbitMQ (testcontainers, image de l'expérimentation 1).

Une file temporaire est liée à l'exchange `article.events` par `article.*`, comme le fera
`notification-service` : c'est aussi la démonstration du point d'extension (contrats.md §3.1).
"""

import asyncio
import json
import time
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass

import aio_pika
import httpx
import pytest
import structlog
from aio_pika.abc import AbstractIncomingMessage, AbstractQueue
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from catalog.auth import JwksCache, TokenVerifier
from catalog.main import create_app
from tests.conftest import (
    AUDIENCE,
    ISSUER,
    JWKS_URL,
    JwksServer,
    TokenFactory,
    build_settings,
)
from tests.event_schemas import assert_conforms
from tests.test_api_articles import (
    ARTICLES,
    PHONE_TEXT,
    alice,
    article_body,
    make_category,
    make_shop,
    publish_article,
)

RABBITMQ_IMAGE = "rabbitmq:4.3.5-management"  # version de l'expérimentation 1
USER = PASSWORD = "collector-test"


@dataclass
class Broker:
    container: DockerContainer
    amqp_url: str
    management_url: str


def start_broker() -> DockerContainer:
    container = (
        DockerContainer(RABBITMQ_IMAGE)
        .with_env("RABBITMQ_DEFAULT_USER", USER)
        .with_env("RABBITMQ_DEFAULT_PASS", PASSWORD)
        .with_exposed_ports(5672, 15672)
        .waiting_for(LogMessageWaitStrategy("Server startup complete").with_startup_timeout(120))
    )
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


def make_client(
    db_url: str, jwks_server: JwksServer, amqp_url: str, budget: float = 5.0
) -> httpx.AsyncClient:
    settings = build_settings(db_url).model_copy(
        update={"rabbitmq_url": amqp_url, "event_publish_budget_seconds": budget}
    )
    application = create_app(settings)
    jwks = JwksCache(JWKS_URL, 600, 30, transport=httpx.MockTransport(jwks_server.handler))
    application.state.verifier = TokenVerifier(ISSUER, AUDIENCE, jwks)
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application, raise_app_exceptions=False),
        base_url="http://testserver",
    )
    client.app = application  # type: ignore[attr-defined]
    return client


@pytest.fixture
async def rabbit_client(
    broker: Broker, db_url: str, jwks_server: JwksServer
) -> AsyncIterator[httpx.AsyncClient]:
    client = make_client(db_url, jwks_server, broker.amqp_url)
    async with client.app.router.lifespan_context(client.app):  # type: ignore[attr-defined]
        yield client
    await client.aclose()


@pytest.fixture
async def tap(broker: Broker) -> AsyncIterator[AbstractQueue]:
    """File temporaire liée à `article.events` par `article.*` (consommateur supplémentaire)."""
    connection = await aio_pika.connect_robust(broker.amqp_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "article.events", aio_pika.ExchangeType.TOPIC, durable=True
        )
        queue = await channel.declare_queue(exclusive=True, auto_delete=True)
        await queue.bind(exchange, routing_key="article.*")
        yield queue


async def receive(
    queue: AbstractQueue, wait_seconds: float = 5.0
) -> AbstractIncomingMessage | None:
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        message = await queue.get(fail=False)
        if message is not None:
            await message.ack()
            return message
        await asyncio.sleep(0.1)
    return None


async def test_les_deux_evenements_arrivent_avec_leurs_proprietes_amqp(
    rabbit_client: httpx.AsyncClient, tap: AbstractQueue, make_token: TokenFactory
) -> None:
    category_id = await make_category(rabbit_client, make_token)
    shop_id = await make_shop(rabbit_client, alice(make_token))
    created = (
        await rabbit_client.post(
            ARTICLES,
            json=article_body(shop_id, category_id),
            headers={**alice(make_token), "X-Request-ID": "req-rabbit-1"},
        )
    ).json()
    changed = await rabbit_client.put(
        f"{ARTICLES}/{created['id']}/price",
        json={"price": "95.00"},
        headers={**alice(make_token), "X-Request-ID": "req-rabbit-2"},
    )
    assert changed.status_code == 200

    first, second = await receive(tap), await receive(tap)
    assert first is not None
    assert second is not None
    for message, event_type, correlation_id in (
        (first, "article.published", "req-rabbit-1"),
        (second, "article.price_changed", "req-rabbit-2"),
    ):
        envelope = json.loads(message.body)
        assert_conforms(envelope)
        assert message.routing_key == event_type
        assert message.type == event_type == envelope["event_type"]
        assert message.message_id == envelope["event_id"]
        assert message.content_type == "application/json"
        assert message.delivery_mode == aio_pika.DeliveryMode.PERSISTENT
        assert message.headers["x-correlation-id"] == correlation_id == envelope["correlation_id"]
        assert envelope["data"]["article_id"] == created["id"]
    assert json.loads(second.body)["data"]["old_price"] == "120.00"
    assert json.loads(second.body)["data"]["new_price"] == "95.00"


async def test_exchange_durable_de_type_topic(
    rabbit_client: httpx.AsyncClient, broker: Broker
) -> None:
    async with httpx.AsyncClient(auth=(USER, PASSWORD)) as management:
        response = await management.get(f"{broker.management_url}/api/exchanges/%2F/article.events")
    assert response.status_code == 200
    assert response.json()["type"] == "topic"
    assert response.json()["durable"] is True


async def test_un_article_rejected_n_envoie_aucun_message(
    rabbit_client: httpx.AsyncClient, tap: AbstractQueue, make_token: TokenFactory
) -> None:
    category_id = await make_category(rabbit_client, make_token)
    shop_id = await make_shop(rabbit_client, alice(make_token))
    rejected = await publish_article(
        rabbit_client, alice(make_token), shop_id, category_id, description=PHONE_TEXT
    )
    accepted = await publish_article(rabbit_client, alice(make_token), shop_id, category_id)
    assert rejected["status"] == "REJECTED"

    message = await receive(tap)
    assert message is not None
    assert json.loads(message.body)["data"]["article_id"] == accepted["id"]  # le seul message
    assert await receive(tap, wait_seconds=1.0) is None


async def test_broker_arrete_la_creation_repond_201_l_erreur_est_journalisee(
    db_url: str, jwks_server: JwksServer, make_token: TokenFactory
) -> None:
    container = start_broker()
    try:
        client = make_client(db_url, jwks_server, describe(container).amqp_url, budget=2.0)
        application = client.app  # type: ignore[attr-defined]
        async with application.router.lifespan_context(application):
            category_id = await make_category(client, make_token)
            shop_id = await make_shop(client, alice(make_token))
            container.get_wrapped_container().stop()  # le broker disparaît en cours de route

            with structlog.testing.capture_logs() as logs:
                started = time.monotonic()
                created = await publish_article(client, alice(make_token), shop_id, category_id)
                elapsed = time.monotonic() - started

            assert created["status"] == "PUBLISHED"  # l'écriture est conservée
            assert elapsed < 6  # la durée est bornée
            failed = [log for log in logs if log["event"] == "event_publish_failed"]
            assert len(failed) == 1
            assert failed[0]["event_type"] == "article.published"
            assert failed[0]["event_id"]
            assert (await client.get(f"{ARTICLES}/{created['id']}")).status_code == 200
            assert (await client.get("/health/ready")).status_code == 200  # sans RabbitMQ
        await client.aclose()
    finally:
        container.stop()


async def test_le_service_demarre_sans_rabbitmq_et_reste_pret(
    db_url: str, jwks_server: JwksServer, make_token: TokenFactory
) -> None:
    client = make_client(db_url, jwks_server, "amqp://u:p@127.0.0.1:1/", budget=1.0)
    application = client.app  # type: ignore[attr-defined]
    with structlog.testing.capture_logs() as logs:
        async with application.router.lifespan_context(application):
            assert (await client.get("/health/ready")).status_code == 200
            category_id = await make_category(client, make_token)
            shop_id = await make_shop(client, alice(make_token))
            created = await publish_article(client, alice(make_token), shop_id, category_id)
            assert created["status"] == "PUBLISHED"
    await client.aclose()
    events = [log["event"] for log in logs]
    assert "amqp_unavailable_at_startup" in events
    assert "event_publish_failed" in events


async def test_un_broker_gele_puis_de_retour_dans_le_delai_recoit_l_evenement(
    db_url: str, jwks_server: JwksServer, make_token: TokenFactory
) -> None:
    """Panne brève (broker gelé, puis dégelé avant la fin du délai) : le réessai aboutit."""
    container = start_broker()
    try:
        client = make_client(db_url, jwks_server, describe(container).amqp_url, budget=20.0)
        application = client.app  # type: ignore[attr-defined]
        async with application.router.lifespan_context(application):
            category_id = await make_category(client, make_token)
            shop_id = await make_shop(client, alice(make_token))
            wrapped = container.get_wrapped_container()
            wrapped.pause()
            asyncio.get_running_loop().call_later(2.0, wrapped.unpause)
            with structlog.testing.capture_logs() as logs:
                created = await publish_article(client, alice(make_token), shop_id, category_id)
            assert created["status"] == "PUBLISHED"
            assert any(log["event"] == "event_published" for log in logs)
            assert not any(log["event"] == "event_publish_failed" for log in logs)
        await client.aclose()
    finally:
        container.stop()
