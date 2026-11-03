"""Acceptation de US-05 côté API (CA1 et CA4) et règles de `/me/*`, sur un vrai PostgreSQL.

CA2 et CA3 traversent RabbitMQ : ils sont dans `test_rabbitmq.py`.
"""

import asyncio
import json
import uuid
from typing import Any

import httpx
import pytest
from sqlalchemy import create_engine, text

from tests.conftest import TokenFactory, roles_headers
from tests.factory import BASKETS, FIGURINES

INTERESTS = "/api/v1/me/interests"
PREFERENCES = "/api/v1/me/preferences"
NOTIFICATIONS = "/api/v1/me/notifications"


def chloe(make_token: TokenFactory) -> dict[str, str]:
    return roles_headers(make_token, "chloe", "buyer")


def alice(make_token: TokenFactory) -> dict[str, str]:
    return roles_headers(make_token, "alice", "seller", "buyer")


def bob(make_token: TokenFactory) -> dict[str, str]:
    return roles_headers(make_token, "bob", "seller")


def seed_notifications(db_url: str, user_id: str, count: int, **overrides: Any) -> list[str]:
    """Insère `count` notifications, de la plus ancienne à la plus récente (une par minute)."""
    ids = []
    engine = create_engine(db_url)
    with engine.begin() as connection:
        for index in range(count):
            notification_id = str(uuid.uuid4())
            ids.append(notification_id)
            connection.execute(
                text(
                    "INSERT INTO notifications (id, user_id, type, article_id, content, "
                    "source_event_id, created_at) VALUES (:id, :user_id, 'NEW_ARTICLE', "
                    ":article_id, CAST(:content AS jsonb), :event_id, "
                    "now() - make_interval(mins => :age))"
                ),
                {
                    "id": notification_id,
                    "user_id": user_id,
                    "article_id": str(uuid.uuid4()),
                    "content": json.dumps(
                        {"title": f"Article {index}", "price": "10.00", "currency": "EUR"}
                    ),
                    "event_id": str(uuid.uuid4()),
                    "age": count - index,
                    **overrides,
                },
            )
    engine.dispose()
    return ids


# --- US-05, critères d'acceptation ------------------------------------------------------------


