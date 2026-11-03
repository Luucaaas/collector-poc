"""Schémas JSON des événements, recopiés de `docs/02-architecture/contrats.md` §3.4 et §3.5.

Ils sont recopiés (et non lus dans le Markdown) pour que le test échoue si le code s'écarte du
contrat, et que modifier le contrat oblige à relire les tests.
"""

from datetime import datetime
from typing import Any

from jsonschema import Draft202012Validator

_ENVELOPE_REQUIRED = [
    "event_id",
    "event_type",
    "schema_version",
    "occurred_at",
    "producer",
    "correlation_id",
    "data",
]
_PRICE = "^(?!0+\\.00$)[0-9]{1,7}\\.[0-9]{2}$"
_UUID = {"type": "string", "format": "uuid"}


def _envelope(event_type: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": _ENVELOPE_REQUIRED,
        "additionalProperties": False,
        "properties": {
            "event_id": _UUID,
            "event_type": {"const": event_type},
            "schema_version": {"const": 1},
            "occurred_at": {"type": "string", "format": "date-time"},
            "producer": {"const": "catalog-service"},
            "correlation_id": {"type": "string", "minLength": 1, "maxLength": 128},
            "data": data,
        },
    }


ARTICLE_PUBLISHED = _envelope(
    "article.published",
    {
        "type": "object",
        "required": [
            "article_id",
            "shop_id",
            "seller_id",
            "category_id",
            "title",
            "price",
            "shipping_fee",
            "currency",
        ],
        "additionalProperties": True,
        "properties": {
            "article_id": _UUID,
            "shop_id": _UUID,
            "seller_id": {"type": "string", "minLength": 1},
            "category_id": _UUID,
            "title": {"type": "string", "minLength": 5, "maxLength": 120},
            "price": {"type": "string", "pattern": _PRICE},
            "shipping_fee": {"type": "string", "pattern": "^[0-9]{1,7}\\.[0-9]{2}$"},
            "currency": {"type": "string", "pattern": "^[A-Z]{3}$"},
        },
    },
)

ARTICLE_PRICE_CHANGED = _envelope(
    "article.price_changed",
    {
        "type": "object",
        "required": [
            "article_id",
            "seller_id",
            "category_id",
            "title",
            "old_price",
            "new_price",
            "currency",
            "changed_by",
        ],
        "additionalProperties": True,
        "properties": {
            "article_id": _UUID,
            "seller_id": {"type": "string", "minLength": 1},
            "category_id": _UUID,
            "title": {"type": "string", "minLength": 5, "maxLength": 120},
            "old_price": {"type": "string", "pattern": _PRICE},
            "new_price": {"type": "string", "pattern": _PRICE},
            "currency": {"type": "string", "pattern": "^[A-Z]{3}$"},
            "changed_by": {"type": "string", "minLength": 1},
        },
    },
)

SCHEMAS = {"article.published": ARTICLE_PUBLISHED, "article.price_changed": ARTICLE_PRICE_CHANGED}


def assert_conforms(envelope: dict[str, Any]) -> None:
    """Valide l'enveloppe par son schéma, formats `uuid` compris, et la date-heure à part
    (`date-time` demande une dépendance supplémentaire pour être vérifié par jsonschema)."""
    validator = Draft202012Validator(
        SCHEMAS[envelope["event_type"]], format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    validator.validate(envelope)
    assert envelope["occurred_at"].endswith("Z")
    datetime.fromisoformat(envelope["occurred_at"])
