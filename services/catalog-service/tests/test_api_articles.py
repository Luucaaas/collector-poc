"""Tests d'acceptation de l'API (US-03, US-04) : application complète sur un PostgreSQL réel,
avec un faux producteur d'événements. Les événements sur un vrai RabbitMQ sont dans
`test_rabbitmq.py`.

Chaque critère d'acceptation de `docs/03-backlog/user-stories.md` a son test `test_usNN_caN_...`.
"""

import asyncio
import re
import uuid
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import create_engine, text

from catalog.events import Event
from tests.conftest import RecordingPublisher, TokenFactory, roles_headers
from tests.event_schemas import assert_conforms

CATEGORIES = "/api/v1/categories"
SHOPS = "/api/v1/shops"
ARTICLES = "/api/v1/articles"
PHONE_TEXT = "Figurine originale Kenner de 1979, appelez-moi au 06 12 34 56 78 pour l'acheter."


def admin(make_token: TokenFactory) -> dict[str, str]:
    return roles_headers(make_token, "admin-1", "admin")


def alice(make_token: TokenFactory) -> dict[str, str]:
    return roles_headers(make_token, "alice-1", "seller", "buyer")


def bob(make_token: TokenFactory) -> dict[str, str]:
    return roles_headers(make_token, "bob-1", "seller")


def chloe(make_token: TokenFactory) -> dict[str, str]:
    return roles_headers(make_token, "chloe-1", "buyer")


def count(url: str, table: str) -> int:
    engine = create_engine(url)
    with engine.connect() as connection:
        value = connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
    engine.dispose()
    return int(value)


def assert_problem(response: httpx.Response, status: int, codes: list[str] | None = None) -> None:
    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == status
    assert body["correlation_id"] == response.headers["x-request-id"]
    if codes is not None:
        assert [error["code"] for error in body["errors"]] == codes


async def make_category(
    client: httpx.AsyncClient, make_token: TokenFactory, name: str = "Figurines"
) -> str:
    response = await client.post(CATEGORIES, json={"name": name}, headers=admin(make_token))
    assert response.status_code == 201
    return str(response.json()["id"])


async def make_shop(
    client: httpx.AsyncClient, headers: dict[str, str], name: str = "Boutique d'Alice"
) -> str:
    response = await client.post(SHOPS, json={"name": name}, headers=headers)
    assert response.status_code == 201
    return str(response.json()["id"])


def article_body(shop_id: str, category_id: str, **overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "shop_id": shop_id,
        "category_id": category_id,
        "title": "Boba Fett Kenner 1979",
        "description": "Figurine originale Kenner de 1979, complète avec son arme, très bon état.",
        "photo_urls": ["https://images.example.com/boba-1.jpg"],
        "price": "120.00",
        "shipping_fee": "8.00",
        "currency": "EUR",
    }
    body.update(overrides)
    return body


async def publish_article(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    shop_id: str,
    category_id: str,
    **overrides: Any,
) -> dict[str, Any]:
    response = await client.post(
        ARTICLES, json=article_body(shop_id, category_id, **overrides), headers=headers
    )
    assert response.status_code == 201
    created: dict[str, Any] = response.json()
    return created


# --- US-03 : publier un article --------------------------------------------------------------


