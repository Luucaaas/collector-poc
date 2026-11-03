"""Consommation sur un vrai RabbitMQ (testcontainers, image de l'expérimentation 1).

Les événements sont injectés dans l'exchange `article.events` comme le ferait `catalog-service`,
puis lus à travers `GET /me/notifications` : c'est la chaîne complète de US-05 (CA2 et CA3).
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

RABBITMQ_IMAGE = "rabbitmq:4.3.5-management"  # version de l'expérimentation 1
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
    """Application complète (consommateur lancé par le lifespan), connectée au vrai broker."""
    application = build_app(db_url, jwks_server, broker.amqp_url)
    async with application.router.lifespan_context(application):
        await asyncio.wait_for(application.state.consumer.connected.wait(), timeout=20)
        async with http_client(application) as client:
            yield Stack(application, client)


Publish = Callable[..., Awaitable[None]]


@pytest.fixture
async def publish(broker: Broker) -> AsyncIterator[Publish]:
    """Publie comme `catalog-service` : exchange durable, message persistant, confirmé."""
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
    """Interroge `GET /me/notifications` jusqu'à `total` notifications ; renvoie les éléments."""
    deadline = time.monotonic() + wait_seconds
    while True:
        body = (await client.get(NOTIFICATIONS, params={"limit": 100}, headers=headers)).json()
        if body["total"] >= total or time.monotonic() > deadline:
            assert body["total"] == total, f"{body['total']} notification(s) au lieu de {total}"
            return list(body["items"])
        await asyncio.sleep(0.05)


async def wait_until(condition: Callable[[], bool], wait_seconds: float = 10.0) -> None:
    deadline = time.monotonic() + wait_seconds
    while not condition():
        assert time.monotonic() < deadline, "condition non atteinte à temps"
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


# --- US-05, critères d'acceptation traversant RabbitMQ ------------------------------------------


async def test_us05_ca2_nouvel_article_notifie_chloe_en_moins_de_2_secondes_et_pas_alice(
    stack: Stack, publish: Publish, make_token: TokenFactory, record_property: Any
) -> None:
    # chloe et alice (qui a aussi le rôle buyer) s'intéressent à « Figurines »
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
    print(f"\nCA2 : notification visible {elapsed * 1000:.0f} ms après la publication")

    assert elapsed < 2.0
    assert notification["type"] == "NEW_ARTICLE"
    assert notification["article_id"] == event["data"]["article_id"]
    assert notification["content"] == {
        "title": "Boba Fett Kenner 1979",
        "price": "120.00",
        "currency": "EUR",
    }
    # Les notifications des deux acheteurs sont écrites dans la même transaction : celle de chloe
    # est visible, donc le traitement est terminé et alice n'en a pas.
    assert (await stack.client.get(NOTIFICATIONS, headers=alice(make_token))).json()["total"] == 0


