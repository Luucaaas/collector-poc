"""US-01: the admin creates a category (3 acceptance criteria)."""

from conftest import Api, Factory, Session, unique


def names(catalog: Api) -> list[str]:
    response = catalog.get("/api/v1/categories")  # public list: no token
    assert response.status_code == 200
    return [c["name"] for c in response.json()["items"]]


def test_us01_ca1_admin_creates_category(catalog: Api, admin: Session) -> None:
    """The criterion label is « Figurines Star Wars » (slug `figurines-star-wars`).

    A random suffix makes the test replayable (the name is unique): the expected slug is thus
    the criterion label followed by the suffix, `figurines-star-wars-<suffix>`.
    """
    suffix = unique("").strip()
    name = f"Figurines Star Wars {suffix}"
    response = catalog.post("/api/v1/categories", admin, json={"name": name})

    assert response.status_code == 201, response.text
    created = response.json()
    assert created["name"] == name
    assert created["slug"] == f"figurines-star-wars-{suffix}"  # « Figurines Star Wars » + suffix
    # Visible in the public list, readable without authentication.
    listed = catalog.get("/api/v1/categories")
    assert listed.status_code == 200
    assert [c for c in listed.json()["items"] if c["id"] == created["id"]] == [created]


def test_us01_ca2_duplicate_and_too_short_name_rejected(catalog: Api, admin: Session) -> None:
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
    # No category created: the total did not move and the duplicate is not in the list.
    after = catalog.get("/api/v1/categories").json()
    assert after["total"] == before
    assert [c["name"] for c in after["items"]].count(base) == 1
    assert base.lower() not in [c["name"] for c in after["items"]]
    assert "x" not in [c["name"] for c in after["items"]]


def test_us01_ca3_creation_denied(catalog: Api, bob: Session, make: Factory) -> None:
    before = catalog.get("/api/v1/categories").json()["total"]
    name = unique("Interdite")

    anonymous = catalog.post("/api/v1/categories", json={"name": name})
    as_seller = catalog.post("/api/v1/categories", bob, json={"name": name})

    assert anonymous.status_code == 401
    assert as_seller.status_code == 403  # bob only has the seller role
    after = catalog.get("/api/v1/categories").json()
    assert after["total"] == before
    assert name not in [c["name"] for c in after["items"]]
