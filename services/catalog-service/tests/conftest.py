"""Fixtures communes. Les clés RSA sont générées à l'exécution des tests et jamais versionnées."""

import json
import time
from collections.abc import Callable
from typing import Annotated, Any

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import APIRouter, Depends, FastAPI
from jwt.algorithms import RSAAlgorithm

from catalog.auth import CurrentUser, JwksCache, TokenVerifier, require_role
from catalog.config import Settings
from catalog.main import create_app
from catalog.schemas import ApiModel

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