async def test_us03_ca1_article_conforme_publie_evenement_et_visible_dans_le_catalogue(
    db_client: httpx.AsyncClient, make_token: TokenFactory, publisher: RecordingPublisher
) -> None:
    category_id = await make_category(db_client, make_token)
    shop_id = await make_shop(db_client, alice(make_token))
    autre_categorie = await make_category(db_client, make_token, "Baskets")
    autre = await publish_article(
        db_client, alice(make_token), shop_id, autre_categorie, title="Baskets Jordan 1985"
    )
    publisher.events.clear()

    response = await db_client.post(
        ARTICLES,
        json=article_body(shop_id, category_id),
        headers={**alice(make_token), "X-Request-ID": "req-us03-ca1"},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["status"] == "PUBLISHED"
    assert created["rejection_reasons"] == []
    assert created["price"] == "120.00"
    assert created["shipping_fee"] == "8.00"
    assert created["seller_id"] == "alice-1"
    assert created["created_at"].endswith("Z")

    # Événement article.published, conforme au contrat et corrélé à la requête.
    assert len(publisher.events) == 1
    event = publisher.events[0]
    envelope = event.envelope()
    assert_conforms(envelope)
    assert envelope["event_type"] == "article.published"
    assert envelope["correlation_id"] == "req-us03-ca1"
    assert envelope["occurred_at"] == created["created_at"]
    assert envelope["data"] == {
        "article_id": created["id"],
        "shop_id": shop_id,
        "seller_id": "alice-1",
        "category_id": category_id,
        "title": "Boba Fett Kenner 1979",
        "price": "120.00",
        "shipping_fee": "8.00",
        "currency": "EUR",
    }

    # Catalogue public (sans jeton), filtré sur la catégorie.
    listing = await db_client.get(ARTICLES, params={"category_id": category_id})
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()["items"]] == [created["id"]]
    assert listing.json()["total"] == 1
    assert autre["id"] not in [item["id"] for item in listing.json()["items"]]
    detail = await db_client.get(f"{ARTICLES}/{created['id']}")
    assert detail.status_code == 200
    assert detail.json()["photo_urls"] == ["https://images.example.com/boba-1.jpg"]


async def test_us03_ca2_coordonnees_dans_la_description_donnent_rejected_sans_evenement(
    db_client: httpx.AsyncClient,
    make_token: TokenFactory,
    publisher: RecordingPublisher,
    db_url: str,
) -> None:
    category_id = await make_category(db_client, make_token)
    shop_id = await make_shop(db_client, alice(make_token))
    cas = {
        PHONE_TEXT: ["CONTACT_PHONE"],
        "Figurine de 1979 en bon état, contact: jean.dupont@example.com pour plus de détails.": [
            "CONTACT_EMAIL"
        ],
        "Figurine Kenner complète, joignable au +33 6 12 34 56 78 ou à jean@example.com.": [
            "CONTACT_EMAIL",
            "CONTACT_PHONE",
        ],
    }
    for description, reasons in cas.items():
        created = await publish_article(
            db_client, alice(make_token), shop_id, category_id, description=description
        )
        assert created["status"] == "REJECTED"
        assert created["rejection_reasons"] == reasons

    assert publisher.events == []  # aucun événement
    assert count(db_url, "articles") == 3  # conservés pour la traçabilité
    listing = await db_client.get(ARTICLES)
    assert listing.json() == {"items": [], "total": 0}  # absents du catalogue public


async def test_us03_ca2_coordonnees_dans_le_titre_sont_aussi_controlees(
    db_client: httpx.AsyncClient, make_token: TokenFactory, publisher: RecordingPublisher
) -> None:
    category_id = await make_category(db_client, make_token)
    shop_id = await make_shop(db_client, alice(make_token))
    created = await publish_article(
        db_client, alice(make_token), shop_id, category_id, title="Vends boba, 0612345678"
    )
    assert created["status"] == "REJECTED"
    assert created["rejection_reasons"] == ["CONTACT_PHONE"]
    assert publisher.events == []


async def test_us03_ca3_article_invalide_donne_422_et_rien_n_est_enregistre(
    db_client: httpx.AsyncClient,
    make_token: TokenFactory,
    publisher: RecordingPublisher,
    db_url: str,
) -> None:
    category_id = await make_category(db_client, make_token)
    shop_id = await make_shop(db_client, alice(make_token))
    headers = alice(make_token)

    for overrides in (
        {"price": "0.00"},
        {"price": "-10.00"},
        {"photo_urls": []},
        {"title": "abc"},
        {"currency": "USD"},
    ):
        response = await db_client.post(
            ARTICLES, json=article_body(shop_id, category_id, **overrides), headers=headers
        )
        assert_problem(response, 422)

    inconnue = await db_client.post(
        ARTICLES, json=article_body(shop_id, str(uuid.uuid4())), headers=headers
    )
    assert_problem(inconnue, 422, ["CATEGORY_NOT_FOUND"])
    boutique = await db_client.post(
        ARTICLES, json=article_body(str(uuid.uuid4()), category_id), headers=headers
    )
    assert_problem(boutique, 422, ["SHOP_NOT_FOUND"])
    les_deux = await db_client.post(
        ARTICLES, json=article_body(str(uuid.uuid4()), str(uuid.uuid4())), headers=headers
    )
    assert_problem(les_deux, 422, ["SHOP_NOT_FOUND", "CATEGORY_NOT_FOUND"])

    assert count(db_url, "articles") == 0
    assert count(db_url, "article_photos") == 0
    assert publisher.events == []


