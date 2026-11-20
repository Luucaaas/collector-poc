"""Security tests: JWT validation, roles, RFC 9457 errors, correlation, logs."""

import base64
import hashlib
import hmac
import json
import time
from typing import Any

import httpx
import jwt
import pytest
from fastapi import FastAPI
from pydantic import ValidationError

from catalog.auth import JwksCache
from catalog.config import Settings
from catalog.errors import ProblemError
from tests.conftest import JWKS_URL, JwksServer, TestKey, TokenFactory, bearer

ME = "/api/v1/_probe/me"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _forge_hs256(claims: dict[str, Any], secret: bytes, kid: str) -> str:
    """PyJWT refuses to sign in HS256 with a public key: the token is forged by hand."""
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT", "kid": kid}).encode())
    payload = _b64(json.dumps(claims).encode())
    signature = hmac.new(secret, f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64(signature)}"


def assert_unauthenticated(response: httpx.Response) -> None:
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["title"] == "Non authentifié"
    assert body["status"] == 401
    assert "detail" not in body  # the rejection reason is never in the response
    assert body["correlation_id"] == response.headers["x-request-id"]


async def test_valid_token_gives_200_with_sub_and_roles(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await client.get(ME, headers=bearer(make_token()))
    assert response.status_code == 200
    assert response.json() == {"sub": "user-1", "roles": ["buyer"]}


async def test_missing_token_gives_401(client: httpx.AsyncClient) -> None:
    assert_unauthenticated(await client.get(ME))


async def test_scheme_other_than_bearer_gives_401(client: httpx.AsyncClient) -> None:
    assert_unauthenticated(await client.get(ME, headers={"Authorization": "Basic abc"}))


async def test_malformed_token_gives_401(client: httpx.AsyncClient) -> None:
    assert_unauthenticated(await client.get(ME, headers=bearer("not-a-jwt")))


async def test_token_with_a_wrong_issuer_gives_401_unauthorized(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    token = make_token(iss="https://evil.test.invalid/realms/collector")
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


async def test_wrong_audience_gives_401(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    assert_unauthenticated(await client.get(ME, headers=bearer(make_token(aud="other-api"))))


async def test_expired_token_gives_401(client: httpx.AsyncClient, make_token: TokenFactory) -> None:
    token = make_token(exp=int(time.time()) - 10)
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


@pytest.mark.parametrize("claim", ["exp", "iss", "aud", "sub"])
async def test_missing_required_claim_gives_401(
    client: httpx.AsyncClient, make_token: TokenFactory, claim: str
) -> None:
    token = make_token(remove=(claim,))
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


async def test_tampered_signature_gives_401(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    header, payload, signature = make_token().split(".")
    flipped = ("A" if signature[0] != "A" else "B") + signature[1:]
    assert_unauthenticated(await client.get(ME, headers=bearer(f"{header}.{payload}.{flipped}")))


async def test_tampered_payload_gives_401(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    header, payload, signature = make_token().split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=="))
    claims["realm_access"] = {"roles": ["admin"]}
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    assert_unauthenticated(await client.get(ME, headers=bearer(f"{header}.{forged}.{signature}")))


async def test_token_signed_by_another_key_with_the_same_kid_gives_401(
    client: httpx.AsyncClient, make_token: TokenFactory, key: TestKey
) -> None:
    attacker = TestKey(key.kid)  # same `kid`, other key pair
    assert_unauthenticated(await client.get(ME, headers=bearer(make_token(signing_key=attacker))))


async def test_unknown_kid_gives_401(
    client: httpx.AsyncClient, make_token: TokenFactory, other_key: TestKey
) -> None:
    token = make_token(signing_key=other_key)
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


async def test_missing_kid_gives_401(client: httpx.AsyncClient, key: TestKey) -> None:
    now = int(time.time())
    claims = {"iss": "x", "aud": "collector-api", "sub": "u", "exp": now + 60}
    token = jwt.encode(claims, key.private, algorithm="RS256")  # no `kid`
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


async def test_algorithm_none_gives_401(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    now = int(time.time())
    claims = {"iss": "x", "aud": "collector-api", "sub": "u", "exp": now + 60}
    token = jwt.encode(claims, None, algorithm="none", headers={"kid": "test-key-1"})
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


async def test_algorithm_hs256_signed_with_the_public_key_gives_401(
    client: httpx.AsyncClient, key: TestKey
) -> None:
    """Algorithm confusion attack: HS256 with the public JWK as secret."""
    now = int(time.time())
    claims = {"iss": "x", "aud": "collector-api", "sub": "u", "exp": now + 60}
    token = _forge_hs256(claims, json.dumps(key.jwk).encode(), key.kid)
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


@pytest.mark.parametrize(
    "realm_access",
    ["buyer", ["buyer"], {"roles": "buyer"}, {"roles": ["buyer", 7]}],
)
async def test_malformed_realm_access_gives_401_not_500(
    client: httpx.AsyncClient, make_token: TokenFactory, realm_access: Any
) -> None:
    token = make_token(realm_access=realm_access)
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


async def test_non_text_sub_gives_401(client: httpx.AsyncClient, make_token: TokenFactory) -> None:
    assert_unauthenticated(await client.get(ME, headers=bearer(make_token(sub=42))))


async def test_empty_sub_gives_401(client: httpx.AsyncClient, make_token: TokenFactory) -> None:
    assert_unauthenticated(await client.get(ME, headers=bearer(make_token(sub=""))))


async def test_missing_role_gives_403(client: httpx.AsyncClient, make_token: TokenFactory) -> None:
    response = await client.get("/api/v1/_probe/admin", headers=bearer(make_token()))
    assert response.status_code == 403
    body = response.json()
    assert body["title"] == "Accès refusé"
    assert body["type"] == "https://collector.shop/problems/forbidden"
    assert "detail" not in body


async def test_present_role_gives_200(client: httpx.AsyncClient, make_token: TokenFactory) -> None:
    token = make_token(realm_access={"roles": ["admin"]})
    response = await client.get("/api/v1/_probe/admin", headers=bearer(token))
    assert response.status_code == 200


async def test_failing_jwks_gives_503(
    client: httpx.AsyncClient, make_token: TokenFactory, jwks_server: JwksServer
) -> None:
    jwks_server.fail = True
    response = await client.get(ME, headers=bearer(make_token()))
    assert response.status_code == 503
    assert response.json()["title"] == "Service d'identité indisponible"


@pytest.mark.parametrize(
    "body",
    [
        "not an object",
        {"other": []},
        {"keys": "non"},
        {"keys": ["non"]},
        {"keys": [{"kty": "RSA", "use": "sig", "kid": "k", "n": "!", "e": "AQAB"}]},
        {"keys": [{"kty": "RSA", "use": "sig", "n": "AQAB", "e": "AQAB"}]},  # without `kid`
    ],
)
async def test_malformed_jwks_gives_503_not_500(
    client: httpx.AsyncClient, make_token: TokenFactory, jwks_server: JwksServer, body: Any
) -> None:
    jwks_server.body = body
    response = await client.get(ME, headers=bearer(make_token()))
    assert response.status_code == 503
    assert response.json()["title"] == "Service d'identité indisponible"


async def test_jwks_is_cached(
    client: httpx.AsyncClient, make_token: TokenFactory, jwks_server: JwksServer
) -> None:
    for _ in range(5):
        assert (await client.get(ME, headers=bearer(make_token()))).status_code == 200
    assert jwks_server.calls == 1


async def test_unknown_kid_reloads_the_jwks_only_once_per_minimum_delay(
    jwks_server: JwksServer, other_key: TestKey
) -> None:
    now = [0.0]
    cache = JwksCache(
        "http://x",
        600,
        30,
        transport=httpx.MockTransport(jwks_server.handler),
        clock=lambda: now[0],
    )
    await cache.get("test-key-1")
    assert jwks_server.calls == 1
    for _ in range(3):  # burst of unknown `kid`: no reload before 30 s
        with pytest.raises(ProblemError):
            await cache.get("unknown")
    assert jwks_server.calls == 1
    now[0] = 31.0
    jwks_server.keys.append(other_key)
    assert (await cache.get("other-key")).key is not None
    assert jwks_server.calls == 2


async def test_jwks_cache_expires_after_the_ttl(jwks_server: JwksServer) -> None:
    now = [0.0]
    cache = JwksCache(
        "http://x",
        600,
        30,
        transport=httpx.MockTransport(jwks_server.handler),
        clock=lambda: now[0],
    )
    await cache.get("test-key-1")
    now[0] = 601.0
    await cache.get("test-key-1")
    assert jwks_server.calls == 2


async def test_body_with_unknown_field_gives_422_rfc_9457(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await client.post(
        "/api/v1/_probe/body", json={"name": "ok", "extra_field": "sensitive-value"}
    )
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"] == "https://collector.shop/problems/validation-error"
    assert body["title"] == "Données invalides"
    assert body["errors"] == [{"field": "extra_field", "code": "EXTRA_FORBIDDEN"}]
    assert body["correlation_id"] == response.headers["x-request-id"]
    assert "sensitive-value" not in response.text


async def test_unknown_route_gives_404_rfc_9457(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/unknown")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["title"] == "Ressource introuvable"


async def test_unexpected_error_gives_500_without_detail(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/_probe/boom", headers={"X-Request-ID": "req-500"})
    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["x-request-id"] == "req-500"
    body = response.json()
    assert body["title"] == "Erreur interne"
    assert body["correlation_id"] == "req-500"
    assert "secret interne" not in response.text
    assert "RuntimeError" not in response.text


async def test_valid_request_id_is_kept(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/live", headers={"X-Request-ID": "mon-id.42_A"})
    assert response.headers["x-request-id"] == "mon-id.42_A"


@pytest.mark.parametrize("value", ["a" * 129, "with space", "a;b", "<b>"])
async def test_too_long_or_invalid_request_id_is_replaced(
    client: httpx.AsyncClient, value: str
) -> None:
    response = await client.get("/health/live", headers={"X-Request-ID": value})
    assert response.headers["x-request-id"] != value
    assert len(response.headers["x-request-id"]) == 36  # UUID


async def test_one_json_log_line_per_request_with_correlation_id(
    client: httpx.AsyncClient, make_token: TokenFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    await client.get(ME, headers={**bearer(make_token()), "X-Request-ID": "corr-1"})
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]
    requests = [line for line in lines if line["event"] == "request"]
    assert len(requests) == 1
    entry = requests[0]
    assert entry["correlation_id"] == "corr-1"
    assert (entry["method"], entry["path"], entry["status"]) == ("GET", ME, 200)
    assert entry["duration_ms"] >= 0
    assert entry["sub"] == "user-1"


async def test_no_token_nor_reason_in_the_responses_and_logs(
    client: httpx.AsyncClient, make_token: TokenFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    token = make_token(aud="other-api")
    response = await client.get(ME, headers=bearer(token))
    logs = capsys.readouterr().out
    assert token not in logs
    assert token.split(".")[1] not in logs
    assert "invalid_audience" in logs  # the reason is in the logs...
    assert "invalid_audience" not in response.text  # ... and only there


async def test_cors_allows_only_the_front_origin(client: httpx.AsyncClient) -> None:
    allowed = await client.get("/health/live", headers={"Origin": "https://app.test.invalid"})
    refused = await client.get("/health/live", headers={"Origin": "https://evil.test.invalid"})
    assert allowed.headers["access-control-allow-origin"] == "https://app.test.invalid"
    assert "access-control-allow-origin" not in refused.headers


async def test_metrics_exposes_the_histogram_with_the_i3_buckets(
    client: httpx.AsyncClient, app: FastAPI
) -> None:
    await client.get("/api/v1/unknown")
    text = (await client.get("/metrics")).text
    assert "http_request_duration_seconds_bucket" in text
    assert 'le="0.3"' in text
    assert 'le="0.5"' in text
    assert "http_requests_total" in text


def _cache(server: JwksServer, now: list[float], max_stale: float = 3600) -> JwksCache:
    return JwksCache(
        "http://x",
        600,
        30,
        max_stale=max_stale,
        transport=httpx.MockTransport(server.handler),
        clock=lambda: now[0],
    )


async def test_failing_jwks_is_not_called_again_during_the_minimum_delay(
    client: httpx.AsyncClient, make_token: TokenFactory, jwks_server: JwksServer
) -> None:
    jwks_server.fail = True
    for _ in range(5):
        assert (await client.get(ME, headers=bearer(make_token()))).status_code == 503
    assert jwks_server.calls == 1  # 5 requests, 1 single call to Keycloak


async def test_empty_cache_and_failing_jwks_gives_503_without_immediate_retry(
    jwks_server: JwksServer,
) -> None:
    now = [0.0]
    cache = _cache(jwks_server, now)
    jwks_server.fail = True
    for _ in range(3):
        with pytest.raises(ProblemError) as caught:
            await cache.get("test-key-1")
        assert caught.value.status == 503
    assert jwks_server.calls == 1
    now[0] = 31.0  # the minimum delay has elapsed: a new attempt is allowed
    with pytest.raises(ProblemError):
        await cache.get("test-key-1")
    assert jwks_server.calls == 2


async def test_stale_keys_served_after_a_failure_then_503_beyond_max_stale(
    jwks_server: JwksServer, capsys: pytest.CaptureFixture[str]
) -> None:
    now = [0.0]
    cache = _cache(jwks_server, now, max_stale=3600)
    await cache.get("test-key-1")
    jwks_server.fail = True
    now[0] = 601.0  # TTL exceeded, Keycloak down: the previous keys are still used
    assert (await cache.get("test-key-1")).key is not None
    assert jwks_server.calls == 2
    assert "jwks_stale_keys_used" in capsys.readouterr().out
    for _ in range(3):  # no retry during the minimum delay
        await cache.get("test-key-1")
    assert jwks_server.calls == 2
    now[0] = 600 + 3600 + 1  # beyond TTL + max_stale
    with pytest.raises(ProblemError) as caught:
        await cache.get("test-key-1")
    assert caught.value.status == 503


async def test_unknown_kid_during_an_outage_gives_401_while_keys_are_fresh(
    jwks_server: JwksServer,
) -> None:
    now = [0.0]
    cache = _cache(jwks_server, now)
    await cache.get("test-key-1")
    jwks_server.fail = True
    now[0] = 40.0
    with pytest.raises(ProblemError) as caught:
        await cache.get("unknown")
    assert caught.value.status == 401


async def test_rejected_algorithm_is_detected_before_the_key_and_logged(
    client: httpx.AsyncClient,
    key: TestKey,
    jwks_server: JwksServer,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Without the header check, the reason would be `invalid_signature` or other, and the JWKS
    would be called: this test fails if the `alg` check is removed."""
    now = int(time.time())
    claims = {"iss": "x", "aud": "collector-api", "sub": "u", "exp": now + 60}
    token = jwt.encode(claims, None, algorithm="none", headers={"kid": key.kid})
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))
    logs = capsys.readouterr().out
    assert '"reason": "invalid_algorithm"' in logs
    assert jwks_server.calls == 0


async def test_swagger_ui_removed_and_openapi_json_kept(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/v1/docs")).status_code == 404
    assert (await client.get("/docs")).status_code == 404
    assert (await client.get("/redoc")).status_code == 404
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert response.json()["openapi"].startswith("3.")


def test_uvicorn_logs_as_json(capsys: pytest.CaptureFixture[str]) -> None:
    import logging

    from catalog.main import create_app
    from tests.conftest import build_settings

    create_app(build_settings())
    logging.getLogger("uvicorn.error").info("Application startup complete.")
    logging.getLogger("uvicorn").info("Started server process")
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    entries = [json.loads(line) for line in lines]  # raises if a line is not JSON
    assert {e["event"] for e in entries} == {
        "Application startup complete.",
        "Started server process",
    }
    assert all(e["level"] == "info" and "timestamp" in e for e in entries)


async def test_unexpected_exception_while_loading_jwks_gives_503_not_500(
    client: httpx.AsyncClient, make_token: TokenFactory, jwks_server: JwksServer
) -> None:
    """D-C: an exception that `_fetch` did not foresee (here a RuntimeError) gives a 503."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise RuntimeError("unexpected failure")

    jwks = JwksCache(JWKS_URL, 600, 30, transport=httpx.MockTransport(handler))
    with pytest.raises(ProblemError) as raised:
        await jwks.get("test-key-1")
    assert raised.value.status == 503


async def test_jwks_timeout_is_configurable_and_defaults_to_2_seconds() -> None:
    """D-A: the delay passed to httpx comes from the `timeout` parameter (2 s by default)."""
    seen: list[float | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.extensions["timeout"]["read"])
        return httpx.Response(200, json={"keys": []})

    default = JwksCache(JWKS_URL, 600, 30, transport=httpx.MockTransport(handler))
    custom = JwksCache(JWKS_URL, 600, 30, timeout=0.5, transport=httpx.MockTransport(handler))
    for cache in (default, custom):
        with pytest.raises(ProblemError):  # no key: 401 `unknown_kid`
            await cache.get("kid")
    assert seen == [2.0, 0.5]
    assert Settings.model_fields["jwks_timeout_seconds"].default == 2.0


@pytest.mark.parametrize("value", [0, 0.5, -1])
def test_minimum_reload_delay_below_1_second_is_rejected(value: float) -> None:
    """D-B: rejected at startup (the construction of `Settings` fails)."""
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://u:p@h/db",
            rabbitmq_url="amqp://u:p@h/",
            jwks_min_refetch_seconds=value,
        )


def test_minimum_reload_delay_of_1_second_is_accepted() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://u:p@h/db",
        rabbitmq_url="amqp://u:p@h/",
        jwks_min_refetch_seconds=1,
    )
    assert settings.jwks_min_refetch_seconds == 1


FRONT = "https://app.test.invalid"


@pytest.mark.parametrize(
    ("method", "path", "kwargs", "status"),
    [
        ("GET", "/health/live", {}, 200),
        ("GET", ME, {}, 401),
        ("GET", "/api/v1/unknown", {}, 404),
        ("POST", "/api/v1/_probe/body", {"json": {"name": "ok", "extra_field": "x"}}, 422),
    ],
)
async def test_cors_and_request_id_on_normal_and_error_responses(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    kwargs: dict[str, Any],
    status: int,
) -> None:
    response = await client.request(method, path, headers={"Origin": FRONT}, **kwargs)
    assert response.status_code == status
    assert response.headers["access-control-allow-origin"] == FRONT
    assert response.headers["x-request-id"]
    exposed = response.headers["access-control-expose-headers"].lower()
    assert "x-request-id" in exposed


async def test_cors_403_carries_the_cors_headers_and_x_request_id(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await client.get(
        "/api/v1/_probe/admin", headers={**bearer(make_token()), "Origin": FRONT}
    )
    assert response.status_code == 403
    assert response.headers["access-control-allow-origin"] == FRONT
    assert response.headers["x-request-id"]
    assert "x-request-id" in response.headers["access-control-expose-headers"].lower()


async def test_cors_valid_x_request_id_is_kept_on_an_error(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/unknown", headers={"Origin": FRONT, "X-Request-ID": "req-123.abc_9"}
    )
    assert response.status_code == 404
    assert response.headers["x-request-id"] == "req-123.abc_9"
    assert response.json()["correlation_id"] == "req-123.abc_9"


async def test_cors_options_preflight_request_accepted(client: httpx.AsyncClient) -> None:
    response = await client.options(
        ME,
        headers={
            "Origin": FRONT,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, X-Request-ID",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONT
    allowed = response.headers["access-control-allow-headers"].lower()
    assert "authorization" in allowed
    assert "x-request-id" in allowed


async def test_cors_rejected_origin_without_cors_header_but_with_x_request_id(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(ME, headers={"Origin": "https://evil.test.invalid"})
    assert response.status_code == 401
    assert "access-control-allow-origin" not in response.headers
    assert response.headers["x-request-id"]
