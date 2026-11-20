"""Unit tests of the articles: RM-01 validation, event envelope, contract schemas."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
import structlog
from jsonschema import Draft202012Validator, ValidationError
from pydantic import ValidationError as PydanticValidationError

from catalog.articles import ArticleCreate
from catalog.events import ARTICLE_PRICE_CHANGED, ARTICLE_PUBLISHED, build_event
from tests.event_schemas import SCHEMAS, assert_conforms


def payload(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "shop_id": str(uuid.uuid4()),
        "category_id": str(uuid.uuid4()),
        "title": "Boba Fett Kenner 1979",
        "description": "Figurine originale Kenner de 1979, complète, très bon état.",
        "photo_urls": ["https://images.example.com/boba-1.jpg"],
        "price": "120.00",
        "shipping_fee": "8.00",
        "currency": "EUR",
    }
    body.update(overrides)
    return body


def test_a_compliant_article_is_valid_and_amounts_are_decimal() -> None:
    article = ArticleCreate.model_validate(payload())
    assert article.price == Decimal("120.00")
    assert article.shipping_fee == Decimal("8.00")


def test_currency_has_a_default_value_shipping_cost_is_required() -> None:
    body = payload()
    del body["currency"]
    assert ArticleCreate.model_validate(body).currency == "EUR"
    del body["shipping_fee"]
    with pytest.raises(PydanticValidationError):
        ArticleCreate.model_validate(body)


@pytest.mark.parametrize(
    ("overrides", "valid"),
    [
        ({"title": "a" * 4}, False),
        ({"title": "a" * 5}, True),
        ({"title": "a" * 120}, True),
        ({"title": "a" * 121}, False),
        ({"title": "    ab    "}, False),  # spaces do not count
        ({"description": "a" * 19}, False),
        ({"description": "a" * 20}, True),
        ({"description": "a" * 5000}, True),
        ({"description": "a" * 5001}, False),
        ({"price": "0.00"}, False),
        ({"price": "0"}, False),
        ({"price": "0.01"}, True),
        ({"price": "-10"}, False),
        ({"price": "120"}, True),
        ({"price": "120.5"}, True),
        ({"price": "120.505"}, False),  # 3 decimals
        ({"price": "1000000.00"}, True),
        ({"price": "1000000.01"}, False),
        ({"price": "9999999.99"}, False),
        ({"price": 120}, False),  # a JSON number is not a decimal string
        ({"price": 120.5}, False),
        ({"price": "1e3"}, False),
        ({"price": "12,50"}, False),
        ({"price": "abc"}, False),
        ({"shipping_fee": "0.00"}, True),
        ({"shipping_fee": "-0.01"}, False),
        ({"shipping_fee": "8.123"}, False),
        ({"shipping_fee": 8}, False),
        ({"shipping_fee": "1000000.00"}, True),  # upper bound of the shipping cost
        ({"shipping_fee": "1000000.01"}, False),
        ({"currency": "USD"}, False),
        ({"photo_urls": []}, False),
        ({"photo_urls": ["https://a.example/1.jpg"] * 10}, True),
        ({"photo_urls": ["https://a.example/1.jpg"] * 11}, False),
        ({"photo_urls": ["http://a.example/1.jpg"]}, False),
        ({"photo_urls": ["ftp://a.example/1.jpg"]}, False),
        ({"photo_urls": ["https://"]}, False),
        ({"photo_urls": ["https://a.example/un fichier.jpg"]}, False),
        ({"photo_urls": ["images/1.jpg"]}, False),
        ({"shop_id": "not-a-uuid"}, False),
        ({"category_id": "not-a-uuid"}, False),
        ({"unknown": "x"}, False),  # unknown field rejected (ENF-07)
    ],
)
def test_validation_rm01_bounds_of_each_field(overrides: dict[str, Any], valid: bool) -> None:
    if valid:
        ArticleCreate.model_validate(payload(**overrides))
    else:
        with pytest.raises(PydanticValidationError):
            ArticleCreate.model_validate(payload(**overrides))


def test_missing_required_field_is_rejected() -> None:
    for field in (
        "shop_id",
        "category_id",
        "title",
        "description",
        "photo_urls",
        "price",
        "shipping_fee",
    ):
        body = payload()
        del body[field]
        with pytest.raises(PydanticValidationError):
            ArticleCreate.model_validate(body)


# --- Envelope and schemas -------------------------------------------------------------------


def published_data() -> dict[str, Any]:
    return {
        "article_id": str(uuid.uuid4()),
        "shop_id": str(uuid.uuid4()),
        "seller_id": "alice-1",
        "category_id": str(uuid.uuid4()),
        "title": "Boba Fett Kenner 1979",
        "price": "120.00",
        "shipping_fee": "8.00",
        "currency": "EUR",
    }


def price_changed_data() -> dict[str, Any]:
    return {
        "article_id": str(uuid.uuid4()),
        "seller_id": "alice-1",
        "category_id": str(uuid.uuid4()),
        "title": "Boba Fett Kenner 1979",
        "old_price": "120.00",
        "new_price": "95.00",
        "currency": "EUR",
        "changed_by": "alice-1",
    }


def test_article_published_envelope_matches_the_schema() -> None:
    moment = datetime(2026, 11, 2, 14, 5, 0, tzinfo=UTC)
    structlog.contextvars.bind_contextvars(correlation_id="req-42")
    try:
        event = build_event(ARTICLE_PUBLISHED, moment, published_data())
    finally:
        structlog.contextvars.clear_contextvars()
    envelope = event.envelope()
    assert_conforms(envelope)
    assert envelope["event_type"] == "article.published"
    assert envelope["schema_version"] == 1
    assert envelope["producer"] == "catalog-service"
    assert envelope["correlation_id"] == "req-42"
    assert envelope["occurred_at"] == "2026-11-02T14:05:00Z"


def test_article_price_changed_envelope_matches_the_schema() -> None:
    event = build_event(ARTICLE_PRICE_CHANGED, datetime.now(UTC), price_changed_data())
    assert_conforms(event.envelope())


def test_without_request_context_a_correlation_id_is_generated() -> None:
    structlog.contextvars.clear_contextvars()
    event = build_event(ARTICLE_PUBLISHED, datetime.now(UTC), published_data())
    assert event.correlation_id
    assert_conforms(event.envelope())


@pytest.mark.parametrize(
    "mutation",
    [
        lambda e: e["data"].update(price="0.00"),  # zero price
        lambda e: e["data"].update(price="120"),  # no decimals
        lambda e: e["data"].update(price=120.0),  # number instead of string
        lambda e: e["data"].update(title="abc"),
        lambda e: e["data"].update(article_id="not-a-uuid"),
        lambda e: e["data"].pop("category_id"),
        lambda e: e.update(extra="x"),  # the envelope is closed
        lambda e: e.update(schema_version=2),
        lambda e: e.update(producer="other-service"),
        lambda e: e.update(correlation_id=""),
    ],
)
def test_the_published_schema_rejects_deviations(mutation: Any) -> None:
    event = build_event(ARTICLE_PUBLISHED, datetime.now(UTC), published_data())
    envelope = event.envelope()
    mutation(envelope)
    validator = Draft202012Validator(
        SCHEMAS["article.published"], format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    with pytest.raises(ValidationError):
        validator.validate(envelope)


def test_the_price_changed_schema_rejects_a_zero_old_price() -> None:
    data = price_changed_data()
    data["old_price"] = "0.00"
    envelope = build_event(ARTICLE_PRICE_CHANGED, datetime.now(UTC), data).envelope()
    validator = Draft202012Validator(SCHEMAS["article.price_changed"])
    with pytest.raises(ValidationError):
        validator.validate(envelope)
