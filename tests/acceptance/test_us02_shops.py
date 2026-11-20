"""US-02: the seller creates a shop (3 acceptance criteria)."""

from conftest import Api, Session, unique


def my_shop_names(catalog: Api, user: Session) -> list[str]:
    response = catalog.get("/api/v1/shops/me", user)
    assert response.status_code == 200
    return [s["name"] for s in response.json()["items"]]


def test_us02_ca1_seller_creates_shop(catalog: Api, alice: Session) -> None:
    """The criterion label is « Jouets des années 80 »; a random suffix (unique name)
    makes the test replayable, so the expected name is this label followed by the suffix."""
    name = unique("Jouets des années 80")
    response = catalog.post(
        "/api/v1/shops", alice, json={"name": name, "description": "Jouets vintage d'avant 1990."}
    )

    assert response.status_code == 201, response.text
    shop = response.json()
    assert shop["owner_id"] == alice.sub  # the shop belongs to alice
    assert shop["seller_type"] == "INDIVIDUAL"
    assert shop["name"] == name
    # Public page readable without authentication, identical to the creation response.
    public = catalog.get(f"/api/v1/shops/{shop['id']}")
    assert public.status_code == 200
    assert public.json() == shop
    assert name in my_shop_names(catalog, alice)


def test_us02_ca2_shop_with_contact_details_rejected(catalog: Api, alice: Session) -> None:
    before = my_shop_names(catalog, alice)
    with_email = unique("Boutique email")
    with_phone = unique("Boutique téléphone")

    email = catalog.post(
        "/api/v1/shops",
        alice,
        json={"name": with_email, "description": "Écrivez-moi à alice.martin@example.com"},
    )
    phone = catalog.post(
        "/api/v1/shops",
        alice,
        json={"name": with_phone, "description": "Appelez-moi au 06 12 34 56 78 le soir"},
    )

    assert email.status_code == 422
    assert [e["code"] for e in email.json()["errors"]] == ["CONTACT_EMAIL"]
    assert phone.status_code == 422
    assert [e["code"] for e in phone.json()["errors"]] == ["CONTACT_PHONE"]
    after = my_shop_names(catalog, alice)  # no shop created
    assert after == before
    assert with_email not in after and with_phone not in after


def test_us02_ca3_creation_denied(catalog: Api, alice: Session, chloe: Session) -> None:
    name = unique("Boutique interdite")
    alice_before = my_shop_names(catalog, alice)

    anonymous = catalog.post("/api/v1/shops", json={"name": name})
    as_buyer = catalog.post("/api/v1/shops", chloe, json={"name": name})

    assert anonymous.status_code == 401
    assert as_buyer.status_code == 403  # chloe only has the buyer role
    assert my_shop_names(catalog, alice) == alice_before
    # Name still free: a creation by a seller succeeds, so nothing had been recorded.
    assert catalog.post("/api/v1/shops", alice, json={"name": name}).status_code == 201
