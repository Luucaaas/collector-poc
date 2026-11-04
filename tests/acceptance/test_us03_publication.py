"""US-03 : le vendeur publie un article, contrôlé automatiquement (4 critères)."""

import uuid
from typing import Any

from conftest import Api, Factory, Session, published
from helpers import EventSpy


def catalog_ids(catalog: Api, **filters: str) -> list[str]:
    response = catalog.get("/api/v1/articles", params={"limit": 100, **filters})
    assert response.status_code == 200
    return [a["id"] for a in response.json()["items"]]


def test_us03_ca1_article_conforme_publie(
    catalog: Api,
    alice: Session,
    alice_shop: dict[str, Any],
    make: Factory,
    spy: EventSpy,
) -> None:
    category = make.category("Figurines")
    payload = make.article_payload(alice_shop["id"], category["id"])
    request_id = f"acceptance-{uuid.uuid4().hex}"

    response = catalog.post(
        "/api/v1/articles", alice, json=payload, headers={"X-Request-ID": request_id}
    )

    assert response.status_code == 201, response.text
    article = response.json()
    assert article["status"] == "PUBLISHED"
    assert article["rejection_reasons"] == []
    assert article["price"] == "120.00" and article["shipping_fee"] == "8.00"
    assert article["seller_id"] == alice.sub
    assert article["photo_urls"] == payload["photo_urls"]
    # Événement article.published sur l'exchange article.events, avec l'état utile.
    events = spy.collect(5, lambda e: bool(published(e, article["id"])))
    mine = published(events, article["id"])
    assert len(mine) == 1
    event = mine[0]
    assert event["_routing_key"] == "article.published"
    assert event["event_type"] == "article.published" and event["_type"] == "article.published"
    assert event["schema_version"] == 1 and event["producer"] == "catalog-service"
    assert event["_delivery_mode"] == 2  # message persistant
    assert event["_message_id"] == event["event_id"]
    assert event["correlation_id"] == request_id == event["_correlation_header"]
    assert event["data"] == {
        "article_id": article["id"],
        "shop_id": alice_shop["id"],
        "seller_id": alice.sub,
        "category_id": category["id"],
        "title": payload["title"],
        "price": "120.00",
        "shipping_fee": "8.00",
        "currency": "EUR",
    }
    # Visible dans le catalogue public filtré sur la catégorie « Figurines ».
    assert catalog_ids(catalog, category_id=category["id"]) == [article["id"]]
    assert catalog.get(f"/api/v1/articles/{article['id']}").status_code == 200


def test_us03_ca2_article_avec_coordonnees_rejete(
    catalog: Api,
    alice: Session,
    alice_shop: dict[str, Any],
    make: Factory,
    spy: EventSpy,
) -> None:
    category = make.category("Figurines")
    cases = [
        ("CONTACT_EMAIL", "Figurine en bon état, écrivez-moi à alice.martin@example.com"),
        ("CONTACT_PHONE", "Figurine en bon état, appelez le 06 12 34 56 78 après 18 h"),
        ("CONTACT_PHONE", "Figurine en bon état, appelez le +33 6 12 34 56 78 après 18 h"),
    ]
    rejected_ids: list[str] = []
    for expected_reason, description in cases:
        response = catalog.post(
            "/api/v1/articles",
            alice,
            json=make.article_payload(alice_shop["id"], category["id"], description=description),
        )

        assert response.status_code == 201, response.text  # rejet métier : 201, pas une erreur
        article = response.json()
        assert article["status"] == "REJECTED"
        assert article["rejection_reasons"] == [expected_reason]
        rejected_ids.append(article["id"])

    # Aucun événement publié, même après un délai laissant le temps à un envoi tardif.
    events = spy.collect(2)
    assert [e for e in events if e["data"]["article_id"] in rejected_ids] == []
    # Absent du catalogue public (liste et détail) ; le propriétaire, lui, peut le consulter.
    assert catalog_ids(catalog, category_id=category["id"]) == []
    for article_id in rejected_ids:
        assert catalog.get(f"/api/v1/articles/{article_id}").status_code == 404
        assert catalog.get(f"/api/v1/articles/{article_id}", alice).status_code == 200


def test_us03_ca3_article_invalide_refuse(
    catalog: Api,
    alice: Session,
    alice_shop: dict[str, Any],
    make: Factory,
    spy: EventSpy,
) -> None:
    category = make.category("Figurines")
    shop_id, category_id = alice_shop["id"], category["id"]
    unknown_category = str(uuid.uuid4())
    invalid: dict[str, dict[str, Any]] = {
        "prix nul": {"price": "0.00"},
        "prix négatif": {"price": "-5.00"},
        "aucune photo": {"photo_urls": []},
        "catégorie inexistante": {"category_id": unknown_category},
    }
    for label, overrides in invalid.items():
        response = catalog.post(
            "/api/v1/articles",
            alice,
            json={**make.article_payload(shop_id, category_id), **overrides},
        )

        assert response.status_code == 422, f"{label} : {response.text}"
        assert response.headers["content-type"].startswith("application/problem+json")
        errors = response.json()["errors"]
        if label == "catégorie inexistante":
            assert [e["code"] for e in errors] == ["CATEGORY_NOT_FOUND"]
        elif label.startswith("prix"):
            assert [e["field"] for e in errors] == ["price"]
        else:
            assert [e["field"] for e in errors] == ["photo_urls"]

    # Le contrat n'offre aucune lecture des articles non publiés (ni liste, ni détail pour un
    # tiers) : on vérifie donc le catalogue public et l'absence d'événement, pas la base.
    # Rien n'est enregistré ni publié : catalogue vide, aucun événement.
    assert catalog_ids(catalog, category_id=category_id) == []
    assert catalog_ids(catalog, category_id=unknown_category) == []
    assert spy.collect(1.5) == []


def test_us03_ca4_publication_non_autorisee(
    catalog: Api,
    alice: Session,
    chloe: Session,
    bob_shop: dict[str, Any],
    make: Factory,
    spy: EventSpy,
) -> None:
    category = make.category("Figurines")
    payload = make.article_payload(bob_shop["id"], category["id"])

    in_bobs_shop = catalog.post("/api/v1/articles", alice, json=payload)  # boutique d'un autre
    as_buyer = catalog.post("/api/v1/articles", chloe, json=payload)  # rôle buyer seul
    anonymous = catalog.post("/api/v1/articles", json=payload)

    assert in_bobs_shop.status_code == 403
    assert as_buyer.status_code == 403
    assert anonymous.status_code == 401
    # Rien dans la boutique de bob, aucun événement.
    assert catalog_ids(catalog, shop_id=bob_shop["id"], category_id=category["id"]) == []
    assert spy.collect(1.5) == []
