"""Fixtures communes : jetons Keycloak, clients HTTP, fabriques de données, observation AMQP."""

import base64
import json
import time
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

import httpx
import pytest

import config
from helpers import EventSpy

USERS = ("admin", "alice", "bob", "chloe")
KEYCLOAK_WAIT_SECONDS = 60.0
TOKEN_MAX_AGE_SECONDS = 200  # les jetons du realm durent 300 s


def unique(name: str) -> str:
    """Nom unique par appel : les tests restent rejouables sur une pile qui garde son état."""
    return f"{name} {uuid.uuid4().hex[:8]}"


@dataclass
class Session:
    """Un compte de démonstration : son jeton (renouvelé au besoin) et son identifiant `sub`."""

    username: str
    password: str
    _token: str = ""
    _fetched_at: float = 0.0

    @property
    def token(self) -> str:
        if not self._token or time.monotonic() - self._fetched_at > TOKEN_MAX_AGE_SECONDS:
            response = httpx.post(
                f"{config.KEYCLOAK_URL}/realms/{config.REALM}/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "client_id": config.TEST_CLIENT,
                    "username": self.username,
                    "password": self.password,
                },
                timeout=10,
            )
            assert response.status_code == 200, f"jeton refusé pour {self.username}"
            self._token = response.json()["access_token"]
            self._fetched_at = time.monotonic()
        return self._token

    @property
    def sub(self) -> str:
        payload = self.token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return str(json.loads(base64.urlsafe_b64decode(payload))["sub"])

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


class Api:
    """Client HTTP d'un service ; `as_` choisit le compte, absent = appel sans jeton."""

    def __init__(self, base_url: str) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=10)

    def request(
        self, method: str, path: str, as_: Session | None = None, **kwargs: Any
    ) -> httpx.Response:
        headers = {**kwargs.pop("headers", {}), **(as_.headers if as_ is not None else {})}
        return self._client.request(method, path, headers=headers, **kwargs)

    def get(self, path: str, as_: Session | None = None, **kwargs: Any) -> httpx.Response:
        return self.request("GET", path, as_, **kwargs)

    def post(self, path: str, as_: Session | None = None, **kwargs: Any) -> httpx.Response:
        return self.request("POST", path, as_, **kwargs)

    def put(self, path: str, as_: Session | None = None, **kwargs: Any) -> httpx.Response:
        return self.request("PUT", path, as_, **kwargs)

    def close(self) -> None:
        self._client.close()


@pytest.fixture(scope="session")
def env() -> dict[str, str]:
    return config.read_env()


@pytest.fixture(scope="session")
def accounts(env: dict[str, str]) -> dict[str, Session]:
    return {u: Session(u, env[f"{u.upper()}_PASSWORD"]) for u in USERS}


@pytest.fixture(scope="session")
def admin(accounts: dict[str, Session]) -> Session:
    return accounts["admin"]


@pytest.fixture(scope="session")
def alice(accounts: dict[str, Session]) -> Session:
    return accounts["alice"]


@pytest.fixture(scope="session")
def bob(accounts: dict[str, Session]) -> Session:
    return accounts["bob"]


@pytest.fixture(scope="session")
def chloe(accounts: dict[str, Session]) -> Session:
    return accounts["chloe"]


@pytest.fixture(scope="session")
def catalog() -> Iterator[Api]:
    api = Api(config.CATALOG_URL)
    yield api
    api.close()


@pytest.fixture(scope="session")
def notification() -> Iterator[Api]:
    api = Api(config.NOTIFICATION_URL)
    yield api
    api.close()


@pytest.fixture(scope="session", autouse=True)
def stack_ready(catalog: Api, notification: Api, alice: Session) -> None:
    """Échoue tout de suite, avec un message clair, si la pile n'est pas lancée ou pas prête."""
    for name, api in (("catalog", catalog), ("notification", notification)):
        try:
            response = api.get("/health/ready")
        except httpx.HTTPError as error:
            pytest.exit(f"{name}-service injoignable ({error}) : lancer deploy/compose/up.sh")
        if response.status_code != 200:
            pytest.exit(f"{name}-service pas prêt (HTTP {response.status_code})")
    # Keycloak : le realm est importé après le démarrage ; on attend (borné) un premier jeton.
    deadline = time.monotonic() + KEYCLOAK_WAIT_SECONDS
    while True:
        try:
            alice.token  # noqa: B018  (obtient et met en cache le jeton)
            break
        except (AssertionError, httpx.HTTPError) as error:
            if time.monotonic() > deadline:
                pytest.exit(
                    f"Keycloak ne délivre pas de jeton après {KEYCLOAK_WAIT_SECONDS:.0f} s "
                    f"(realm non importé ?) : {error}"
                )
            time.sleep(1)


@pytest.fixture
def spy(env: dict[str, str]) -> Iterator[EventSpy]:
    """File temporaire liée à `article.events`, créée avant l'action testée."""
    event_spy = EventSpy(config.amqp_url(env)).start()
    yield event_spy
    event_spy.close()


# --- Fabriques de données -------------------------------------------------------------------


@dataclass
class Factory:
    catalog: Api
    admin: Session

    def category(self, name: str) -> dict[str, Any]:
        response = self.catalog.post("/api/v1/categories", self.admin, json={"name": unique(name)})
        assert response.status_code == 201, response.text
        body: dict[str, Any] = response.json()
        return body

    def shop(self, owner: Session, name: str = "Boutique de test") -> dict[str, Any]:
        response = self.catalog.post("/api/v1/shops", owner, json={"name": unique(name)})
        assert response.status_code == 201, response.text
        body: dict[str, Any] = response.json()
        return body

    def article_payload(self, shop_id: str, category_id: str, **overrides: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "shop_id": shop_id,
            "category_id": category_id,
            "title": unique("Boba Fett Kenner 1979"),
            "description": "Figurine originale Kenner de 1979, complète avec son arme, bon état.",
            "photo_urls": ["https://images.example.com/boba-1.jpg"],
            "price": "120.00",
            "shipping_fee": "8.00",
            "currency": "EUR",
        }
        payload.update(overrides)
        return payload

    def article(
        self, seller: Session, shop_id: str, category_id: str, **overrides: Any
    ) -> dict[str, Any]:
        payload = self.article_payload(shop_id, category_id, **overrides)
        response = self.catalog.post("/api/v1/articles", seller, json=payload)
        assert response.status_code == 201, response.text
        body: dict[str, Any] = response.json()
        return body


@pytest.fixture
def make(catalog: Api, admin: Session) -> Factory:
    return Factory(catalog, admin)


@pytest.fixture(scope="session")
def alice_shop(catalog: Api, admin: Session, alice: Session) -> dict[str, Any]:
    """Boutique d'alice, partagée par les tests (chacun crée sa propre catégorie)."""
    return Factory(catalog, admin).shop(alice, "Boutique d'alice")


@pytest.fixture(scope="session")
def bob_shop(catalog: Api, admin: Session, bob: Session) -> dict[str, Any]:
    return Factory(catalog, admin).shop(bob, "Boutique de bob")


def published(events: list[dict[str, Any]], article_id: str) -> list[dict[str, Any]]:
    """Événements d'un article donné (les autres tests peuvent publier en parallèle de la pile)."""
    return [e for e in events if e["data"]["article_id"] == article_id]


Predicate = Callable[[list[dict[str, Any]]], bool]
