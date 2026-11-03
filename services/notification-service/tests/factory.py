"""Fabrique d'événements conformes au contrat (contrats.md §3.4 et §3.5)."""

import uuid
from typing import Any

from tests.event_schemas import assert_conforms

FIGURINES = "3f1e9a62-7c1d-4a8b-9f3e-2d5c6b7a8e90"
BASKETS = "7a2b4c6d-8e0f-4a1b-9c3d-5e7f9a1b3c5d"
OCCURRED_AT = "2026-11-03T10:00:00.123456Z"


def published_event(
    *,
    category_id: str = FIGURINES,
    seller_id: str = "alice",
    title: str = "Boba Fett Kenner 1979",
    price: str = "120.00",
    event_id: str | None = None,
    correlation_id: str = "corr-published",
) -> dict[str, Any]:
    event = {
        "event_id": event_id or str(uuid.uuid4()),
        "event_type": "article.published",
        "schema_version": 1,
        "occurred_at": OCCURRED_AT,
        "producer": "catalog-service",
        "correlation_id": correlation_id,
        "data": {
            "article_id": str(uuid.uuid4()),
            "shop_id": str(uuid.uuid4()),
            "seller_id": seller_id,
            "category_id": category_id,
            "title": title,
            "price": price,
            "shipping_fee": "8.00",
            "currency": "EUR",
        },
    }
    assert_conforms(event)  # les événements de test respectent le contrat, sinon le test ment
    return event


def price_changed_event(
    *,
    category_id: str = FIGURINES,
    seller_id: str = "alice",
    title: str = "Boba Fett Kenner 1979",
    old_price: str = "120.00",
    new_price: str = "95.00",
    event_id: str | None = None,
    correlation_id: str = "corr-price",
) -> dict[str, Any]:
    event = {
        "event_id": event_id or str(uuid.uuid4()),
        "event_type": "article.price_changed",
        "schema_version": 1,
        "occurred_at": OCCURRED_AT,
        "producer": "catalog-service",
        "correlation_id": correlation_id,
        "data": {
            "article_id": str(uuid.uuid4()),
            "seller_id": seller_id,
            "category_id": category_id,
            "title": title,
            "old_price": old_price,
            "new_price": new_price,
            "currency": "EUR",
            "changed_by": seller_id,
        },
    }
    assert_conforms(event)
    return event
