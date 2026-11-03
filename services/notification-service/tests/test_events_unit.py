"""Tests unitaires : validation des événements et construction du contenu des notifications."""

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


def test_evenement_publie_valide_est_accepte() -> None:
    event = parse_event(body(published_event(title="Boba Fett Kenner 1979", price="120.00")))
    assert isinstance(event, PublishedEvent)
    assert str(event.data.category_id) == FIGURINES
    assert event.data.price == "120.00"
    assert event.correlation_id == "corr-published"


def test_evenement_de_prix_valide_est_accepte() -> None:
    event = parse_event(body(price_changed_event()))
    assert isinstance(event, PriceChangedEvent)
    assert (event.data.old_price, event.data.new_price) == ("120.00", "95.00")


def test_un_champ_inconnu_dans_data_est_ignore() -> None:
    raw = published_event()
    raw["data"]["nouveau_champ"] = "futur"
    assert isinstance(parse_event(body(raw)), PublishedEvent)


def test_un_champ_inconnu_dans_l_enveloppe_est_ignore() -> None:
    for raw in (published_event(), price_changed_event()):
        raw["trace_id"] = "futur"
        assert isinstance(parse_event(body(raw)), PublishedEvent | PriceChangedEvent)


def test_un_type_inconnu_bien_forme_est_reconnu_comme_tel() -> None:
    raw = published_event()
    raw["event_type"] = "article.deleted"
    raw["schema_version"] = 3  # sans importance : aucune lecture n'est tentée
    event = parse_event(body(raw))
    assert isinstance(event, UnknownTypeEvent)
    assert event.event_type == "article.deleted"
    assert str(event.event_id) == raw["event_id"]


@pytest.mark.parametrize("field", ["event_id", "occurred_at", "correlation_id", "data"])
def test_un_type_inconnu_a_enveloppe_incomplete_est_invalide(field: str) -> None:
    raw = published_event()
    raw["event_type"] = "article.deleted"
    del raw[field]
    with pytest.raises(InvalidEvent):
        parse_event(body(raw))


def test_un_type_connu_sans_event_type_lisible_est_invalide() -> None:
    raw = published_event()
    del raw["event_type"]
    with pytest.raises(InvalidEvent):
        parse_event(body(raw))


def test_le_contenu_d_un_nouvel_article_porte_titre_et_prix() -> None:
    event = parse_event(body(published_event(title="Boba Fett Kenner 1979", price="120.00")))
    assert notification_type(event) == "NEW_ARTICLE"
    assert build_content(event) == {
        "title": "Boba Fett Kenner 1979",
        "price": "120.00",
        "currency": "EUR",
    }


def test_le_contenu_d_un_changement_de_prix_porte_l_ancien_et_le_nouveau_prix() -> None:
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
        ("event_id pas un uuid", set_("abc", "event_id")),
        ("version 2", set_(2, "schema_version")),
        ("version booléenne", set_(True, "schema_version")),
        ("version en texte", set_("1", "schema_version")),
        ("producer inconnu", set_("autre-service", "producer")),
        ("date sous forme de nombre", set_(1762164000, "occurred_at")),
        ("date illisible", set_("hier", "occurred_at")),
        ("correlation_id vide", set_("", "correlation_id")),
        ("correlation_id trop long", set_("x" * 129, "correlation_id")),
        ("data absent", drop("data")),
        ("category_id absent", drop("data", "category_id")),
        ("category_id pas un uuid", set_("baskets", "data", "category_id")),
        ("seller_id vide", set_("", "data", "seller_id")),
        ("titre trop court", set_("Boba", "data", "title")),
        ("titre trop long", set_("x" * 121, "data", "title")),
        ("prix nul", set_("0.00", "data", "price")),
        ("prix à une décimale", set_("12.5", "data", "price")),
        ("prix négatif", set_("-1.00", "data", "price")),
        ("prix en nombre", set_(120.0, "data", "price")),
        ("devise en minuscules", set_("eur", "data", "currency")),
    ]


@pytest.mark.parametrize(("label", "mutate"), _mutations(), ids=[m[0] for m in _mutations()])
def test_un_evenement_non_conforme_est_invalide(label: str, mutate: Any) -> None:
    raw = copy.deepcopy(published_event())
    mutate(raw)
    with pytest.raises(InvalidEvent):
        parse_event(body(raw))


@pytest.mark.parametrize("raw", [b"", b"pas du json", b"[]", b"null", b'{"event_type": 3}', b"{}"])
def test_un_corps_qui_n_est_pas_un_evenement_est_invalide(raw: bytes) -> None:
    with pytest.raises(InvalidEvent):
        parse_event(raw)


def test_le_message_d_erreur_ne_recopie_pas_la_valeur_recue() -> None:
    raw = published_event()
    raw["data"]["price"] = "secret-12"
    with pytest.raises(InvalidEvent) as error:
        parse_event(body(raw))
    assert "secret-12" not in str(error.value)
    assert "data.price" in str(error.value)


def test_un_evenement_de_prix_exige_ancien_et_nouveau_prix() -> None:
    raw = price_changed_event()
    del raw["data"]["old_price"]
    with pytest.raises(InvalidEvent):
        parse_event(body(raw))
