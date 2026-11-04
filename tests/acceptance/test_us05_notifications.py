"""US-05 : centres d'intérêt, préférences et notifications de l'acheteur (4 critères).

Les comptes `chloe` et `alice` gardent leur état d'un test à l'autre (et d'une exécution à
l'autre) : chaque test commence par fixer ses propres centres d'intérêt et préférences, et ne
regarde que les notifications de ses propres articles.
"""

import re
import time
from collections.abc import Callable
from typing import Any

from conftest import Api, Factory, Session
from helpers import wait_until

MAX_DELAY_SECONDS = 2.0  # US-05 CA2


def set_interests(notification: Api, user: Session, category_ids: list[str]) -> None:
    response = notification.put("/api/v1/me/interests", user, json={"category_ids": category_ids})
    assert response.status_code == 200, response.text


def set_preferences(
    notification: Api, user: Session, new_article: bool, price_changed: bool
) -> None:
    response = notification.put(
        "/api/v1/me/preferences",
        user,
        json={"new_article": new_article, "price_changed": price_changed},
    )
    assert response.status_code == 200, response.text


def notifications_of(notification: Api, user: Session, article_id: str) -> list[dict[str, Any]]:
    response = notification.get("/api/v1/me/notifications", user, params={"limit": 100})
    assert response.status_code == 200
    items: list[dict[str, Any]] = response.json()["items"]
    return [n for n in items if n["article_id"] == article_id]


def processed_events(notification: Api, event_type: str) -> float:
    """Valeur de events_consumed_total{event_type, outcome="processed"} (0 si absente)."""
    text = notification.get("/metrics").text
    pattern = (
        rf'^events_consumed_total\{{[^}}]*event_type="{re.escape(event_type)}"[^}}]*\}} (\S+)$'
    )
    total = 0.0
    for line in text.splitlines():
        match = re.match(pattern, line)
        if match and 'outcome="processed"' in line:
            total += float(match.group(1))
    return total


def wait_for_notification(
    notification: Api, user: Session, article_id: str, kind: str, timeout: float
) -> tuple[dict[str, Any] | None, float]:
    def probe() -> dict[str, Any] | None:
        found = [n for n in notifications_of(notification, user, article_id) if n["type"] == kind]
        return found[0] if found else None

    return wait_until(probe, timeout)


def test_us05_ca1_interets_et_preferences_enregistres(
    notification: Api, chloe: Session, make: Factory
) -> None:
    baskets, figurines = make.category("Baskets"), make.category("Figurines")
    ids = [baskets["id"], figurines["id"]]

    interests = notification.put("/api/v1/me/interests", chloe, json={"category_ids": ids})
    preferences = notification.put(
        "/api/v1/me/preferences", chloe, json={"new_article": True, "price_changed": False}
    )

    assert interests.status_code == 200 and preferences.status_code == 200
    # Relecture : les deux catégories et les préférences choisies.
    reread_interests = notification.get("/api/v1/me/interests", chloe)
    assert reread_interests.status_code == 200
    assert sorted(reread_interests.json()["category_ids"]) == sorted(ids)
    reread_preferences = notification.get("/api/v1/me/preferences", chloe)
    assert reread_preferences.status_code == 200
    assert reread_preferences.json()["new_article"] is True
    assert reread_preferences.json()["price_changed"] is False


def test_us05_ca2_notification_nouvel_article_en_moins_de_2_secondes(
    catalog: Api,
    notification: Api,
    alice: Session,
    chloe: Session,
    alice_shop: dict[str, Any],
    make: Factory,
    record_property: Callable[[str, object], None],
) -> None:
    category = make.category("Figurines")
    set_interests(notification, chloe, [category["id"]])
    set_preferences(notification, chloe, new_article=True, price_changed=True)
    # alice s'intéresse aussi à la catégorie : sans l'exclusion du vendeur, elle serait notifiée.
    set_interests(notification, alice, [category["id"]])
    set_preferences(notification, alice, new_article=True, price_changed=True)
    payload = make.article_payload(alice_shop["id"], category["id"])

    started = time.monotonic()
    response = catalog.post("/api/v1/articles", alice, json=payload)
    assert response.status_code == 201 and response.json()["status"] == "PUBLISHED"
    article_id = response.json()["id"]
    received, _ = wait_for_notification(notification, chloe, article_id, "NEW_ARTICLE", 10)
    delay = time.monotonic() - started  # de l'envoi de la publication à la notification lisible

    assert received is not None, "aucune notification NEW_ARTICLE reçue en 10 s"
    record_property("delai_notification_secondes", f"{delay:.3f}")
    print(f"\nDélai publication -> notification lisible : {delay:.3f} s")
    assert delay < MAX_DELAY_SECONDS
    assert received["content"] == {"title": payload["title"], "price": "120.00", "currency": "EUR"}
    assert received["article_id"] == article_id
    # Le vendeur ne reçoit rien pour son propre article.
    assert notifications_of(notification, alice, article_id) == []


