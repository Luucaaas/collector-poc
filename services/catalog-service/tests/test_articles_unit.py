"""Tests unitaires des articles : validation RM-01, enveloppe des événements, schémas du contrat."""

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


def test_un_article_conforme_est_valide_et_les_montants_sont_decimaux() -> None:
    article = ArticleCreate.model_validate(payload())
    assert article.price == Decimal("120.00")
    assert article.shipping_fee == Decimal("8.00")


def test_la_devise_a_une_valeur_par_defaut_les_frais_de_port_sont_obligatoires() -> None:
    body = payload()
    del body["currency"]
    assert ArticleCreate.model_validate(body).currency == "EUR"
    del body["shipping_fee"]
    with pytest.raises(PydanticValidationError):
        ArticleCreate.model_validate(body)


@pytest.mark.parametrize(
    ("overrides", "valide"),
    [
        ({"title": "a" * 4}, False),
        ({"title": "a" * 5}, True),
        ({"title": "a" * 120}, True),
        ({"title": "a" * 121}, False),
        ({"title": "    ab    "}, False),  # les espaces ne comptent pas
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
        ({"price": "120.505"}, False),  # 3 décimales
        ({"price": "1000000.00"}, True),
        ({"price": "1000000.01"}, False),
        ({"price": "9999999.99"}, False),
        ({"price": 120}, False),  # un nombre JSON n'est pas une chaîne décimale
        ({"price": 120.5}, False),
        ({"price": "1e3"}, False),
        ({"price": "12,50"}, False),
        ({"price": "abc"}, False),
        ({"shipping_fee": "0.00"}, True),
        ({"shipping_fee": "-0.01"}, False),
        ({"shipping_fee": "8.123"}, False),
        ({"shipping_fee": 8}, False),
        ({"currency": "USD"}, False),
        ({"photo_urls": []}, False),
        ({"photo_urls": ["https://a.example/1.jpg"] * 10}, True),
        ({"photo_urls": ["https://a.example/1.jpg"] * 11}, False),
        ({"photo_urls": ["http://a.example/1.jpg"]}, False),
        ({"photo_urls": ["ftp://a.example/1.jpg"]}, False),
        ({"photo_urls": ["https://"]}, False),
        ({"photo_urls": ["https://a.example/un fichier.jpg"]}, False),
        ({"photo_urls": ["images/1.jpg"]}, False),
        ({"shop_id": "pas-un-uuid"}, False),
        ({"category_id": "pas-un-uuid"}, False),
        ({"inconnu": "x"}, False),  # champ inconnu refusé (ENF-07)
    ],
)
def test_validation_rm01_bornes_de_chaque_champ(overrides: dict[str, Any], valide: bool) -> None:
    if valide:
        ArticleCreate.model_validate(payload(**overrides))
    else:
        with pytest.raises(PydanticValidationError):
            ArticleCreate.model_validate(payload(**overrides))


def test_champ_obligatoire_manquant_est_refuse() -> None:
    for champ in (
        "shop_id",
        "category_id",
        "title",
        "description",
        "photo_urls",
        "price",
        "shipping_fee",
    ):
        body = payload()
        del body[champ]
        with pytest.raises(PydanticValidationError):
            ArticleCreate.model_validate(body)


# --- Enveloppe et schémas -------------------------------------------------------------------


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


def test_enveloppe_article_published_conforme_au_schema() -> None:
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


def test_enveloppe_article_price_changed_conforme_au_schema() -> None:
    event = build_event(ARTICLE_PRICE_CHANGED, datetime.now(UTC), price_changed_data())
    assert_conforms(event.envelope())


def test_sans_contexte_de_requete_un_identifiant_de_correlation_est_genere() -> None:
    structlog.contextvars.clear_contextvars()
    event = build_event(ARTICLE_PUBLISHED, datetime.now(UTC), published_data())
    assert event.correlation_id
    assert_conforms(event.envelope())


@pytest.mark.parametrize(
    "mutation",
    [
        lambda e: e["data"].update(price="0.00"),  # prix nul
        lambda e: e["data"].update(price="120"),  # pas de décimales
        lambda e: e["data"].update(price=120.0),  # nombre au lieu de chaîne
        lambda e: e["data"].update(title="abc"),
        lambda e: e["data"].update(article_id="pas-un-uuid"),
        lambda e: e["data"].pop("category_id"),
        lambda e: e.update(extra="x"),  # l'enveloppe est fermée
        lambda e: e.update(schema_version=2),
        lambda e: e.update(producer="autre"),
        lambda e: e.update(correlation_id=""),
    ],
)
def test_le_schema_published_refuse_les_ecarts(mutation: Any) -> None:
    event = build_event(ARTICLE_PUBLISHED, datetime.now(UTC), published_data())
    envelope = event.envelope()
    mutation(envelope)
    validator = Draft202012Validator(
        SCHEMAS["article.published"], format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    with pytest.raises(ValidationError):
        validator.validate(envelope)


def test_le_schema_price_changed_refuse_un_ancien_prix_nul() -> None:
    data = price_changed_data()
    data["old_price"] = "0.00"
    envelope = build_event(ARTICLE_PRICE_CHANGED, datetime.now(UTC), data).envelope()
    validator = Draft202012Validator(SCHEMAS["article.price_changed"])
    with pytest.raises(ValidationError):
        validator.validate(envelope)
