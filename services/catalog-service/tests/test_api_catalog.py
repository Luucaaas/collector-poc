"""API acceptance tests (US-01, US-02): complete application on a real PostgreSQL.

Each acceptance criterion of `docs/03-backlog/user-stories.md` has its `test_usNN_caN_...` test.
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


# --- US-01: create a category ----------------------------------------------------------------


async def test_us01_ca1_admin_creates_a_category_visible_in_the_public_list(
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

    listing = await db_client.get(CATEGORIES)  # without a token
    assert listing.status_code == 200
    assert listing.json()["items"] == [created]
    assert listing.json()["total"] == 1


async def test_us01_ca2_case_insensitive_duplicate_gives_409_and_too_short_name_422(
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


async def test_us01_ca3_no_token_401_and_seller_only_403(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    anonymous = await db_client.post(CATEGORIES, json={"name": "Baskets"})
    assert_problem(anonymous, 401)
    forbidden = await db_client.post(CATEGORIES, json={"name": "Baskets"}, headers=bob(make_token))
    assert_problem(forbidden, 403)
    assert count(db_url, "categories") == 0


async def test_categories_sorted_by_name_ignoring_case(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    for name in ["vinyles", "Baskets", "Cartes Pokémon"]:
        await db_client.post(CATEGORIES, json={"name": name}, headers=admin(make_token))
    names = [item["name"] for item in (await db_client.get(CATEGORIES)).json()["items"]]
    assert names == ["Baskets", "Cartes Pokémon", "vinyles"]


async def test_category_unknown_field_gives_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.post(
        CATEGORIES, json={"name": "Baskets", "slug": "pirate"}, headers=admin(make_token)
    )
    assert_problem(response, 422)


async def test_category_name_without_letter_or_digit_gives_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.post(CATEGORIES, json={"name": "!!"}, headers=admin(make_token))
    assert_problem(response, 422, ["NAME_INVALID"])


async def test_category_name_of_60_characters_accepted_and_61_rejected(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    ok = await db_client.post(CATEGORIES, json={"name": "a" * 60}, headers=admin(make_token))
    assert ok.status_code == 201
    too_long = await db_client.post(CATEGORIES, json={"name": "b" * 61}, headers=admin(make_token))
    assert_problem(too_long, 422)


async def test_category_with_same_slug_gives_409(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    headers = admin(make_token)
    await db_client.post(CATEGORIES, json={"name": "Baskets"}, headers=headers)
    response = await db_client.post(CATEGORIES, json={"name": "Baskets!"}, headers=headers)
    assert_problem(response, 409)
    assert count(db_url, "categories") == 1


async def test_unauthenticated_is_rejected_before_body_validation(
    db_client: httpx.AsyncClient,
) -> None:
    response = await db_client.post(CATEGORIES, json={"unknown": "bad field"})
    assert response.status_code == 401


async def test_category_of_60_ligatures_gives_a_120_character_slug_and_201(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.post(CATEGORIES, json={"name": "œ" * 60}, headers=admin(make_token))
    assert response.status_code == 201
    assert response.json()["slug"] == "oe" * 60


async def test_category_whose_slug_exceeds_120_characters_gives_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    response = await db_client.post(CATEGORIES, json={"name": "ﬃ" * 60}, headers=admin(make_token))
    assert_problem(response, 422, ["NAME_INVALID"])
    assert count(db_url, "categories") == 0


async def test_slug_collision_keeps_the_name_already_used_code_and_its_detail(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    await db_client.post(CATEGORIES, json={"name": "Baskets"}, headers=admin(make_token))
    response = await db_client.post(
        CATEGORIES, json={"name": "Baskets!"}, headers=admin(make_token)
    )
    assert_problem(response, 409, ["NAME_ALREADY_USED"])
    assert response.json()["detail"] == "Nom déjà utilisé ou trop proche d'un nom existant."


# --- US-02: create a shop --------------------------------------------------------------------


async def test_us02_ca1_seller_creates_a_shop_in_their_name_publicly_viewable(
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

    page = await db_client.get(f"{SHOPS}/{shop['id']}")  # without a token
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
async def test_us02_ca2_contact_details_in_the_description_give_422_and_nothing_is_saved(
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


async def test_us02_ca3_no_token_401_and_buyer_only_403(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    assert_problem(await db_client.post(SHOPS, json={"name": "Jouets"}), 401)
    forbidden = await db_client.post(SHOPS, json={"name": "Jouets"}, headers=chloe(make_token))
    assert_problem(forbidden, 403)
    assert count(db_url, "shops") == 0


async def test_shop_contact_details_in_the_name_give_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    response = await db_client.post(
        SHOPS, json={"name": "Chez 0612345678"}, headers=alice(make_token)
    )
    assert_problem(response, 422, ["CONTACT_PHONE"])
    assert response.json()["errors"][0]["field"] == "name"
    assert count(db_url, "shops") == 0


async def test_shop_name_already_used_ignoring_case_gives_409_even_for_another_seller(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    assert (
        await db_client.post(SHOPS, json={"name": "Retro Toys"}, headers=alice(make_token))
    ).status_code == 201
    response = await db_client.post(SHOPS, json={"name": "RETRO toys"}, headers=bob(make_token))
    assert_problem(response, 409, ["NAME_ALREADY_USED"])
    assert count(db_url, "shops") == 1


@pytest.mark.parametrize("name", ["ab", "x" * 61])
async def test_shop_name_out_of_bounds_gives_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory, name: str
) -> None:
    response = await db_client.post(SHOPS, json={"name": name}, headers=alice(make_token))
    assert_problem(response, 422)


async def test_shop_unknown_field_gives_422_and_seller_type_is_not_editable(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.post(
        SHOPS, json={"name": "Jouets", "seller_type": "PROFESSIONAL"}, headers=alice(make_token)
    )
    assert_problem(response, 422)


async def test_shop_owner_id_in_the_body_gives_422(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    response = await db_client.post(
        SHOPS, json={"name": "Jouets", "owner_id": "bob-1"}, headers=alice(make_token)
    )
    assert_problem(response, 422)
    assert count(db_url, "shops") == 0


async def test_shop_empty_description_is_saved_as_null(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await db_client.post(
        SHOPS, json={"name": "Jouets", "description": "   "}, headers=alice(make_token)
    )
    assert response.status_code == 201
    assert response.json()["description"] is None
    page = await db_client.get(f"{SHOPS}/{response.json()['id']}")
    assert page.json()["description"] is None


async def test_unknown_shop_gives_404(db_client: httpx.AsyncClient) -> None:
    response = await db_client.get(f"{SHOPS}/9c4e7f10-2b3a-4d5e-8f6a-7b8c9d0e1f23")
    assert_problem(response, 404)


async def test_shops_me_only_returns_the_shops_of_the_user(
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


async def test_shops_me_requires_the_seller_role(
    db_client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    assert_problem(await db_client.get(f"{SHOPS}/me"), 401)
    assert_problem(await db_client.get(f"{SHOPS}/me", headers=chloe(make_token)), 403)


# --- Database guarantees ---------------------------------------------------------------------


async def test_two_concurrent_creations_of_the_same_name_give_one_201_and_one_409(
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


async def test_two_concurrent_shops_of_the_same_name_give_one_201_and_one_409(
    db_client: httpx.AsyncClient, make_token: TokenFactory, db_url: str
) -> None:
    responses = await asyncio.gather(
        db_client.post(SHOPS, json={"name": "Retro"}, headers=alice(make_token)),
        db_client.post(SHOPS, json={"name": "RETRO"}, headers=bob(make_token)),
    )
    assert sorted(r.status_code for r in responses) == [201, 409]
    assert count(db_url, "shops") == 1


def test_database_rejects_a_duplicate_name_and_a_seller_type_other_than_individual(
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


def test_database_rejects_two_categories_with_the_same_name_even_with_different_slugs(
    db_url: str,
) -> None:
    """The `lower(name)` index acts alone: the unique slug does not mask it."""
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
