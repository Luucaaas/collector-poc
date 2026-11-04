"""US-02 : le vendeur crée une boutique (3 critères d'acceptation)."""

from conftest import Api, Session, unique


def my_shop_names(catalog: Api, user: Session) -> list[str]:
    response = catalog.get("/api/v1/shops/me", user)
    assert response.status_code == 200
    return [s["name"] for s in response.json()["items"]]


def test_us02_ca1_vendeur_cree_boutique(catalog: Api, alice: Session) -> None:
    """Le libellé du critère est « Jouets des années 80 » ; un suffixe aléatoire (nom unique)
    rend le test rejouable, le nom attendu est donc ce libellé suivi du suffixe."""
    name = unique("Jouets des années 80")
    response = catalog.post(
        "/api/v1/shops", alice, json={"name": name, "description": "Jouets vintage d'avant 1990."}
    )

    assert response.status_code == 201, response.text
    shop = response.json()
    assert shop["owner_id"] == alice.sub  # la boutique appartient à alice
    assert shop["seller_type"] == "INDIVIDUAL"
    assert shop["name"] == name
    # Page publique consultable sans authentification, identique à la réponse de création.
    public = catalog.get(f"/api/v1/shops/{shop['id']}")
    assert public.status_code == 200
    assert public.json() == shop
    assert name in my_shop_names(catalog, alice)


def test_us02_ca2_boutique_avec_coordonnees_refusee(catalog: Api, alice: Session) -> None:
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
    after = my_shop_names(catalog, alice)  # aucune boutique créée
    assert after == before
    assert with_email not in after and with_phone not in after


def test_us02_ca3_creation_sans_droit_refusee(catalog: Api, alice: Session, chloe: Session) -> None:
    name = unique("Boutique interdite")
    alice_before = my_shop_names(catalog, alice)

    anonymous = catalog.post("/api/v1/shops", json={"name": name})
    as_buyer = catalog.post("/api/v1/shops", chloe, json={"name": name})

    assert anonymous.status_code == 401
    assert as_buyer.status_code == 403  # chloe n'a que le rôle buyer
    assert my_shop_names(catalog, alice) == alice_before
    # Même nom libre : une création par un vendeur aboutit, donc rien n'avait été enregistré.
    assert catalog.post("/api/v1/shops", alice, json={"name": name}).status_code == 201
