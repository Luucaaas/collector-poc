"""Recipients and notification creation (RM-08, RM-09), on a real PostgreSQL,
without RabbitMQ: the processing is called directly."""

import json
from collections.abc import AsyncIterator, Callable
from datetime import datetime, timedelta
from typing import Any

import pytest
import structlog.testing
from prometheus_client import CollectorRegistry
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

import notification.consumer
from notification.consumer import EventProcessor
from notification.db import create_engine as create_async_engine
from notification.events import find_recipients, parse_event
from notification.metrics import BusinessMetrics
from tests.factory import (
    BASKETS,
    FIGURINES,
    OCCURRED_AT,
    price_changed_event,
    published_event,
)


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


async def test_the_buyers_of_the_category_are_recipients(
    db_url: str, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    interest(db_url, "chloe", FIGURINES)
    interest(db_url, "dave", FIGURINES)
    interest(db_url, "erin", BASKETS)  # other category
    assert await recipients(session_factory, published_event()) == ["chloe", "dave"]


async def test_the_seller_is_never_a_recipient_of_their_article(
    db_url: str, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    interest(db_url, "alice", FIGURINES)
    interest(db_url, "chloe", FIGURINES)
    assert await recipients(session_factory, published_event(seller_id="alice")) == ["chloe"]
    assert await recipients(session_factory, price_changed_event(seller_id="alice")) == ["chloe"]


async def test_without_a_saved_preference_both_types_are_active(
    db_url: str, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    interest(db_url, "chloe", FIGURINES)
    assert await recipients(session_factory, published_event()) == ["chloe"]
    assert await recipients(session_factory, price_changed_event()) == ["chloe"]


async def test_the_preference_of_the_type_concerned_is_respected(
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


async def test_no_interested_buyer_no_notification(db_url: str, processor: EventProcessor) -> None:
    assert await processor.process(parsed(published_event())) == 0
    assert notifications(db_url) == []


async def test_processing_creates_one_notification_per_recipient_and_counts(
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


async def test_rm09_the_same_event_processed_twice_creates_only_one_notification(
    db_url: str, processor: EventProcessor, metrics: BusinessMetrics
) -> None:
    interest(db_url, "chloe", FIGURINES)
    event = parsed(published_event())
    assert await processor.process(event) == 1
    assert await processor.process(event) == 0
    assert len(notifications(db_url)) == 1
    assert metrics.notifications_created.labels(type="NEW_ARTICLE")._value.get() == 1


async def test_a_new_buyer_after_a_first_processing_is_notified_without_duplicate(
    db_url: str, processor: EventProcessor
) -> None:
    """Partial replay: only the missing recipients are added."""
    interest(db_url, "chloe", FIGURINES)
    event = parsed(published_event())
    await processor.process(event)
    interest(db_url, "dave", FIGURINES)
    assert await processor.process(event) == 1
    assert [n["user_id"] for n in notifications(db_url)] == ["chloe", "dave"]


OCCURRED = datetime.fromisoformat(OCCURRED_AT)


def delay_processor(
    session_factory: async_sessionmaker[AsyncSession],
    metrics: BusinessMetrics,
    delay_seconds: float,
) -> EventProcessor:
    """Processor whose clock reads `occurred_at` + `delay_seconds` when processing ends."""
    clock: Callable[[], datetime] = lambda: OCCURRED + timedelta(seconds=delay_seconds)  # noqa: E731
    return EventProcessor(session_factory, metrics, clock)


def delay_stats(metrics: BusinessMetrics, event_type: str) -> tuple[float, float]:
    """(number of observations, sum of the delays) for an event type."""
    for family in metrics.notification_delay.collect():
        count = total = 0.0
        for sample in family.samples:
            if sample.labels.get("event_type") != event_type:
                continue
            if sample.name.endswith("_count"):
                count = sample.value
            elif sample.name.endswith("_sum"):
                total = sample.value
        return count, total
    return 0.0, 0.0


@pytest.mark.parametrize(
    ("raw_factory", "event_type"),
    [(published_event, "article.published"), (price_changed_event, "article.price_changed")],
)
async def test_the_delay_is_observed_once_per_event_with_the_right_type(
    db_url: str,
    session_factory: async_sessionmaker[AsyncSession],
    metrics: BusinessMetrics,
    raw_factory: Callable[[], dict[str, Any]],
    event_type: str,
) -> None:
    interest(db_url, "chloe", FIGURINES)
    interest(db_url, "dave", FIGURINES)
    processor = delay_processor(session_factory, metrics, 0.75)

    assert await processor.process(parsed(raw_factory())) == 2

    # One observation per event (not per notification), known delay: 0.75 s.
    assert delay_stats(metrics, event_type) == (1, pytest.approx(0.75))
    other = "article.price_changed" if event_type == "article.published" else "article.published"
    assert delay_stats(metrics, other) == (0, 0)


async def test_no_observation_without_a_created_notification(
    db_url: str, session_factory: async_sessionmaker[AsyncSession], metrics: BusinessMetrics
) -> None:
    processor = delay_processor(session_factory, metrics, 0.5)
    # No interested buyer
    assert await processor.process(parsed(published_event())) == 0
    # Redelivered duplicate: the second pass creates nothing and is not counted
    interest(db_url, "chloe", FIGURINES)
    event = parsed(published_event())
    assert await processor.process(event) == 1
    assert await processor.process(event) == 0
    assert delay_stats(metrics, "article.published") == (1, pytest.approx(0.5))


async def test_no_observation_if_the_transaction_fails(
    db_url: str,
    session_factory: async_sessionmaker[AsyncSession],
    metrics: BusinessMetrics,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    interest(db_url, "chloe", FIGURINES)

    async def failing(*_: Any) -> list[str]:
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(notification.consumer, "create_notifications", failing)
    processor = delay_processor(session_factory, metrics, 0.5)
    with pytest.raises(RuntimeError):
        await processor.process(parsed(published_event()))
    assert delay_stats(metrics, "article.published") == (0, 0)
    assert notifications(db_url) == []


async def test_a_negative_delay_is_brought_back_to_zero_and_reported(
    db_url: str, session_factory: async_sessionmaker[AsyncSession], metrics: BusinessMetrics
) -> None:
    interest(db_url, "chloe", FIGURINES)
    processor = delay_processor(session_factory, metrics, -3.0)  # producer's clock ahead
    with structlog.testing.capture_logs() as logs:
        await processor.process(parsed(published_event()))
    assert delay_stats(metrics, "article.published") == (1, 0)
    assert [log["event"] for log in logs if log["log_level"] == "warning"] == [
        "negative_notification_delay"
    ]


async def test_no_observation_if_the_commit_fails(
    db_url: str,
    session_factory: async_sessionmaker[AsyncSession],
    metrics: BusinessMetrics,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Proves the order: the observation comes after the commit, not before."""
    interest(db_url, "chloe", FIGURINES)

    async def failing_commit(self: AsyncSession) -> None:
        raise RuntimeError("simulated commit failure")

    monkeypatch.setattr(AsyncSession, "commit", failing_commit)
    processor = delay_processor(session_factory, metrics, 0.5)
    with pytest.raises(RuntimeError):
        await processor.process(parsed(published_event()))
    assert delay_stats(metrics, "article.published") == (0, 0)
    assert metrics.notifications_created.labels(type="NEW_ARTICLE")._value.get() == 0


async def test_a_naive_occurred_at_is_treated_as_utc(
    db_url: str, session_factory: async_sessionmaker[AsyncSession], metrics: BusinessMetrics
) -> None:
    interest(db_url, "chloe", FIGURINES)
    raw = published_event()
    event = parsed(raw)
    event.occurred_at = event.occurred_at.replace(tzinfo=None)  # contract violated: no time zone
    processor = delay_processor(session_factory, metrics, 1.5)
    assert await processor.process(event) == 1
    assert delay_stats(metrics, "article.published") == (1, pytest.approx(1.5))


async def test_a_measurement_error_does_not_fail_the_processing(
    db_url: str, session_factory: async_sessionmaker[AsyncSession], metrics: BusinessMetrics
) -> None:
    interest(db_url, "chloe", FIGURINES)

    def broken_clock() -> datetime:
        raise RuntimeError("clock failure")

    processor = EventProcessor(session_factory, metrics, broken_clock)
    with structlog.testing.capture_logs() as logs:
        assert await processor.process(parsed(published_event())) == 1
    assert len(notifications(db_url)) == 1
    assert delay_stats(metrics, "article.published") == (0, 0)
    assert "notification_delay_failed" in [log["event"] for log in logs]
