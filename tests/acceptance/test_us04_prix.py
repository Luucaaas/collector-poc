"""US-04 : le vendeur modifie le prix d'un article, l'historique est conservé (3 critères)."""

from datetime import UTC, datetime, timedelta
from typing import Any

from conftest import Api, Factory, Session
from helpers import EventSpy


def history(catalog: Api, article_id: str, user: Session) -> list[dict[str, Any]]:
    response = catalog.get(f"/api/v1/articles/{article_id}/price-history", user)
    assert response.status_code == 200
    items: list[dict[str, Any]] = response.json()["items"]
    return items


def price_of(catalog: Api, article_id: str) -> str:
    response = catalog.get(f"/api/v1/articles/{article_id}")
    assert response.status_code == 200
    return str(response.json()["price"])


def published_article(make: Factory, alice: Session, shop: dict[str, Any]) -> dict[str, Any]:
    return make.article(alice, shop["id"], make.category("Figurines")["id"])


def test_us04_ca1_prix_modifie_avec_historique(
    catalog: Api, alice: Session, alice_shop: dict[str, Any], make: Factory, spy: EventSpy
) -> None:
    article = published_article(make, alice, alice_shop)
    assert article["price"] == "120.00"
    before = datetime.now(UTC)

    response = catalog.put(
        f"/api/v1/articles/{article['id']}/price", alice, json={"price": "95.00"}
    )

    assert response.status_code == 200, response.text
    assert response.json()["price"] == "95.00"
    assert price_of(catalog, article["id"]) == "95.00"
    # Une entrée 120 € -> 95 €, datée et attribuée à alice.
    entries = history(catalog, article["id"], alice)
    assert len(entries) == 1
    entry = entries[0]
    assert (entry["old_price"], entry["new_price"]) == ("120.00", "95.00")
    assert entry["changed_by"] == alice.sub
    changed_at = datetime.fromisoformat(entry["changed_at"])
    assert before - timedelta(seconds=5) <= changed_at <= datetime.now(UTC) + timedelta(seconds=5)
    # Événement article.price_changed avec l'ancien et le nouveau prix.
    events = spy.collect(5, lambda e: any(x["event_type"] == "article.price_changed" for x in e))
    changed = [e for e in events if e["event_type"] == "article.price_changed"]
    assert len(changed) == 1
    event = changed[0]
    assert event["_routing_key"] == "article.price_changed"
    assert event["data"]["article_id"] == article["id"]
    assert (event["data"]["old_price"], event["data"]["new_price"]) == ("120.00", "95.00")
    assert event["data"]["changed_by"] == alice.sub
    assert event["data"]["seller_id"] == alice.sub
    assert event["data"]["category_id"] == article["category_id"]
    assert event["data"]["currency"] == "EUR"


def test_us04_ca2_prix_invalide_refuse(
    catalog: Api, alice: Session, alice_shop: dict[str, Any], make: Factory, spy: EventSpy
) -> None:
    article = published_article(make, alice, alice_shop)

    for invalid in ("0", "-10"):
        response = catalog.put(
            f"/api/v1/articles/{article['id']}/price", alice, json={"price": invalid}
        )
        assert response.status_code == 422, f"{invalid} : {response.text}"
        assert response.headers["content-type"].startswith("application/problem+json")

    assert price_of(catalog, article["id"]) == "120.00"
    assert history(catalog, article["id"], alice) == []
    changed = [e for e in spy.collect(1.5) if e["event_type"] == "article.price_changed"]
    assert changed == []


def test_us04_ca3_modification_non_autorisee(
    catalog: Api,
    alice: Session,
    bob: Session,
    alice_shop: dict[str, Any],
    make: Factory,
    spy: EventSpy,
) -> None:
    article = published_article(make, alice, alice_shop)
    path = f"/api/v1/articles/{article['id']}/price"

    by_bob = catalog.put(path, bob, json={"price": "10.00"})
    anonymous = catalog.put(path, json={"price": "10.00"})

    assert by_bob.status_code == 403
    assert anonymous.status_code == 401
    assert price_of(catalog, article["id"]) == "120.00"
    assert history(catalog, article["id"], alice) == []
    changed = [e for e in spy.collect(1.5) if e["event_type"] == "article.price_changed"]
    assert changed == []