async def test_us05_ca3_changement_de_prix_notifie_chloe_si_le_type_est_active(
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


async def test_us05_ca3_changement_de_prix_sans_notification_si_le_type_est_desactive(
    stack: Stack, publish: Publish, make_token: TokenFactory
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES, price_changed=False)
    await publish(price_changed_event())
    await wait_until(lambda: stack.consumed("article.price_changed", "processed") == 1)
    assert (await stack.client.get(NOTIFICATIONS, headers=chloe(make_token))).json()["total"] == 0

    # le type « nouvel article » reste actif : une publication, elle, notifie
    await publish(published_event())
    await wait_for_notifications(stack.client, chloe(make_token), 1)


# --- Règles d'événements sur un vrai broker -----------------------------------------------------


async def test_la_topologie_est_declaree_par_le_consommateur(stack: Stack, broker: Broker) -> None:
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
    # les statistiques de la console de gestion sont rafraîchies toutes les 5 s
    deadline = time.monotonic() + 20
    consumers: list[dict[str, Any]] = []
    while not consumers and time.monotonic() < deadline:
        consumers = (await queue_state(broker))["consumer_details"]
        await asyncio.sleep(0.5)
    assert len(consumers) == 1
    assert consumers[0]["prefetch_count"] == 10


async def test_le_meme_evenement_livre_deux_fois_ne_cree_qu_une_notification(
    stack: Stack, publish: Publish, make_token: TokenFactory
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES)
    event = published_event()
    await publish(event)
    await publish(event)  # doublon, même event_id (réessai du producteur, L2)
    await wait_until(lambda: stack.consumed("article.published", "processed") == 2)

    assert len(await wait_for_notifications(stack.client, chloe(make_token), 1)) == 1


async def test_des_evenements_distincts_creent_chacun_une_notification(
    stack: Stack, publish: Publish, make_token: TokenFactory
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES)
    for _ in range(25):  # plus que le prefetch : tous sont traités
        await publish(published_event())
    items = await wait_for_notifications(stack.client, chloe(make_token), 25, wait_seconds=20)
    assert len({item["id"] for item in items}) == 25


async def test_le_vendeur_n_est_pas_notifie_sur_un_vrai_broker(
    stack: Stack, publish: Publish, make_token: TokenFactory
) -> None:
    await interested(stack.client, alice(make_token), FIGURINES)
    await publish(published_event(seller_id="alice"))
    await publish(price_changed_event(seller_id="alice"))
    await wait_until(lambda: stack.consumed("article.price_changed", "processed") == 1)
    await wait_until(lambda: stack.consumed("article.published", "processed") == 1)
    assert (await stack.client.get(NOTIFICATIONS, headers=alice(make_token))).json()["total"] == 0


async def test_une_autre_categorie_ne_notifie_pas(
    stack: Stack, publish: Publish, make_token: TokenFactory
) -> None:
    await interested(stack.client, chloe(make_token), BASKETS)
    await publish(published_event(category_id=FIGURINES))
    await wait_until(lambda: stack.consumed("article.published", "processed") == 1)
    assert (await stack.client.get(NOTIFICATIONS, headers=chloe(make_token))).json()["total"] == 0


async def test_message_empoisonne_traite_deux_fois_puis_rejete_sans_bloquer_les_suivants(
    stack: Stack,
    publish: Publish,
    make_token: TokenFactory,
    broker: Broker,
    capsys: pytest.CaptureFixture[str],
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES)
    poison = published_event(title="Article empoisonné", correlation_id="corr-poison")
    processor = stack.app.state.consumer.processor
    original = processor.process
    attempts: list[bool] = []

    async def failing(event: Any) -> int:
        if str(event.event_id) == poison["event_id"]:
            attempts.append(True)
            raise RuntimeError("panne simulée")
        return int(await original(event))

    processor.process = failing
    healthy = published_event(title="Article sain")
    await publish(poison)
    await publish(healthy)

    items = await wait_for_notifications(stack.client, chloe(make_token), 1)
    await wait_until(lambda: stack.consumed("article.published", "rejected") == 1)

    assert [i["content"]["title"] for i in items] == ["Article sain"]
    assert len(attempts) == 2  # traité deux fois exactement
    assert stack.consumed("article.published", "requeued") == 1
    state = await queue_state(broker)
    assert state["messages"] == 0  # rejeté sans remise : la file est vide
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if "{" in line]
    rejected = [line for line in lines if line["event"] == "message_rejected"]
    assert len(rejected) == 1
    assert rejected[0]["event_id"] == poison["event_id"]
    assert rejected[0]["correlation_id"] == "corr-poison"
    assert rejected[0]["reason"] == "processing_failed_twice"


@pytest.mark.parametrize(
    "payload",
    [
        b"ceci n'est pas du json",
        json.dumps({"event_type": "article.published"}).encode(),
        json.dumps({**published_event(), "schema_version": 2}).encode(),
        json.dumps({**published_event(), "data": {"category_id": FIGURINES}}).encode(),
    ],
    ids=["json invalide", "schema incomplet", "version inconnue", "champs requis absents"],
)
async def test_message_invalide_rejete_sans_remise_des_la_premiere_fois(
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
    await publish(published_event())  # le message suivant passe
    await wait_for_notifications(stack.client, chloe(make_token), 1)

    assert stack.consumed("article.published", "requeued") == 0
    assert (await queue_state(broker))["messages"] == 0
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if "{" in line]
    rejected = [line for line in lines if line["event"] == "message_rejected"]
    assert len(rejected) == 1
    assert rejected[0]["reason"] == "invalid_event"


