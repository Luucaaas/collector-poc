"""US-01 : l'admin crée une catégorie (3 critères d'acceptation)."""

from conftest import Api, Factory, Session, unique


def names(catalog: Api) -> list[str]:
    response = catalog.get("/api/v1/categories")  # liste publique : aucun jeton
    assert response.status_code == 200
    return [c["name"] for c in response.json()["items"]]


def test_us01_ca1_admin_cree_categorie(catalog: Api, admin: Session) -> None:
    """Le libellé du critère est « Figurines Star Wars » (slug `figurines-star-wars`).

    Un suffixe aléatoire rend le test rejouable (le nom est unique) : le slug attendu est donc
    celui du libellé du critère suivi du suffixe, `figurines-star-wars-<suffixe>`.
    """
    suffix = unique("").strip()
    name = f"Figurines Star Wars {suffix}"
    response = catalog.post("/api/v1/categories", admin, json={"name": name})

    assert response.status_code == 201, response.text
    created = response.json()
    assert created["name"] == name
    assert created["slug"] == f"figurines-star-wars-{suffix}"  # « Figurines Star Wars » + suffixe
    # Visible dans la liste publique, consultable sans authentification.
    listed = catalog.get("/api/v1/categories")
    assert listed.status_code == 200
    assert [c for c in listed.json()["items"] if c["id"] == created["id"]] == [created]


def test_us01_ca2_doublon_et_nom_trop_court_refuses(catalog: Api, admin: Session) -> None:
    base = unique("Baskets")
    first = catalog.post("/api/v1/categories", admin, json={"name": base})
    assert first.status_code == 201
    before = catalog.get("/api/v1/categories").json()["total"]

    duplicate = catalog.post("/api/v1/categories", admin, json={"name": base.lower()})
    too_short = catalog.post("/api/v1/categories", admin, json={"name": "x"})

    assert duplicate.status_code == 409
    assert duplicate.headers["content-type"].startswith("application/problem+json")
    assert [e["code"] for e in duplicate.json()["errors"]] == ["NAME_ALREADY_USED"]
    assert too_short.status_code == 422
    assert too_short.headers["content-type"].startswith("application/problem+json")
    # Aucune catégorie créée : le total n'a pas bougé et le doublon n'est pas dans la liste.
    after = catalog.get("/api/v1/categories").json()
    assert after["total"] == before
    assert [c["name"] for c in after["items"]].count(base) == 1
    assert base.lower() not in [c["name"] for c in after["items"]]
    assert "x" not in [c["name"] for c in after["items"]]


def test_us01_ca3_creation_sans_droit_refusee(catalog: Api, bob: Session, make: Factory) -> None:
    before = catalog.get("/api/v1/categories").json()["total"]
    name = unique("Interdite")

    anonymous = catalog.post("/api/v1/categories", json={"name": name})
    as_seller = catalog.post("/api/v1/categories", bob, json={"name": name})

    assert anonymous.status_code == 401
    assert as_seller.status_code == 403  # bob n'a que le rôle seller
    after = catalog.get("/api/v1/categories").json()
    assert after["total"] == before
    assert name not in [c["name"] for c in after["items"]]