def test_us05_ca3_notification_changement_de_prix_selon_preference(
    catalog: Api,
    notification: Api,
    alice: Session,
    chloe: Session,
    alice_shop: dict[str, Any],
    make: Factory,
) -> None:
    category = make.category("Figurines")
    set_interests(notification, chloe, [category["id"]])
    set_preferences(notification, chloe, new_article=True, price_changed=True)
    article = make.article(alice, alice_shop["id"], category["id"])
    assert article["price"] == "120.00"

    # Type activé : PRICE_CHANGED 120 -> 95.
    catalog.put(f"/api/v1/articles/{article['id']}/price", alice, json={"price": "95.00"})
    received, _ = wait_for_notification(notification, chloe, article["id"], "PRICE_CHANGED", 10)
    assert received is not None, "aucune notification PRICE_CHANGED reçue en 10 s"
    assert received["content"] == {
        "title": article["title"],
        "old_price": "120.00",
        "new_price": "95.00",
        "currency": "EUR",
    }

    # Type désactivé : aucune notification pour le changement suivant (95 -> 80).
    set_preferences(notification, chloe, new_article=True, price_changed=False)
    processed_before = processed_events(notification, "article.price_changed")
    catalog.put(f"/api/v1/articles/{article['id']}/price", alice, json={"price": "80.00"})
    # On attend que le consommateur ait réellement traité l'événement de prix (compteur
    # events_consumed_total{outcome="processed"} de /metrics), puis on vérifie l'absence.
    reached, _ = wait_until(
        lambda: (
            True
            if processed_events(notification, "article.price_changed") > processed_before
            else None
        ),
        10,
    )
    assert reached, "l'événement article.price_changed n'a pas été traité en 10 s"
    price_changes = [
        n
        for n in notifications_of(notification, chloe, article["id"])
        if n["type"] == "PRICE_CHANGED"
    ]
    assert [n["content"]["new_price"] for n in price_changes] == ["95.00"]


def test_us05_ca4_acces_aux_notifications_protege(
    catalog: Api,
    notification: Api,
    alice: Session,
    bob: Session,
    chloe: Session,
    bob_shop: dict[str, Any],
    make: Factory,
) -> None:
    category = make.category("Figurines")
    for buyer in (chloe, alice):
        set_interests(notification, buyer, [category["id"]])
        set_preferences(notification, buyer, new_article=True, price_changed=True)
    article = make.article(bob, bob_shop["id"], category["id"])  # bob vend, chloe et alice achètent
    for buyer in (chloe, alice):
        got, _ = wait_for_notification(notification, buyer, article["id"], "NEW_ARTICLE", 10)
        assert got is not None

    for path in ("/api/v1/me/notifications", "/api/v1/me/interests", "/api/v1/me/preferences"):
        assert notification.get(path).status_code == 401, path
        assert notification.get(path, bob).status_code == 403, path  # bob n'a que seller

    # alice a le rôle buyer : elle ne voit que ses propres notifications. On compare les
    # ensembles complets d'identifiants (toutes les notifications, pas seulement cet article).
    def all_ids(user: Session) -> set[str]:
        response = notification.get("/api/v1/me/notifications", user, params={"limit": 100})
        assert response.status_code == 200
        return {n["id"] for n in response.json()["items"]}

    chloe_ids, alice_ids = all_ids(chloe), all_ids(alice)
    assert len(notifications_of(notification, chloe, article["id"])) == 1
    assert len(notifications_of(notification, alice, article["id"])) == 1
    assert chloe_ids.isdisjoint(alice_ids)
