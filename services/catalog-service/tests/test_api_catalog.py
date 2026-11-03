"""Tests d'acceptation de l'API (US-01, US-02) : application complète sur un PostgreSQL réel.

Chaque critère d'acceptation de `docs/03-backlog/user-stories.md` a son test `test_usNN_caN_...`.
"""

import asyncio

import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from tests.conftest import TokenFactory, roles_headers

CATEGORIES = "/api/v1/categories"
SHOPS = "/api/v1/shops"


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


# --- US-01 : créer une catégorie -------------------------------------------------------------


async def test_us01_ca1_admin_cree_une_categorie_visible_dans_la_liste_publique(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.post(
        CATEGORIES, json={"name": "Figurines Star Wars"}, headers=admin(make_token)
    )
    assert response.status_code == 201
    created = response.json()
    assert created["slug"] == "figurines-star-wars"
    assert created["name"] == "Figurines Star Wars"
    assert created["created_at"].endswith("Z")

    listing = await db_client.get(CATEGORIES)  # sans jeton
    assert listing.status_code == 200
    assert listing.json()["items"] == [created]
    assert listing.json()["total"] == 1


async def test_us01_ca2_doublon_sans_casse_donne_409_et_nom_trop_court_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    headers = admin(make_token)
    assert (
        await db_client.post(CATEGORIES, json={"name": "Baskets"}, headers=headers)
    ).status_code == 201

    duplicate = await db_client.post(CATEGORIES, json={"name": "baskets"}, headers=headers)
    assert_problem(duplicate, 409, ["NAME_ALREADY_USED"])

    too_short = await db_client.post(CATEGORIES, json={"name": "B"}, headers=headers)
    assert_problem(too_short, 422)
    assert count(db_url, "categories") == 1


async def test_us01_ca3_sans_jeton_401_et_vendeur_seul_403(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    anonymous = await db_client.post(CATEGORIES, json={"name": "Baskets"})
    assert_problem(anonymous, 401)
    forbidden = await db_client.post(CATEGORIES, json={"name": "Baskets"}, headers=bob(make_token))
    assert_problem(forbidden, 403)
    assert count(db_url, "categories") == 0


async def test_categories_triees_par_nom_sans_tenir_compte_de_la_casse(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    for name in ["vinyles", "Baskets", "Cartes Pokémon"]:
        await db_client.post(CATEGORIES, json={"name": name}, headers=admin(make_token))
    names = [item["name"] for item in (await db_client.get(CATEGORIES)).json()["items"]]
    assert names == ["Baskets", "Cartes Pokémon", "vinyles"]


async def test_categorie_champ_inconnu_donne_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.post(
        CATEGORIES, json={"name": "Baskets", "slug": "pirate"}, headers=admin(make_token)
    )
    assert_problem(response, 422)


async def test_categorie_nom_sans_lettre_ni_chiffre_donne_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.post(CATEGORIES, json={"name": "!!"}, headers=admin(make_token))
    assert_problem(response, 422, ["NAME_INVALID"])


async def test_categorie_nom_de_60_caracteres_accepte_et_61_refuse(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    ok = await db_client.post(CATEGORIES, json={"name": "a" * 60}, headers=admin(make_token))
    assert ok.status_code == 201
    too_long = await db_client.post(CATEGORIES, json={"name": "b" * 61}, headers=admin(make_token))
    assert_problem(too_long, 422)


async def test_categorie_de_meme_slug_donne_409(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    headers = admin(make_token)
    await db_client.post(CATEGORIES, json={"name": "Baskets"}, headers=headers)
    response = await db_client.post(CATEGORIES, json={"name": "Baskets!"}, headers=headers)
    assert_problem(response, 409)
    assert count(db_url, "categories") == 1


async def test_non_authentifie_est_refuse_avant_la_validation_du_corps(
    db_client: httpx.AsyncClient,
) -> None:
    response = await db_client.post(CATEGORIES, json={"nom": "mauvais champ"})
    assert response.status_code == 401


async def test_categorie_de_60_ligatures_donne_un_slug_de_120_caracteres_et_201(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.post(CATEGORIES, json={"name": "œ" * 60}, headers=admin(make_token))
    assert response.status_code == 201
    assert response.json()["slug"] == "oe" * 60


async def test_categorie_dont_le_slug_depasse_120_caracteres_donne_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    response = await db_client.post(CATEGORIES, json={"name": "ﬃ" * 60}, headers=admin(make_token))
    assert_problem(response, 422, ["NAME_INVALID"])
    assert count(db_url, "categories") == 0


async def test_collision_de_slug_garde_le_code_name_already_used_et_son_detail(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    await db_client.post(CATEGORIES, json={"name": "Baskets"}, headers=admin(make_token))
    response = await db_client.post(
        CATEGORIES, json={"name": "Baskets!"}, headers=admin(make_token)
    )
    assert_problem(response, 409, ["NAME_ALREADY_USED"])
    assert response.json()["detail"] == "Nom déjà utilisé ou trop proche d'un nom existant."


# --- US-02 : créer une boutique --------------------------------------------------------------


async def test_us02_ca1_vendeur_cree_une_boutique_a_son_nom_consultable_publiquement(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.post(
        SHOPS,
        json={"name": "Jouets des années 80", "description": "Figurines et jeux d'époque"},
        headers=alice(make_token),
    )
    assert response.status_code == 201
    shop = response.json()
    assert shop["owner_id"] == "alice-1"
    assert shop["seller_type"] == "INDIVIDUAL"

    page = await db_client.get(f"{SHOPS}/{shop['id']}")  # sans jeton
    assert page.status_code == 200
    assert page.json() == shop


@pytest.mark.parametrize(
    ("description", "code"),
    [
        ("Écrivez à alice@example.com", "CONTACT_EMAIL"),
        ("Appelez le 06 12 34 56 78", "CONTACT_PHONE"),
        ("Ou le +33 6 12 34 56 78", "CONTACT_PHONE"),
    ],
)
async def test_us02_ca2_coordonnees_dans_la_description_donnent_422_sans_rien_enregistrer(
    db_client: httpx.AsyncClient,
    make_token: TokenFactory,
    db_url: str,
    description: str,
    code: str,
) -> None:
    response = await db_client.post(
        SHOPS, json={"name": "Jouets", "description": description}, headers=alice(make_token)
    )
    assert_problem(response, 422, [code])
    assert response.json()["errors"][0]["field"] == "description"
    assert count(db_url, "shops") == 0


async def test_us02_ca3_sans_jeton_401_et_acheteur_seul_403(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    assert_problem(await db_client.post(SHOPS, json={"name": "Jouets"}), 401)
    forbidden = await db_client.post(SHOPS, json={"name": "Jouets"}, headers=chloe(make_token))
    assert_problem(forbidden, 403)
    assert count(db_url, "shops") == 0


async def test_boutique_coordonnees_dans_le_nom_donnent_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    response = await db_client.post(
        SHOPS, json={"name": "Chez 0612345678"}, headers=alice(make_token)
    )
    assert_problem(response, 422, ["CONTACT_PHONE"])
    assert response.json()["errors"][0]["field"] == "name"
    assert count(db_url, "shops") == 0


async def test_boutique_nom_deja_utilise_sans_casse_donne_409_meme_pour_un_autre_vendeur(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    assert (
        await db_client.post(SHOPS, json={"name": "Retro Toys"}, headers=alice(make_token))
    ).status_code == 201
    response = await db_client.post(SHOPS, json={"name": "RETRO toys"}, headers=bob(make_token))
    assert_problem(response, 409, ["NAME_ALREADY_USED"])
    assert count(db_url, "shops") == 1


@pytest.mark.parametrize("name", ["ab", "x" * 61])
async def test_boutique_nom_hors_bornes_donne_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory, name: str
) -> None:
    response = await db_client.post(SHOPS, json={"name": name}, headers=alice(make_token))
    assert_problem(response, 422)


async def test_boutique_champ_inconnu_donne_422_et_seller_type_n_est_pas_modifiable(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.post(
        SHOPS, json={"name": "Jouets", "seller_type": "PROFESSIONAL"}, headers=alice(make_token)
    )
    assert_problem(response, 422)


async def test_boutique_owner_id_dans_le_corps_donne_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    response = await db_client.post(
        SHOPS, json={"name": "Jouets", "owner_id": "bob-1"}, headers=alice(make_token)
    )
    assert_problem(response, 422)
    assert count(db_url, "shops") == 0


async def test_boutique_description_vide_est_enregistree_null(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.post(
        SHOPS, json={"name": "Jouets", "description": "   "}, headers=alice(make_token)
    )
    assert response.status_code == 201
    assert response.json()["description"] is None
    page = await db_client.get(f"{SHOPS}/{response.json()['id']}")
    assert page.json()["description"] is None


async def test_boutique_inconnue_donne_404(db_client: httpx.AsyncClient) -> None:
    response = await db_client.get(f"{SHOPS}/9c4e7f10-2b3a-4d5e-8f6a-7b8c9d0e1f23")
    assert_problem(response, 404)


async def test_shops_me_ne_renvoie_que_les_boutiques_de_l_utilisateur(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    await db_client.post(SHOPS, json={"name": "Boutique A"}, headers=alice(make_token))
    await db_client.post(SHOPS, json={"name": "Boutique B"}, headers=alice(make_token))
    await db_client.post(SHOPS, json={"name": "Boutique Bob"}, headers=bob(make_token))

    mine = (await db_client.get(f"{SHOPS}/me", headers=alice(make_token))).json()
    assert [shop["name"] for shop in mine["items"]] == ["Boutique A", "Boutique B"]
    assert mine["total"] == 2
    assert {shop["owner_id"] for shop in mine["items"]} == {"alice-1"}

    nobody = await db_client.get(f"{SHOPS}/me", headers=roles_headers(make_token, "dan", "seller"))
    assert nobody.json() == {"items": [], "total": 0}


async def test_shops_me_exige_le_role_seller(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    assert_problem(await db_client.get(f"{SHOPS}/me"), 401)
    assert_problem(await db_client.get(f"{SHOPS}/me", headers=chloe(make_token)), 403)


# --- Garanties de la base --------------------------------------------------------------------


async def test_deux_creations_concurrentes_du_meme_nom_donnent_un_201_et_un_409(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    headers = admin(make_token)
    responses = await asyncio.gather(
        *(
            db_client.post(CATEGORIES, json={"name": name}, headers=headers)
            for name in ("Vinyles", "vinyles")
        )
    )
    assert sorted(r.status_code for r in responses) == [201, 409]
    assert count(db_url, "categories") == 1


async def test_deux_boutiques_concurrentes_du_meme_nom_donnent_un_201_et_un_409(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    responses = await asyncio.gather(
        db_client.post(SHOPS, json={"name": "Retro"}, headers=alice(make_token)),
        db_client.post(SHOPS, json={"name": "RETRO"}, headers=bob(make_token)),
    )
    assert sorted(r.status_code for r in responses) == [201, 409]
    assert count(db_url, "shops") == 1


def test_la_base_refuse_un_doublon_de_nom_et_un_type_de_vendeur_autre_qu_individual(
    db_url: str,
) -> None:
    engine = create_engine(db_url)
    insert_shop = text(
        "INSERT INTO shops (id, owner_id, name, seller_type) "
        "VALUES (gen_random_uuid(), 'o', :name, :type)"
    )
    with engine.begin() as connection:
        connection.execute(insert_shop, {"name": "Retro", "type": "INDIVIDUAL"})
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(insert_shop, {"name": "rETRO", "type": "INDIVIDUAL"})
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(insert_shop, {"name": "Autre", "type": "PROFESSIONAL"})
    engine.dispose()
    assert count(db_url, "shops") == 1


def test_la_base_refuse_deux_categories_de_meme_nom_meme_avec_des_slugs_differents(
    db_url: str,
) -> None:
    """L'index `lower(name)` agit seul : le slug unique ne le masque pas."""
    engine = create_engine(db_url)
    insert = text(
        "INSERT INTO categories (id, name, slug) VALUES (gen_random_uuid(), :name, :slug)"
    )
    with engine.begin() as connection:
        connection.execute(insert, {"name": "Baskets", "slug": "baskets-1"})
    with (
        pytest.raises(IntegrityError, match="uq_categories_name_lower"),
        engine.begin() as connection,
    ):
        connection.execute(insert, {"name": "BASKETS", "slug": "baskets-2"})
    engine.dispose()
    assert count(db_url, "categories") == 1
