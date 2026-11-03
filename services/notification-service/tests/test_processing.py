"""Calcul des destinataires et création des notifications (RM-08, RM-09), sur un vrai PostgreSQL,
sans RabbitMQ : le traitement est appelé directement."""

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
from prometheus_client import CollectorRegistry
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from notification.consumer import EventProcessor
from notification.db import create_engine as create_async_engine
from notification.events import find_recipients, parse_event
from notification.metrics import BusinessMetrics
from tests.factory import BASKETS, FIGURINES, price_changed_event, published_event


@pytest.fixture
async def engine(db_url: str) -> AsyncIterator[AsyncEngine]:
    async_engine = create_async_engine(db_url, 3)
    yield async_engine
    await async_engine.dispose()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def metrics() -> BusinessMetrics:
    return BusinessMetrics(CollectorRegistry())


@pytest.fixture
def processor(
    session_factory: async_sessionmaker[AsyncSession], metrics: BusinessMetrics
) -> EventProcessor:
    return EventProcessor(session_factory, metrics)


def interest(db_url: str, user_id: str, category_id: str) -> None:
    engine = create_engine(db_url)
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO interests (user_id, category_id) VALUES (:u, :c)"),
            {"u": user_id, "c": category_id},
        )
    engine.dispose()


def preference(db_url: str, user_id: str, *, new_article: bool, price_changed: bool) -> None:
    engine = create_engine(db_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO preferences (user_id, new_article, price_changed) VALUES (:u, :n, :p)"
            ),
            {"u": user_id, "n": new_article, "p": price_changed},
        )
    engine.dispose()


def notifications(db_url: str) -> list[dict[str, Any]]:
    engine = create_engine(db_url)
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT user_id, type, content, source_event_id FROM notifications ORDER BY user_id"
            )
        ).mappings()
        result = [dict(row) for row in rows]
    engine.dispose()
    return result


def parsed(raw: dict[str, Any]) -> Any:
    return parse_event(json.dumps(raw).encode())


async def recipients(
    session_factory: async_sessionmaker[AsyncSession], raw: dict[str, Any]
) -> list[str]:
    async with session_factory() as session:
        return await find_recipients(session, parsed(raw))


async def test_les_acheteurs_de_la_categorie_sont_destinataires(
    db_url: str, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    interest(db_url, "chloe", FIGURINES)
    interest(db_url, "dave", FIGURINES)
    interest(db_url, "erin", BASKETS)  # autre catégorie
    assert await recipients(session_factory, published_event()) == ["chloe", "dave"]


async def test_le_vendeur_n_est_jamais_destinataire_de_son_article(
    db_url: str, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    interest(db_url, "alice", FIGURINES)
    interest(db_url, "chloe", FIGURINES)
    assert await recipients(session_factory, published_event(seller_id="alice")) == ["chloe"]
    assert await recipients(session_factory, price_changed_event(seller_id="alice")) == ["chloe"]


async def test_sans_preference_enregistree_les_deux_types_sont_actifs(
    db_url: str, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    interest(db_url, "chloe", FIGURINES)
    assert await recipients(session_factory, published_event()) == ["chloe"]
    assert await recipients(session_factory, price_changed_event()) == ["chloe"]


async def test_la_preference_du_type_concerne_est_respectee(
    db_url: str, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    interest(db_url, "chloe", FIGURINES)
    interest(db_url, "dave", FIGURINES)
    interest(db_url, "erin", FIGURINES)
    preference(db_url, "chloe", new_article=True, price_changed=False)
    preference(db_url, "dave", new_article=False, price_changed=True)
    preference(db_url, "erin", new_article=False, price_changed=False)

    assert await recipients(session_factory, published_event()) == ["chloe"]
    assert await recipients(session_factory, price_changed_event()) == ["dave"]


async def test_aucun_interesse_aucune_notification(db_url: str, processor: EventProcessor) -> None:
    assert await processor.process(parsed(published_event())) == 0
    assert notifications(db_url) == []


async def test_le_traitement_cree_une_notification_par_destinataire_et_compte(
    db_url: str, processor: EventProcessor, metrics: BusinessMetrics
) -> None:
    interest(db_url, "chloe", FIGURINES)
    interest(db_url, "dave", FIGURINES)
    raw = price_changed_event(old_price="120.00", new_price="95.00")

    assert await processor.process(parsed(raw)) == 2

    stored = notifications(db_url)
    assert [n["user_id"] for n in stored] == ["chloe", "dave"]
    assert {n["type"] for n in stored} == {"PRICE_CHANGED"}
    assert stored[0]["content"]["old_price"] == "120.00"
    assert str(stored[0]["source_event_id"]) == raw["event_id"]
    assert metrics.notifications_created.labels(type="PRICE_CHANGED")._value.get() == 2


async def test_rm09_le_meme_evenement_traite_deux_fois_ne_cree_qu_une_notification(
    db_url: str, processor: EventProcessor, metrics: BusinessMetrics
) -> None:
    interest(db_url, "chloe", FIGURINES)
    event = parsed(published_event())
    assert await processor.process(event) == 1
    assert await processor.process(event) == 0
    assert len(notifications(db_url)) == 1
    assert metrics.notifications_created.labels(type="NEW_ARTICLE")._value.get() == 1


async def test_un_nouvel_acheteur_apres_un_premier_traitement_est_notifie_sans_doublon(
    db_url: str, processor: EventProcessor
) -> None:
    """Rejeu partiel : seuls les destinataires manquants sont ajoutés."""
    interest(db_url, "chloe", FIGURINES)
    event = parsed(published_event())
    await processor.process(event)
    interest(db_url, "dave", FIGURINES)
    assert await processor.process(event) == 1
    assert [n["user_id"] for n in notifications(db_url)] == ["chloe", "dave"]
