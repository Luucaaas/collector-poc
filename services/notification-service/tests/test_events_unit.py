"""Unit tests: event validation and building of the notification content."""

import copy
import json
from typing import Any

import pytest

from notification.events import (
    InvalidEvent,
    PriceChangedEvent,
    PublishedEvent,
    UnknownTypeEvent,
    build_content,
    notification_type,
    parse_event,
)
from tests.factory import FIGURINES, price_changed_event, published_event


def body(event: dict[str, Any]) -> bytes:
    return json.dumps(event).encode()


def test_valid_published_event_is_accepted() -> None:
    event = parse_event(body(published_event(title="Boba Fett Kenner 1979", price="120.00")))
    assert isinstance(event, PublishedEvent)
    assert str(event.data.category_id) == FIGURINES
    assert event.data.price == "120.00"
    assert event.correlation_id == "corr-published"


def test_valid_price_event_is_accepted() -> None:
    event = parse_event(body(price_changed_event()))
    assert isinstance(event, PriceChangedEvent)
    assert (event.data.old_price, event.data.new_price) == ("120.00", "95.00")


def test_an_unknown_field_in_data_is_ignored() -> None:
    raw = published_event()
    raw["data"]["new_field"] = "future"
    assert isinstance(parse_event(body(raw)), PublishedEvent)


def test_an_unknown_field_in_the_envelope_is_ignored() -> None:
    for raw in (published_event(), price_changed_event()):
        raw["trace_id"] = "future"
        assert isinstance(parse_event(body(raw)), PublishedEvent | PriceChangedEvent)


def test_a_well_formed_unknown_type_is_recognised_as_such() -> None:
    raw = published_event()
    raw["event_type"] = "article.deleted"
    raw["schema_version"] = 3  # irrelevant: no read is attempted
    event = parse_event(body(raw))
    assert isinstance(event, UnknownTypeEvent)
    assert event.event_type == "article.deleted"
    assert str(event.event_id) == raw["event_id"]


@pytest.mark.parametrize("field", ["event_id", "occurred_at", "correlation_id", "data"])
def test_an_unknown_type_with_an_incomplete_envelope_is_invalid(field: str) -> None:
    raw = published_event()
    raw["event_type"] = "article.deleted"
    del raw[field]
    with pytest.raises(InvalidEvent):
        parse_event(body(raw))


def test_a_known_type_without_a_readable_event_type_is_invalid() -> None:
    raw = published_event()
    del raw["event_type"]
    with pytest.raises(InvalidEvent):
        parse_event(body(raw))


def test_the_content_of_a_new_article_carries_title_and_price() -> None:
    event = parse_event(body(published_event(title="Boba Fett Kenner 1979", price="120.00")))
    assert notification_type(event) == "NEW_ARTICLE"
    assert build_content(event) == {
        "title": "Boba Fett Kenner 1979",
        "price": "120.00",
        "currency": "EUR",
    }


def test_the_content_of_a_price_change_carries_the_old_and_the_new_price() -> None:
    event = parse_event(body(price_changed_event(old_price="120.00", new_price="95.00")))
    assert notification_type(event) == "PRICE_CHANGED"
    assert build_content(event) == {
        "title": "Boba Fett Kenner 1979",
        "old_price": "120.00",
        "new_price": "95.00",
        "currency": "EUR",
    }


def _mutations() -> list[tuple[str, Any]]:
    def drop(*path: str) -> Any:
        def apply(event: dict[str, Any]) -> None:
            target = event
            for key in path[:-1]:
                target = target[key]
            del target[path[-1]]

        return apply

    def set_(value: Any, *path: str) -> Any:
        def apply(event: dict[str, Any]) -> None:
            target = event
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value

        return apply

    return [
        ("event_id absent", drop("event_id")),
        ("event_id not a uuid", set_("abc", "event_id")),
        ("version 2", set_(2, "schema_version")),
        ("boolean version", set_(True, "schema_version")),
        ("text version", set_("1", "schema_version")),
        ("unknown producer", set_("other-service", "producer")),
        ("date as a number", set_(1762164000, "occurred_at")),
        ("unreadable date", set_("yesterday", "occurred_at")),
        ("empty correlation_id", set_("", "correlation_id")),
        ("correlation_id too long", set_("x" * 129, "correlation_id")),
        ("data absent", drop("data")),
        ("category_id absent", drop("data", "category_id")),
        ("category_id not a uuid", set_("baskets", "data", "category_id")),
        ("empty seller_id", set_("", "data", "seller_id")),
        ("title too short", set_("Boba", "data", "title")),
        ("title too long", set_("x" * 121, "data", "title")),
        ("zero price", set_("0.00", "data", "price")),
        ("price with one decimal", set_("12.5", "data", "price")),
        ("negative price", set_("-1.00", "data", "price")),
        ("price as a number", set_(120.0, "data", "price")),
        ("lowercase currency", set_("eur", "data", "currency")),
    ]


@pytest.mark.parametrize(("label", "mutate"), _mutations(), ids=[m[0] for m in _mutations()])
def test_a_non_compliant_event_is_invalid(label: str, mutate: Any) -> None:
    raw = copy.deepcopy(published_event())
    mutate(raw)
    with pytest.raises(InvalidEvent):
        parse_event(body(raw))


@pytest.mark.parametrize("raw", [b"", b"not json", b"[]", b"null", b'{"event_type": 3}', b"{}"])
def test_a_body_that_is_not_an_event_is_invalid(raw: bytes) -> None:
    with pytest.raises(InvalidEvent):
        parse_event(raw)


def test_the_error_message_does_not_copy_the_received_value() -> None:
    raw = published_event()
    raw["data"]["price"] = "secret-12"
    with pytest.raises(InvalidEvent) as error:
        parse_event(body(raw))
    assert "secret-12" not in str(error.value)
    assert "data.price" in str(error.value)


def test_a_price_event_requires_old_and_new_price() -> None:
    raw = price_changed_event()
    del raw["data"]["old_price"]
    with pytest.raises(InvalidEvent):
        parse_event(body(raw))
