"""Fixtures communes. Les clés RSA sont générées à l'exécution des tests et jamais versionnées."""

import json
import os
import time
from collections.abc import Callable, Iterator
from typing import Annotated, Any

import httpx
import jwt
import pytest
from alembic import command
from alembic.config import Config
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import APIRouter, Depends, FastAPI
from jwt.algorithms import RSAAlgorithm
from sqlalchemy import create_engine, text
from testcontainers.community.postgres import PostgresContainer

from notification.auth import CurrentUser, JwksCache, TokenVerifier, require_role
from notification.config import Settings
from notification.main import create_app
from notification.schemas import ApiModel

ISSUER = "https://auth.test.invalid/realms/collector"
AUDIENCE = "collector-api"
JWKS_URL = "http://keycloak.test.invalid/certs"
KID = "test-key-1"


class TestKey:
    """Une paire RSA de test et son JWK public."""

    __test__ = False

    def __init__(self, kid: str) -> None:
        self.kid = kid
        self.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        jwk = json.loads(RSAAlgorithm.to_jwk(self.private.public_key()))
        jwk.update({"kid": kid, "use": "sig", "alg": "RS256"})
        self.jwk: dict[str, Any] = jwk


@pytest.fixture(scope="session")
def key() -> TestKey:
    return TestKey(KID)


@pytest.fixture(scope="session")
def other_key() -> TestKey:
    """Clé que le JWKS ne publie pas, même `kid` possible."""
    return TestKey("other-key")


class ProbeBody(ApiModel):
    name: str


def make_probe_router() -> APIRouter:
    """Routes de test protégées : ajoutées par les tests seulement, jamais dans l'application."""
    router = APIRouter(prefix="/api/v1/_probe")

    @router.get("/me")
    async def me(user: Annotated[CurrentUser, Depends(require_role("buyer"))]) -> dict[str, Any]:
        return {"sub": user.sub, "roles": sorted(user.roles)}

    @router.get("/admin")
    async def admin(user: Annotated[CurrentUser, Depends(require_role("admin"))]) -> dict[str, str]:
        return {"sub": user.sub}

    @router.post("/body", status_code=201)
    async def body(payload: ProbeBody) -> dict[str, str]:
        return {"name": payload.name}

    @router.get("/boom")
    async def boom() -> None:
        raise RuntimeError("secret interne")

    return router


class JwksServer:
    """Faux Keycloak : sert le JWKS courant et compte les appels."""

    def __init__(self, *keys: TestKey) -> None:
        self.keys = list(keys)
        self.calls = 0
        self.fail = False
        self.body: Any = None  # si non nul, remplace le JWKS (corps mal formé)

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        if self.fail:
            return httpx.Response(500)
        if self.body is not None:
            return httpx.Response(200, json=self.body)
        return httpx.Response(200, json={"keys": [k.jwk for k in self.keys]})


@pytest.fixture
def jwks_server(key: TestKey) -> JwksServer:
    return JwksServer(key)


def build_settings(database_url: str = "postgresql+psycopg://u:p@127.0.0.1:1/db") -> Settings:
    return Settings(
        database_url=database_url,
        # Inatteignable : les tests injectent un faux producteur ou démarrent un vrai broker.
        rabbitmq_url="amqp://guest:guest@127.0.0.1:1/",
        issuer=ISSUER,
        jwks_url=JWKS_URL,
        audience=AUDIENCE,
        cors_origin="https://app.test.invalid",
    )


@pytest.fixture
def app(jwks_server: JwksServer) -> FastAPI:
    application = create_app(build_settings())
    jwks = JwksCache(JWKS_URL, 600, 30, transport=httpx.MockTransport(jwks_server.handler))
    application.state.verifier = TokenVerifier(ISSUER, AUDIENCE, jwks)
    application.include_router(make_probe_router())
    return application


@pytest.fixture
async def client(app: FastAPI):  # type: ignore[no-untyped-def]
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as http_client:
        yield http_client


TokenFactory = Callable[..., str]


@pytest.fixture
def make_token(key: TestKey) -> TokenFactory:
    def factory(
        *,
        signing_key: TestKey | None = None,
        algorithm: str = "RS256",
        headers: dict[str, Any] | None = None,
        remove: tuple[str, ...] = (),
        **overrides: Any,
    ) -> str:
        now = int(time.time())
        claims: dict[str, Any] = {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": "user-1",
            "iat": now,
            "exp": now + 300,
            "realm_access": {"roles": ["buyer"]},
        }
        claims.update(overrides)
        for name in remove:
            claims.pop(name, None)
        signer = signing_key or key
        return jwt.encode(
            claims,
            signer.private,
            algorithm=algorithm,
            headers={"kid": signer.kid, **(headers or {})},
        )

    return factory


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


POSTGRES_IMAGE = "postgres:18.4-alpine"  # version retenue pour le POC (ADR 0008)


@pytest.fixture(scope="session")
def migrated_database_url() -> Iterator[str]:
    """Un PostgreSQL réel pour toute la session de tests, schéma créé par Alembic (`head`)."""
    with PostgresContainer(POSTGRES_IMAGE, driver="psycopg") as container:
        url = container.get_connection_url()
        previous = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = url
        try:
            command.upgrade(Config("alembic.ini"), "head")
        finally:
            if previous is None:
                os.environ.pop("DATABASE_URL")
            else:
                os.environ["DATABASE_URL"] = previous
        yield url


@pytest.fixture
def db_url(migrated_database_url: str) -> Iterator[str]:
    """Base vidée avant chaque test."""
    engine = create_engine(migrated_database_url)
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE notifications, preferences, interests"))
    engine.dispose()
    yield migrated_database_url


class NoConsumer:
    """Faux consommateur : les tests d'API n'ont pas besoin de RabbitMQ."""

    async def start(self) -> None:
        pass

    async def close(self) -> None:
        pass


@pytest.fixture
async def db_client(  # type: ignore[no-untyped-def]
    db_url: str, jwks_server: JwksServer
):
    """Client HTTP sur l'application complète, avec PostgreSQL réel, faux JWKS et sans broker."""
    application = create_app(build_settings(db_url))
    application.state.consumer = NoConsumer()
    jwks = JwksCache(JWKS_URL, 600, 30, transport=httpx.MockTransport(jwks_server.handler))
    application.state.verifier = TokenVerifier(ISSUER, AUDIENCE, jwks)
    async with application.router.lifespan_context(application):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=application, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as http_client:
            yield http_client


def roles_headers(make_token: Callable[..., str], sub: str, *roles: str) -> dict[str, str]:
    """En-tête Bearer d'un utilisateur de démonstration (alice, bob, chloe, admin)."""
    return bearer(make_token(sub=sub, realm_access={"roles": list(roles)}))