async def test_us03_ca4_boutique_d_un_autre_vendeur_acheteur_et_sans_jeton(
    db_client: httpx.AsyncClient,
    make_token: TokenFactory,
    publisher: RecordingPublisher,
    db_url: str,
) -> None:
    category_id = await make_category(db_client, make_token)
    bob_shop = await make_shop(db_client, bob(make_token), "Boutique de Bob")
    body = article_body(bob_shop, category_id)

    autre_vendeur = await db_client.post(ARTICLES, json=body, headers=alice(make_token))
    assert_problem(autre_vendeur, 403)
    acheteur = await db_client.post(ARTICLES, json=body, headers=chloe(make_token))
    assert_problem(acheteur, 403)
    sans_jeton = await db_client.post(ARTICLES, json=body)
    assert_problem(sans_jeton, 401)

    assert count(db_url, "articles") == 0
    assert publisher.events == []


async def test_la_publication_a_lieu_apres_le_commit(
    db_client: httpx.AsyncClient,
    make_token: TokenFactory,
    publisher: RecordingPublisher,
    db_url: str,
) -> None:
    category_id = await make_category(db_client, make_token)
    shop_id = await make_shop(db_client, alice(make_token))
    visibles: list[int] = []

    def observer(event: Event) -> None:
        # Connexion indépendante : elle ne voit la ligne que si la transaction est validée.
        visibles.append(count(db_url, "articles"))

    publisher.on_publish = observer
    await publish_article(db_client, alice(make_token), shop_id, category_id)
    assert visibles == [1]


async def test_un_broker_indisponible_ne_change_pas_la_reponse(
    db_client: httpx.AsyncClient,
    make_token: TokenFactory,
    publisher: RecordingPublisher,
    db_url: str,
) -> None:
    category_id = await make_category(db_client, make_token)
    shop_id = await make_shop(db_client, alice(make_token))
    publisher.ok = False
    created = await publish_article(db_client, alice(make_token), shop_id, category_id)
    assert created["status"] == "PUBLISHED"
    assert count(db_url, "articles") == 1


