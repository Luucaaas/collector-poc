"""Validation locale des JWT émis par Keycloak (contrats.md §1.2), sans appel par requête.

Reprise de l'expérimentation 2, avec les corrections de sa synthèse : type de `realm_access` vérifié
(401 et non 500), JWKS mal formé (503 et non 500), titre unique pour tous les 401.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated, Any

import httpx
import jwt
import structlog
from fastapi import Depends, Request

from catalog.errors import ProblemError, forbidden, unauthenticated

ALGORITHM = "RS256"
logger = structlog.get_logger()


class JwksCache:
    """Clés publiques du realm, récupérées par l'URL interne puis gardées en mémoire (TTL).

    Un `kid` inconnu déclenche un rechargement, au plus un par `min_refetch` secondes : un attaquant
    qui fabrique des `kid` ne peut pas faire appeler Keycloak à chaque requête.
    """

    def __init__(
        self,
        url: str,
        ttl: float,
        min_refetch: float,
        *,
        max_stale: float = 3600.0,
        transport: httpx.AsyncBaseTransport | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._url = url
        self._ttl = ttl
        self._min_refetch = min_refetch
        self._max_stale = max_stale
        self._transport = transport
        self._clock = clock
        self._keys: dict[str, jwt.PyJWK] = {}
        self._fetched_at: float | None = None  # dernier chargement réussi
        self._attempted_at: float | None = None  # dernière tentative, réussie ou non
        self._lock = asyncio.Lock()

    async def get(self, kid: str) -> jwt.PyJWK:
        if self._fresh() and kid in self._keys:
            return self._keys[kid]
        async with self._lock:
            now = self._clock()
            reason = self._refresh_reason(kid, now)
            if reason is not None:
                if self._may_attempt(now):
                    await self._refresh(reason, now)
                elif not self._usable(now):
                    # Pas de clé utilisable et une tentative trop récente : on ne rappelle pas
                    # Keycloak à chaque requête.
                    raise self._unavailable()
            key = self._keys.get(kid) if self._usable(self._clock()) else None
            if key is None:
                raise unauthenticated("unknown_kid")
            return key

    def _fresh(self) -> bool:
        return self._fetched_at is not None and self._clock() - self._fetched_at <= self._ttl

    def _usable(self, now: float) -> bool:
        """Des clés existent et ne sont pas plus vieilles que TTL + `max_stale`."""
        return (
            self._fetched_at is not None and now - self._fetched_at <= self._ttl + self._max_stale
        )

    def _may_attempt(self, now: float) -> bool:
        return self._attempted_at is None or now - self._attempted_at >= self._min_refetch

    def _refresh_reason(self, kid: str, now: float) -> str | None:
        if self._fetched_at is None:
            return "cache_empty"
        if now - self._fetched_at > self._ttl:
            return "cache_expired"
        if kid not in self._keys:
            return "unknown_kid"
        return None

    @staticmethod
    def _unavailable() -> ProblemError:
        return ProblemError(503, title="Service d'identité indisponible", reason="jwks_unavailable")

    async def _refresh(self, reason: str, now: float) -> None:
        """Tente un rechargement ; en cas d'échec, garde les clés précédentes si elles restent
        utilisables (TTL + `max_stale`), sinon répond 503."""
        self._attempted_at = now
        try:
            await self._fetch(reason)
        except ProblemError:
            if not self._usable(now):
                raise
            logger.warning("jwks_stale_keys_used", reason=reason, kids=sorted(self._keys))

    async def _fetch(self, reason: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=5, transport=self._transport) as client:
                response = await client.get(self._url)
                response.raise_for_status()
            keys = self._parse(response.json())
        except (
            httpx.HTTPError,
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
            jwt.PyJWTError,
        ) as error:
            logger.error(
                "jwks_fetch_failed", url=self._url, reason=reason, error=type(error).__name__
            )
            raise self._unavailable() from error
        self._keys = keys
        self._fetched_at = self._clock()
        logger.info("jwks_fetch", url=self._url, reason=reason, kids=sorted(keys))

    @staticmethod
    def _parse(data: Any) -> dict[str, jwt.PyJWK]:
        if not isinstance(data, dict) or not isinstance(data.get("keys"), list):
            raise ValueError("jwks_malformed")
        keys: dict[str, jwt.PyJWK] = {}
        for item in data["keys"]:
            if item.get("use") == "sig" and item.get("kty") == "RSA":
                keys[item["kid"]] = jwt.PyJWK(item, ALGORITHM)
        return keys


@dataclass(frozen=True)
class CurrentUser:
    sub: str
    roles: frozenset[str]


def extract_roles(claims: dict[str, Any]) -> frozenset[str]:
    """Rôles de `realm_access.roles`. Absent : aucun rôle. Présent mais mal formé : 401, car le
    jeton est signé mais ne respecte pas le format attendu du realm."""
    realm_access = claims.get("realm_access")
    if realm_access is None:
        return frozenset()
    if not isinstance(realm_access, dict):
        raise unauthenticated("malformed_realm_access")
    roles = realm_access.get("roles", [])
    if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
        raise unauthenticated("malformed_roles")
    return frozenset(roles)


class TokenVerifier:
    def __init__(self, issuer: str, audience: str, jwks: JwksCache) -> None:
        self._issuer = issuer
        self._audience = audience
        self._jwks = jwks

    async def verify(self, token: str) -> CurrentUser:
        try:
            header = jwt.get_unverified_header(token)  # sert uniquement à choisir la clé (`kid`)
            if header.get("alg") != ALGORITHM:
                raise unauthenticated("invalid_algorithm")
            kid = header.get("kid")
            if not isinstance(kid, str):
                raise unauthenticated("missing_kid")
            key = await self._jwks.get(kid)
            claims: dict[str, Any] = jwt.decode(
                token,
                key.key,
                algorithms=[ALGORITHM],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except jwt.ExpiredSignatureError as error:
            raise unauthenticated("token_expired") from error
        except jwt.InvalidAudienceError as error:
            raise unauthenticated("invalid_audience") from error
        except jwt.InvalidIssuerError as error:
            raise unauthenticated("invalid_issuer") from error
        except jwt.InvalidSignatureError as error:
            raise unauthenticated("invalid_signature") from error
        except jwt.MissingRequiredClaimError as error:
            raise unauthenticated(f"missing_claim_{error.claim}") from error
        except jwt.InvalidTokenError as error:
            raise unauthenticated("malformed_token") from error
        sub = claims["sub"]
        if not isinstance(sub, str) or not sub:
            raise unauthenticated("invalid_sub")
        return CurrentUser(sub=sub, roles=extract_roles(claims))


async def get_current_user(request: Request) -> CurrentUser:
    """Dépendance : utilisateur du jeton Bearer, ou 401."""
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise unauthenticated("missing_token")
    verifier: TokenVerifier = request.app.state.verifier
    user = await verifier.verify(token)
    structlog.contextvars.bind_contextvars(sub=user.sub)
    return user


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_role(role: str) -> Callable[[CurrentUser], Awaitable[CurrentUser]]:
    """Dépendance : l'utilisateur doit avoir `role`, sinon 403."""

    async def check(user: CurrentUserDep) -> CurrentUser:
        if role not in user.roles:
            raise forbidden(f"missing_role_{role}")
        return user

    return check
