"""US-03: the seller publishes an article, automatically checked (4 criteria)."""

import uuid
from typing import Any

from conftest import Api, Factory, Session, published
from helpers import EventSpy


def catalog_ids(catalog: Api, **filters: str) -> list[str]:
    response = catalog.get("/api/v1/articles", params={"limit": 100, **filters})
    assert response.status_code == 200
    return [a["id"] for a in response.json()["items"]]


def test_us03_ca1_compliant_article_published(
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
    # article.published event on the article.events exchange, with the useful state.
    events = spy.collect(5, lambda e: bool(published(e, article["id"])))
    mine = published(events, article["id"])
    assert len(mine) == 1
    event = mine[0]
    assert event["_routing_key"] == "article.published"
    assert event["event_type"] == "article.published" and event["_type"] == "article.published"
    assert event["schema_version"] == 1 and event["producer"] == "catalog-service"
    assert event["_delivery_mode"] == 2  # persistent message
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
    # Visible in the public catalogue filtered on the « Figurines » category.
    assert catalog_ids(catalog, category_id=category["id"]) == [article["id"]]
    assert catalog.get(f"/api/v1/articles/{article['id']}").status_code == 200


def test_us03_ca2_article_with_contact_details_rejected(
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

        assert response.status_code == 201, response.text  # business rejection: 201, not an error
        article = response.json()
        assert article["status"] == "REJECTED"
        assert article["rejection_reasons"] == [expected_reason]
        rejected_ids.append(article["id"])

    # No event published, even after a delay that leaves time for a late send.
    events = spy.collect(2)
    assert [e for e in events if e["data"]["article_id"] in rejected_ids] == []
    # Absent from the public catalogue (list and detail); the owner can still read it.
    assert catalog_ids(catalog, category_id=category["id"]) == []
    for article_id in rejected_ids:
        assert catalog.get(f"/api/v1/articles/{article_id}").status_code == 404
        assert catalog.get(f"/api/v1/articles/{article_id}", alice).status_code == 200


def test_us03_ca3_invalid_article_rejected(
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
        "zero price": {"price": "0.00"},
        "negative price": {"price": "-5.00"},
        "no photo": {"photo_urls": []},
        "unknown category": {"category_id": unknown_category},
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
        if label == "unknown category":
            assert [e["code"] for e in errors] == ["CATEGORY_NOT_FOUND"]
        elif label.endswith("price"):
            assert [e["field"] for e in errors] == ["price"]
        else:
            assert [e["field"] for e in errors] == ["photo_urls"]

    # The contract offers no way to read unpublished articles (neither list nor detail for a
    # third party): so we check the public catalogue and the absence of events, not the database.
    # Nothing is stored or published: empty catalogue, no event.
    assert catalog_ids(catalog, category_id=category_id) == []
    assert catalog_ids(catalog, category_id=unknown_category) == []
    assert spy.collect(1.5) == []


def test_us03_ca4_publication_not_authorized(
    catalog: Api,
    alice: Session,
    chloe: Session,
    bob_shop: dict[str, Any],
    make: Factory,
    spy: EventSpy,
) -> None:
    category = make.category("Figurines")
    payload = make.article_payload(bob_shop["id"], category["id"])

    in_bobs_shop = catalog.post("/api/v1/articles", alice, json=payload)  # someone else's shop
    as_buyer = catalog.post("/api/v1/articles", chloe, json=payload)  # buyer role only
    anonymous = catalog.post("/api/v1/articles", json=payload)

    assert in_bobs_shop.status_code == 403
    assert as_buyer.status_code == 403
    assert anonymous.status_code == 401
    # Nothing in bob's shop, no event.
    assert catalog_ids(catalog, shop_id=bob_shop["id"], category_id=category["id"]) == []
    assert spy.collect(1.5) == []