async def test_article_rejected_invisible_pour_un_tiers_visible_du_proprietaire_et_de_l_admin(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    category_id = await make_category(db_client, make_token)
    shop_id = await make_shop(db_client, alice(make_token))
    rejected = await publish_article(
        db_client, alice(make_token), shop_id, category_id, description=PHONE_TEXT
    )
    url = f"{ARTICLES}/{rejected['id']}"

    assert_problem(await db_client.get(url), 404)  # anonyme
    assert_problem(await db_client.get(url, headers=chloe(make_token)), 404)
    assert_problem(await db_client.get(url, headers=bob(make_token)), 404)
    proprietaire = await db_client.get(url, headers=alice(make_token))
    assert proprietaire.status_code == 200
    assert proprietaire.json()["status"] == "REJECTED"
    administrateur = await db_client.get(url, headers=admin(make_token))
    assert administrateur.status_code == 200
    # Un article inexistant et un article caché donnent la même réponse.
    inconnu = await db_client.get(f"{ARTICLES}/{uuid.uuid4()}")
    assert inconnu.status_code == 404
    assert inconnu.json()["title"] == (await db_client.get(url)).json()["title"]


async def test_un_jeton_invalide_sur_une_route_publique_donne_401(
    db_client: httpx.AsyncClient,
) -> None:
    response = await db_client.get(
        ARTICLES + "/" + str(uuid.uuid4()), headers={"Authorization": "Bearer x"}
    )
    assert_problem(response, 401)


async def test_catalogue_pagination_filtres_et_tri_stable(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    figurines = await make_category(db_client, make_token, "Figurines")
    baskets = await make_category(db_client, make_token, "Baskets")
    shop_alice = await make_shop(db_client, alice(make_token))
    shop_bob = await make_shop(db_client, bob(make_token), "Boutique de Bob")
    ids = []
    for index in range(5):
        created = await publish_article(
            db_client, alice(make_token), shop_alice, figurines, title=f"Figurine numéro {index}"
        )
        ids.append(created["id"])
    sneaker = await publish_article(
        db_client, bob(make_token), shop_bob, baskets, title="Baskets Jordan 1985"
    )
    await publish_article(  # rejeté : jamais dans le catalogue
        db_client, alice(make_token), shop_alice, figurines, description=PHONE_TEXT
    )

    tout = (await db_client.get(ARTICLES)).json()
    assert tout["total"] == 6
    assert [item["id"] for item in tout["items"]] == [
        sneaker["id"],
        *reversed(ids),
    ]  # récents d'abord
    dates = [datetime.fromisoformat(item["created_at"]) for item in tout["items"]]
    assert dates == sorted(dates, reverse=True)

    page1 = (await db_client.get(ARTICLES, params={"limit": 2, "offset": 0})).json()
    page2 = (await db_client.get(ARTICLES, params={"limit": 2, "offset": 2})).json()
    page3 = (await db_client.get(ARTICLES, params={"limit": 2, "offset": 4})).json()
    assert page1["total"] == page2["total"] == page3["total"] == 6
    assert [i["id"] for p in (page1, page2, page3) for i in p["items"]] == [
        item["id"] for item in tout["items"]
    ]
    assert (await db_client.get(ARTICLES, params={"offset": 50})).json() == {
        "items": [],
        "total": 6,
    }

    par_categorie = (await db_client.get(ARTICLES, params={"category_id": baskets})).json()
    assert [i["id"] for i in par_categorie["items"]] == [sneaker["id"]]
    par_boutique = (await db_client.get(ARTICLES, params={"shop_id": shop_alice})).json()
    assert par_boutique["total"] == 5
    croise = (
        await db_client.get(ARTICLES, params={"shop_id": shop_alice, "category_id": baskets})
    ).json()
    assert croise == {"items": [], "total": 0}

    for params in ({"limit": 0}, {"limit": 101}, {"offset": -1}, {"limit": "x"}):
        assert_problem(await db_client.get(ARTICLES, params=params), 422)
    assert (await db_client.get(ARTICLES, params={"limit": 100})).status_code == 200


# --- US-04 : modifier le prix ----------------------------------------------------------------


async def published(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> tuple[dict[str, Any], str, str]:
    category_id = await make_category(client, make_token)
    shop_id = await make_shop(client, alice(make_token))
    created = await publish_article(client, alice(make_token), shop_id, category_id)
    return created, shop_id, category_id


async def test_us04_ca1_prix_modifie_historique_et_evenement(
    db_client: httpx.AsyncClient, make_token: TokenFactory, publisher: RecordingPublisher
) -> None:
    created, _, category_id = await published(db_client, make_token)
    publisher.events.clear()
    url = f"{ARTICLES}/{created['id']}"

    response = await db_client.put(
        f"{url}/price",
        json={"price": "95.00"},
        headers={**alice(make_token), "X-Request-ID": "req-us04-ca1"},
    )
    assert response.status_code == 200
    assert response.json()["price"] == "95.00"
    assert (await db_client.get(url)).json()["price"] == "95.00"

    history = await db_client.get(f"{url}/price-history", headers=alice(make_token))
    assert history.status_code == 200
    items = history.json()["items"]
    assert len(items) == 1
    assert items[0]["old_price"] == "120.00"
    assert items[0]["new_price"] == "95.00"
    assert items[0]["changed_by"] == "alice-1"
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT.*Z", items[0]["changed_at"])

    assert len(publisher.events) == 1
    envelope = publisher.events[0].envelope()
    assert_conforms(envelope)
    assert envelope["event_type"] == "article.price_changed"
    assert envelope["correlation_id"] == "req-us04-ca1"
    assert envelope["occurred_at"] == items[0]["changed_at"]
    assert envelope["data"] == {
        "article_id": created["id"],
        "seller_id": "alice-1",
        "category_id": category_id,
        "title": "Boba Fett Kenner 1979",
        "old_price": "120.00",
        "new_price": "95.00",
        "currency": "EUR",
        "changed_by": "alice-1",
    }


async def test_us04_ca2_prix_invalide_donne_422_et_le_prix_reste(
    db_client: httpx.AsyncClient,
    make_token: TokenFactory,
    publisher: RecordingPublisher,
    db_url: str,
) -> None:
    created, _, _ = await published(db_client, make_token)
    publisher.events.clear()
    url = f"{ARTICLES}/{created['id']}"
    for invalide in ("0", "-10", "0.00", "abc", 95, "1000000.01", "95.123"):
        response = await db_client.put(
            f"{url}/price", json={"price": invalide}, headers=alice(make_token)
        )
        assert_problem(response, 422)
    assert_problem(await db_client.put(f"{url}/price", json={}, headers=alice(make_token)), 422)
    assert (await db_client.get(url)).json()["price"] == "120.00"
    assert count(db_url, "price_history") == 0
    assert publisher.events == []


async def test_us04_ca3_autre_vendeur_403_sans_jeton_401_et_le_prix_reste(
    db_client: httpx.AsyncClient,
    make_token: TokenFactory,
    publisher: RecordingPublisher,
    db_url: str,
) -> None:
    created, _, _ = await published(db_client, make_token)
    publisher.events.clear()
    url = f"{ARTICLES}/{created['id']}"
    body = {"price": "95.00"}

    assert_problem(await db_client.put(f"{url}/price", json=body, headers=bob(make_token)), 403)
    assert_problem(await db_client.put(f"{url}/price", json=body, headers=chloe(make_token)), 403)
    assert_problem(await db_client.put(f"{url}/price", json=body), 401)
    assert (await db_client.get(url)).json()["price"] == "120.00"
    assert count(db_url, "price_history") == 0
    assert publisher.events == []


async def test_prix_d_un_article_inconnu_donne_404(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.put(
        f"{ARTICLES}/{uuid.uuid4()}/price", json={"price": "95.00"}, headers=alice(make_token)
    )
    assert_problem(response, 404)


async def test_prix_d_un_article_rejected_donne_409(
    db_client: httpx.AsyncClient,
    make_token: TokenFactory,
    publisher: RecordingPublisher,
    db_url: str,
) -> None:
    category_id = await make_category(db_client, make_token)
    shop_id = await make_shop(db_client, alice(make_token))
    rejected = await publish_article(
        db_client, alice(make_token), shop_id, category_id, description=PHONE_TEXT
    )
    response = await db_client.put(
        f"{ARTICLES}/{rejected['id']}/price", json={"price": "95.00"}, headers=alice(make_token)
    )
    assert_problem(response, 409)
    assert count(db_url, "price_history") == 0
    assert publisher.events == []


async def test_prix_identique_ne_cree_ni_ligne_ni_evenement(
    db_client: httpx.AsyncClient,
    make_token: TokenFactory,
    publisher: RecordingPublisher,
    db_url: str,
) -> None:
    created, _, _ = await published(db_client, make_token)
    publisher.events.clear()
    url = f"{ARTICLES}/{created['id']}/price"
    for same in ("120.00", "120", "120.0"):
        response = await db_client.put(url, json={"price": same}, headers=alice(make_token))
        assert response.status_code == 200
        assert response.json()["price"] == "120.00"
    assert count(db_url, "price_history") == 0
    assert publisher.events == []

    # Idempotence : la même requête rejouée ne change plus rien après la première application.
    for _ in range(2):
        await db_client.put(url, json={"price": "95.00"}, headers=alice(make_token))
    assert count(db_url, "price_history") == 1
    assert len(publisher.events) == 1


async def test_historique_chronologique_proprietaire_et_admin_seulement(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    created, _, _ = await published(db_client, make_token)
    url = f"{ARTICLES}/{created['id']}"
    for price in ("100.00", "90.50", "99.99"):
        assert (
            await db_client.put(f"{url}/price", json={"price": price}, headers=alice(make_token))
        ).status_code == 200

    history = await db_client.get(f"{url}/price-history", headers=alice(make_token))
    assert [(i["old_price"], i["new_price"]) for i in history.json()["items"]] == [
        ("120.00", "100.00"),
        ("100.00", "90.50"),
        ("90.50", "99.99"),
    ]
    assert history.json()["total"] == 3
    assert (
        await db_client.get(f"{url}/price-history", headers=admin(make_token))
    ).status_code == 200
    assert_problem(await db_client.get(f"{url}/price-history", headers=bob(make_token)), 403)
    assert_problem(await db_client.get(f"{url}/price-history", headers=chloe(make_token)), 403)
    assert_problem(await db_client.get(f"{url}/price-history"), 401)
    assert_problem(
        await db_client.get(f"{ARTICLES}/{uuid.uuid4()}/price-history", headers=alice(make_token)),
        404,
    )


async def test_metriques_metier_exposees(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    created, shop_id, category_id = await published(db_client, make_token)
    await publish_article(
        db_client, alice(make_token), shop_id, category_id, description=PHONE_TEXT
    )
    await db_client.put(
        f"{ARTICLES}/{created['id']}/price", json={"price": "95.00"}, headers=alice(make_token)
    )
    metrics = (await db_client.get("/metrics")).text
    assert "articles_published_total 1.0" in metrics
    assert 'articles_rejected_total{reason="CONTACT_PHONE"} 1.0' in metrics
    assert "price_changes_total 1.0" in metrics


async def test_frais_de_port_obligatoires_422_missing_et_devise_par_defaut(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    category_id = await make_category(db_client, make_token)
    shop_id = await make_shop(db_client, alice(make_token))
    body = article_body(shop_id, category_id)
    del body["shipping_fee"]
    response = await db_client.post(ARTICLES, json=body, headers=alice(make_token))
    assert_problem(response, 422, ["MISSING"])
    assert count(db_url, "articles") == 0

    body = article_body(shop_id, category_id)
    del body["currency"]
    response = await db_client.post(ARTICLES, json=body, headers=alice(make_token))
    assert response.status_code == 201
    assert response.json()["currency"] == "EUR"


async def test_tiers_sur_article_non_publie_404_sur_prix_et_historique(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    category_id = await make_category(db_client, make_token)
    shop_id = await make_shop(db_client, alice(make_token))
    rejected = await publish_article(
        db_client, alice(make_token), shop_id, category_id, description=PHONE_TEXT
    )
    url = f"{ARTICLES}/{rejected['id']}"
    body = {"price": "95.00"}

    # Un tiers (vendeur, acheteur) ne doit pas deviner l'existence de l'article.
    for headers in (bob(make_token), chloe(make_token)):
        assert_problem(await db_client.get(f"{url}/price-history", headers=headers), 404)
    assert_problem(await db_client.put(f"{url}/price", json=body, headers=bob(make_token)), 404)
    assert_problem(await db_client.put(f"{url}/price", json=body, headers=chloe(make_token)), 403)
    # chloe n'a pas le rôle seller : le 403 de rôle passe avant, il ne révèle rien sur l'article.

    # Le propriétaire et l'admin gardent leurs droits.
    assert (
        await db_client.get(f"{url}/price-history", headers=alice(make_token))
    ).status_code == 200
    assert (
        await db_client.get(f"{url}/price-history", headers=admin(make_token))
    ).status_code == 200
    assert_problem(await db_client.put(f"{url}/price", json=body, headers=alice(make_token)), 409)


async def test_tiers_sur_article_publie_garde_403(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    created, _, _ = await published(db_client, make_token)
    url = f"{ARTICLES}/{created['id']}"
    assert_problem(await db_client.get(f"{url}/price-history", headers=bob(make_token)), 403)
    assert_problem(
        await db_client.put(f"{url}/price", json={"price": "95.00"}, headers=bob(make_token)), 403
    )


async def test_deux_modifications_de_prix_simultanees_restent_coherentes(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    created, _, _ = await published(db_client, make_token)
    url = f"{ARTICLES}/{created['id']}"
    responses = await asyncio.gather(
        db_client.put(f"{url}/price", json={"price": "95.00"}, headers=alice(make_token)),
        db_client.put(f"{url}/price", json={"price": "100.00"}, headers=alice(make_token)),
    )
    assert [r.status_code for r in responses] == [200, 200]

    items = (await db_client.get(f"{url}/price-history", headers=alice(make_token))).json()["items"]
    assert len(items) == 2
    assert items[0]["old_price"] == "120.00"
    assert items[1]["old_price"] == items[0]["new_price"]  # chaîne ininterrompue grâce au verrou
    assert {items[0]["new_price"], items[1]["new_price"]} == {"95.00", "100.00"}
    assert (await db_client.get(url)).json()["price"] == items[1]["new_price"]