async def test_champs_inconnus_ignores_et_type_inconnu_acquitte_sans_traitement(
    stack: Stack,
    publish: Publish,
    make_token: TokenFactory,
    broker: Broker,
    capsys: pytest.CaptureFixture[str],
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES)
    futur = published_event(title="Champs de la version suivante")
    futur["trace_id"] = "nouveau champ de l'enveloppe"
    futur["data"]["etat"] = "nouveau champ de data"
    unknown = published_event(title="Article supprimé")
    unknown["event_type"] = "article.deleted"

    await publish(unknown, routing_key="article.deleted")
    await publish(futur)

    items = await wait_for_notifications(stack.client, chloe(make_token), 1)
    await wait_until(lambda: stack.consumed("unknown", "ignored") == 1)
    assert [i["content"]["title"] for i in items] == ["Champs de la version suivante"]
    assert stack.consumed("unknown", "invalid") == 0
    assert (await queue_state(broker))["messages"] == 0  # acquitté : la file est vide
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if "{" in line]
    ignored = [line for line in lines if line["event"] == "event_ignored"]
    assert len(ignored) == 1
    assert ignored[0]["event_id"] == unknown["event_id"]
    assert ignored[0]["event_type"] == "article.deleted"
    assert not [line for line in lines if line["event"] == "message_rejected"]


async def test_la_correlation_de_l_evenement_est_dans_les_logs_du_traitement(
    stack: Stack, publish: Publish, make_token: TokenFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    await interested(stack.client, chloe(make_token), FIGURINES)
    event = published_event(correlation_id="corr-de-bout-en-bout")
    await publish(event)
    await wait_for_notifications(stack.client, chloe(make_token), 1)
    await asyncio.sleep(0.1)
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if "{" in line]
    processed = [line for line in lines if line["event"] == "event_processed"]
    assert len(processed) == 1
    assert processed[0]["correlation_id"] == "corr-de-bout-en-bout"
    assert processed[0]["event_id"] == event["event_id"]
    assert processed[0]["notifications"] == 1


async def test_les_metriques_metier_sont_exposees(
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


async def test_les_messages_publies_pendant_l_arret_du_service_sont_traites_au_redemarrage(
    broker: Broker, db_url: str, jwks_server: JwksServer, publish: Publish, make_token: TokenFactory
) -> None:
    """File durable : un événement publié alors que le service est arrêté n'est pas perdu."""
    first = build_app(db_url, jwks_server, broker.amqp_url)
    async with first.router.lifespan_context(first):
        await asyncio.wait_for(first.state.consumer.connected.wait(), timeout=20)
        async with http_client(first) as client:
            await interested(client, chloe(make_token), FIGURINES)
    await publish(published_event(title="Publié pendant l'arrêt"))

    second = build_app(db_url, jwks_server, broker.amqp_url)
    async with second.router.lifespan_context(second):
        async with http_client(second) as client:
            items = await wait_for_notifications(client, chloe(make_token), 1, wait_seconds=20)
    assert items[0]["content"]["title"] == "Publié pendant l'arrêt"


# --- Démarrage sans RabbitMQ ----------------------------------------------------------------------


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


async def test_demarrage_sans_rabbitmq_puis_connexion_quand_le_broker_arrive(
    db_url: str, jwks_server: JwksServer, make_token: TokenFactory
) -> None:
    port = free_port()
    application = build_app(db_url, jwks_server, f"amqp://{USER}:{PASSWORD}@127.0.0.1:{port}/")
    consumer = application.state.consumer
    container: DockerContainer | None = None
    try:
        started = time.monotonic()
        async with application.router.lifespan_context(application):
            assert time.monotonic() - started < 2  # le démarrage n'attend pas le broker
            async with http_client(application) as client:
                await asyncio.sleep(1.0)  # plusieurs tentatives échouent
                assert not consumer.connected.is_set()
                assert (await client.get("/health/ready")).status_code == 200
                assert (await client.get("/health/live")).status_code == 200
                await interested(client, chloe(make_token), FIGURINES)

                container = start_broker(port)  # le broker arrive
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