async def test_us05_ca1_chloe_declare_ses_interets_et_desactive_les_prix(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    headers = chloe(make_token)
    interests = await db_client.put(
        INTERESTS, json={"category_ids": [BASKETS, FIGURINES]}, headers=headers
    )
    preferences = await db_client.put(
        PREFERENCES, json={"new_article": True, "price_changed": False}, headers=headers
    )
    assert interests.status_code == 200
    assert preferences.status_code == 200

    reread_interests = await db_client.get(INTERESTS, headers=headers)
    reread_preferences = await db_client.get(PREFERENCES, headers=headers)
    assert sorted(reread_interests.json()["category_ids"]) == sorted([BASKETS, FIGURINES])
    assert reread_preferences.json() == {"new_article": True, "price_changed": False}


@pytest.mark.parametrize("path", [INTERESTS, PREFERENCES, NOTIFICATIONS])
async def test_us05_ca4_sans_jeton_401_et_sans_role_buyer_403(
    db_client: httpx.AsyncClient, make_token: TokenFactory, path: str
) -> None:
    assert (await db_client.get(path)).status_code == 401
    forbidden = await db_client.get(path, headers=bob(make_token))
    assert forbidden.status_code == 403
    assert forbidden.headers["content-type"].startswith("application/problem+json")


async def test_us05_ca4_ecritures_sans_jeton_401_et_sans_role_buyer_403(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    for path, body in (
        (INTERESTS, {"category_ids": [FIGURINES]}),
        (PREFERENCES, {"new_article": True, "price_changed": True}),
    ):
        assert (await db_client.put(path, json=body)).status_code == 401
        assert (await db_client.put(path, json=body, headers=bob(make_token))).status_code == 403


async def test_us05_ca4_alice_ne_voit_que_ses_propres_notifications(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    chloe_ids = seed_notifications(db_url, "chloe", 3)
    alice_ids = seed_notifications(db_url, "alice", 2)

    for headers, expected in ((chloe(make_token), chloe_ids), (alice(make_token), alice_ids)):
        body = (await db_client.get(NOTIFICATIONS, headers=headers)).json()
        assert body["total"] == len(expected)
        assert {item["id"] for item in body["items"]} == set(expected)


# --- Règles de /me/interests et /me/preferences ------------------------------------------------


async def test_sans_interets_la_liste_est_vide(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.get(INTERESTS, headers=chloe(make_token))
    assert response.status_code == 200
    assert response.json() == {"category_ids": []}


async def test_put_interests_remplace_la_liste_entiere(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    headers = chloe(make_token)
    await db_client.put(INTERESTS, json={"category_ids": [BASKETS, FIGURINES]}, headers=headers)
    second = await db_client.put(INTERESTS, json={"category_ids": [FIGURINES]}, headers=headers)
    assert second.json() == {"category_ids": [FIGURINES]}
    assert (await db_client.get(INTERESTS, headers=headers)).json() == {"category_ids": [FIGURINES]}
    cleared = await db_client.put(INTERESTS, json={"category_ids": []}, headers=headers)
    assert cleared.json() == {"category_ids": []}


async def test_put_interests_dedoublonne_les_identifiants(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.put(
        INTERESTS,
        json={"category_ids": [FIGURINES, FIGURINES, FIGURINES.upper()]},
        headers=chloe(make_token),
    )
    assert response.status_code == 200
    assert response.json() == {"category_ids": [FIGURINES]}


async def test_vingt_categories_distinctes_sont_acceptees_vingt_et_une_donnent_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    headers = chloe(make_token)
    ids = [str(uuid.uuid4()) for _ in range(21)]
    accepted = await db_client.put(INTERESTS, json={"category_ids": ids[:20]}, headers=headers)
    refused = await db_client.put(INTERESTS, json={"category_ids": ids}, headers=headers)
    assert accepted.status_code == 200
    assert refused.status_code == 422
    assert refused.headers["content-type"].startswith("application/problem+json")
    assert refused.json()["errors"] == [{"field": "category_ids", "code": "TOO_MANY_CATEGORIES"}]
    # la liste précédente n'est pas touchée par un remplacement refusé
    stored = (await db_client.get(INTERESTS, headers=headers)).json()["category_ids"]
    assert sorted(stored) == sorted(ids[:20])


async def test_21_identifiants_dont_un_doublon_font_20_categories_et_sont_acceptes(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    ids = [str(uuid.uuid4()) for _ in range(20)]
    response = await db_client.put(
        INTERESTS, json={"category_ids": [*ids, ids[0]]}, headers=chloe(make_token)
    )
    assert response.status_code == 200
    assert sorted(response.json()["category_ids"]) == sorted(ids)


async def test_une_liste_brute_demesuree_donne_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    ids = [str(uuid.uuid4())] * 201
    response = await db_client.put(INTERESTS, json={"category_ids": ids}, headers=chloe(make_token))
    assert response.status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        {"category_ids": ["pas-un-uuid"]},
        {"category_ids": "x"},
        {"category_ids": [FIGURINES], "autre": 1},
        {},
    ],
)
async def test_put_interests_refuse_un_corps_invalide(
    db_client: httpx.AsyncClient, make_token: TokenFactory, body: dict[str, Any]
) -> None:
    response = await db_client.put(INTERESTS, json=body, headers=chloe(make_token))
    assert response.status_code == 422


async def test_une_categorie_inconnue_du_catalogue_est_acceptee(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    """Le format est vérifié, pas l'existence : le service n'appelle pas le catalogue."""
    unknown = str(uuid.uuid4())
    response = await db_client.put(
        INTERESTS, json={"category_ids": [unknown]}, headers=chloe(make_token)
    )
    assert response.json() == {"category_ids": [unknown]}


async def test_preferences_par_defaut_les_deux_types_sont_actifs(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.get(PREFERENCES, headers=chloe(make_token))
    assert response.status_code == 200
    assert response.json() == {"new_article": True, "price_changed": True}


async def test_put_preferences_est_idempotent_et_modifiable(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    headers = chloe(make_token)
    for body in (
        {"new_article": False, "price_changed": False},
        {"new_article": False, "price_changed": False},
        {"new_article": True, "price_changed": False},
    ):
        response = await db_client.put(PREFERENCES, json=body, headers=headers)
        assert response.status_code == 200
        assert response.json() == body
        assert (await db_client.get(PREFERENCES, headers=headers)).json() == body


@pytest.mark.parametrize(
    "body",
    [
        {"new_article": True},
        {"new_article": "oui", "price_changed": True},
        {"new_article": 1, "price_changed": True},
        {"new_article": True, "price_changed": True, "email": True},
    ],
)
async def test_put_preferences_refuse_un_corps_invalide(
    db_client: httpx.AsyncClient, make_token: TokenFactory, body: dict[str, Any]
) -> None:
    response = await db_client.put(PREFERENCES, json=body, headers=chloe(make_token))
    assert response.status_code == 422


async def test_interets_et_preferences_sont_propres_a_chaque_acheteur(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    await db_client.put(INTERESTS, json={"category_ids": [FIGURINES]}, headers=chloe(make_token))
    await db_client.put(
        PREFERENCES, json={"new_article": False, "price_changed": False}, headers=chloe(make_token)
    )
    assert (await db_client.get(INTERESTS, headers=alice(make_token))).json() == {
        "category_ids": []
    }
    assert (await db_client.get(PREFERENCES, headers=alice(make_token))).json() == {
        "new_article": True,
        "price_changed": True,
    }


async def test_deux_remplacements_simultanes_ne_donnent_pas_d_erreur(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    headers = chloe(make_token)
    ids = [str(uuid.uuid4()) for _ in range(6)]
    results = await asyncio.gather(
        *(
            db_client.put(INTERESTS, json={"category_ids": ids[: 2 + n % 4]}, headers=headers)
            for n in range(12)
        )
    )
    assert {r.status_code for r in results} == {200}
    stored = (await db_client.get(INTERESTS, headers=headers)).json()["category_ids"]
    assert sorted(stored) in [sorted(ids[:k]) for k in range(2, 6)]


# --- GET /me/notifications ---------------------------------------------------------------------


async def test_notifications_vides_pour_un_nouvel_acheteur(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.get(NOTIFICATIONS, headers=chloe(make_token))
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


async def test_notifications_de_la_plus_recente_a_la_plus_ancienne_avec_pagination(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    ids = seed_notifications(db_url, "chloe", 5)  # ids[4] est la plus récente
    headers = chloe(make_token)

    page_1 = (await db_client.get(NOTIFICATIONS, params={"limit": 2}, headers=headers)).json()
    page_2 = (
        await db_client.get(NOTIFICATIONS, params={"limit": 2, "offset": 2}, headers=headers)
    ).json()
    page_3 = (
        await db_client.get(NOTIFICATIONS, params={"limit": 2, "offset": 4}, headers=headers)
    ).json()
    beyond = (await db_client.get(NOTIFICATIONS, params={"offset": 50}, headers=headers)).json()

    assert [i["id"] for i in page_1["items"]] == [ids[4], ids[3]]
    assert [i["id"] for i in page_2["items"]] == [ids[2], ids[1]]
    assert [i["id"] for i in page_3["items"]] == [ids[0]]
    assert {p["total"] for p in (page_1, page_2, page_3, beyond)} == {5}
    assert beyond["items"] == []


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"limit": "x"}])
async def test_pagination_invalide_donne_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory, params: dict[str, Any]
) -> None:
    response = await db_client.get(NOTIFICATIONS, params=params, headers=chloe(make_token))
    assert response.status_code == 422


async def test_une_notification_expose_type_article_contenu_et_date(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    (notification_id,) = seed_notifications(db_url, "chloe", 1)
    (item,) = (await db_client.get(NOTIFICATIONS, headers=chloe(make_token))).json()["items"]
    assert set(item) == {"id", "type", "article_id", "content", "created_at"}
    assert item["id"] == notification_id
    assert item["type"] == "NEW_ARTICLE"
    assert item["content"] == {"title": "Article 0", "price": "10.00", "currency": "EUR"}
    assert item["created_at"].endswith(("Z", "+00:00"))
