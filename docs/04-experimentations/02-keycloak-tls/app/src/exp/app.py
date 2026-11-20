"""Test application: local validation of the JWTs issued by Keycloak (contrats.md §1.2).

- GET /api/v1/public: without token;
- GET /api/v1/me    : any authenticated user, returns `sub` and roles;
- GET /api/v1/seller: `seller` role required.

The token is validated without a Keycloak call per request: RS256 signature (JWKS keys fetched via
the internal URL of the Keycloak service and cached), then `iss` (public URL), `aud` and `exp`.
Logs are JSON lines (structlog) that carry `correlation_id`.
"""

import asyncio
import os
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated, Any

import httpx
import jwt
import structlog
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse

ISSUER = os.environ.get("ISSUER", "https://auth.127.0.0.1.sslip.io/realms/collector")
JWKS_URL = os.environ.get(
    "JWKS_URL",
    "http://keycloak-service.keycloak.svc.cluster.local:8080"
    "/realms/collector/protocol/openid-connect/certs",
)
AUDIENCE = os.environ.get("AUDIENCE", "collector-api")
JWKS_TTL_S = 600.0  # lifetime of the key cache
JWKS_MIN_REFETCH_S = 30.0  # minimum delay between two reloads triggered by an unknown `kid`

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
)
logger = structlog.get_logger()


class ApiError(Exception):
    """Error returned in RFC 9457 format; `reason` is only written to the logs."""

    def __init__(self, status: int, title: str, reason: str) -> None:
        super().__init__(reason)
        self.status = status
        self.title = title
        self.reason = reason


class JwksCache:
    """Realm public keys, fetched through the internal URL then kept in memory."""

    def __init__(self, url: str, ttl: float, min_refetch: float) -> None:
        self._url = url
        self._ttl = ttl
        self._min_refetch = min_refetch
        self._keys: dict[str, jwt.PyJWK] = {}
        self._fetched_at: float | None = None
        self._lock = asyncio.Lock()

    async def get(self, kid: str) -> jwt.PyJWK:
        now = time.monotonic()
        if (
            self._fetched_at is not None
            and now - self._fetched_at <= self._ttl
            and kid in self._keys
        ):
            return self._keys[kid]
        async with self._lock:
            now = time.monotonic()
            reason = None
            if self._fetched_at is None:
                reason = "cache_empty"
            elif now - self._fetched_at > self._ttl:
                reason = "cache_expired"
            elif kid not in self._keys and now - self._fetched_at >= self._min_refetch:
                reason = "unknown_kid"
            if reason is not None:
                await self._fetch(reason)
            key = self._keys.get(kid)
            if key is None:
                raise ApiError(401, "Non authentifié", "unknown_kid")
            return key

    async def _fetch(self, reason: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(self._url)
                response.raise_for_status()
        except httpx.HTTPError as error:
            logger.error("jwks_fetch_failed", url=self._url, reason=reason, error=str(error))
            raise ApiError(503, "Service d'identité indisponible", "jwks_unavailable") from error
        data: dict[str, Any] = response.json()
        self._keys = {
            key["kid"]: jwt.PyJWK(key, "RS256")
            for key in data["keys"]
            if key.get("use") == "sig" and key.get("kty") == "RSA"
        }
        self._fetched_at = time.monotonic()
        logger.info(
            "jwks_fetch",
            url=self._url,
            reason=reason,
            status=response.status_code,
            kids=sorted(self._keys),
        )


jwks = JwksCache(JWKS_URL, JWKS_TTL_S, JWKS_MIN_REFETCH_S)

app = FastAPI(title="JWT validation test application")


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, error: ApiError) -> JSONResponse:
    logger.warning("auth_rejected", status=error.status, reason=error.reason, path=request.url.path)
    headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else None
    return JSONResponse(
        {
            "type": "about:blank",
            "title": error.title,
            "status": error.status,
            "correlation_id": structlog.contextvars.get_contextvars().get("correlation_id"),
        },
        status_code=error.status,
        media_type="application/problem+json",
        headers=headers,
    )


@app.middleware("http")
async def correlation_and_log(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Picks up or generates X-Request-ID, returns it, and logs every request as JSON."""
    correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = correlation_id
    if not request.url.path.startswith("/health"):
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )
    return response


async def authenticate(request: Request) -> dict[str, Any]:
    """Validates the Bearer token and returns its claims; 401 on the slightest defect."""
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ApiError(401, "Non authentifié", "missing_token")
    try:
        header = jwt.get_unverified_header(token)  # only used to pick the key (`kid`)
        if header.get("alg") != "RS256":
            raise ApiError(401, "Non authentifié", "invalid_algorithm")
        kid = header.get("kid")
        if not isinstance(kid, str):
            raise ApiError(401, "Non authentifié", "missing_kid")
        key = await jwks.get(kid)
        claims: dict[str, Any] = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=ISSUER,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.ExpiredSignatureError as error:
        raise ApiError(401, "Non authentifié", "token_expired") from error
    except jwt.InvalidAudienceError as error:
        raise ApiError(401, "Non authentifié", "invalid_audience") from error
    except jwt.InvalidIssuerError as error:
        raise ApiError(401, "Non authentifié", "invalid_issuer") from error
    except jwt.InvalidSignatureError as error:
        raise ApiError(401, "Non authentifié", "invalid_signature") from error
    except jwt.MissingRequiredClaimError as error:
        raise ApiError(401, "Non authentifié", f"missing_claim_{error.claim}") from error
    except jwt.InvalidTokenError as error:
        raise ApiError(401, "Non authentifié", "malformed_token") from error
    structlog.contextvars.bind_contextvars(sub=claims["sub"])
    return claims


Claims = Annotated[dict[str, Any], Depends(authenticate)]


def roles_of(claims: dict[str, Any]) -> list[str]:
    roles = claims.get("realm_access", {}).get("roles", [])
    return sorted(role for role in roles if isinstance(role, str))


def require_role(role: str) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
    async def check(claims: Claims) -> dict[str, Any]:
        if role not in roles_of(claims):
            raise ApiError(403, "Accès refusé", f"missing_role_{role}")
        return claims

    return check


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def ready() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/public")
async def public() -> dict[str, str]:
    return {"message": "route publique"}


@app.get("/api/v1/me")
async def me(claims: Claims) -> dict[str, Any]:
    return {"sub": claims["sub"], "roles": roles_of(claims)}


@app.get("/api/v1/seller")
async def seller(
    claims: Annotated[dict[str, Any], Depends(require_role("seller"))],
) -> dict[str, Any]:
    return {"sub": claims["sub"], "message": "espace vendeur"}
