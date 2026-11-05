"""Tests de sécurité : validation des JWT, rôles, erreurs RFC 9457, corrélation, journaux."""

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
    """PyJWT refuse de signer en HS256 avec une clé publique : on forge le jeton à la main."""
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
    assert "detail" not in body  # la raison du rejet n'est jamais dans la réponse
    assert body["correlation_id"] == response.headers["x-request-id"]


async def test_jeton_valide_donne_200_avec_sub_et_roles(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await client.get(ME, headers=bearer(make_token()))
    assert response.status_code == 200
    assert response.json() == {"sub": "user-1", "roles": ["buyer"]}


async def test_jeton_absent_donne_401(client: httpx.AsyncClient) -> None:
    assert_unauthenticated(await client.get(ME))


async def test_schema_autre_que_bearer_donne_401(client: httpx.AsyncClient) -> None:
    assert_unauthenticated(await client.get(ME, headers={"Authorization": "Basic abc"}))


async def test_jeton_mal_forme_donne_401(client: httpx.AsyncClient) -> None:
    assert_unauthenticated(await client.get(ME, headers=bearer("pas-un-jwt")))


async def test_mauvais_issuer_donne_401(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    token = make_token(iss="https://evil.test.invalid/realms/collector")
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


async def test_mauvaise_audience_donne_401(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    assert_unauthenticated(await client.get(ME, headers=bearer(make_token(aud="autre-api"))))


async def test_jeton_expire_donne_401(client: httpx.AsyncClient, make_token: TokenFactory) -> None:
    token = make_token(exp=int(time.time()) - 10)
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


@pytest.mark.parametrize("claim", ["exp", "iss", "aud", "sub"])
async def test_claim_obligatoire_absent_donne_401(
    client: httpx.AsyncClient, make_token: TokenFactory, claim: str
) -> None:
    token = make_token(remove=(claim,))
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


async def test_signature_alteree_donne_401(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    header, payload, signature = make_token().split(".")
    flipped = ("A" if signature[0] != "A" else "B") + signature[1:]
    assert_unauthenticated(await client.get(ME, headers=bearer(f"{header}.{payload}.{flipped}")))


async def test_charge_alteree_donne_401(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    header, payload, signature = make_token().split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=="))
    claims["realm_access"] = {"roles": ["admin"]}
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    assert_unauthenticated(await client.get(ME, headers=bearer(f"{header}.{forged}.{signature}")))


async def test_jeton_signe_par_une_autre_cle_avec_le_meme_kid_donne_401(
    client: httpx.AsyncClient, make_token: TokenFactory, key: TestKey
) -> None:
    attacker = TestKey(key.kid)  # même `kid`, autre paire de clés
    assert_unauthenticated(await client.get(ME, headers=bearer(make_token(signing_key=attacker))))


async def test_kid_inconnu_donne_401(
    client: httpx.AsyncClient, make_token: TokenFactory, other_key: TestKey
) -> None:
    token = make_token(signing_key=other_key)
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


async def test_kid_absent_donne_401(client: httpx.AsyncClient, key: TestKey) -> None:
    now = int(time.time())
    claims = {"iss": "x", "aud": "collector-api", "sub": "u", "exp": now + 60}
    token = jwt.encode(claims, key.private, algorithm="RS256")  # aucun `kid`
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


async def test_algorithme_none_donne_401(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    now = int(time.time())
    claims = {"iss": "x", "aud": "collector-api", "sub": "u", "exp": now + 60}
    token = jwt.encode(claims, None, algorithm="none", headers={"kid": "test-key-1"})
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


async def test_algorithme_hs256_signe_avec_la_cle_publique_donne_401(
    client: httpx.AsyncClient, key: TestKey
) -> None:
    """Attaque par confusion d'algorithme : HS256 avec le JWK public comme secret."""
    now = int(time.time())
    claims = {"iss": "x", "aud": "collector-api", "sub": "u", "exp": now + 60}
    token = _forge_hs256(claims, json.dumps(key.jwk).encode(), key.kid)
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


@pytest.mark.parametrize(
    "realm_access",
    ["buyer", ["buyer"], {"roles": "buyer"}, {"roles": ["buyer", 7]}],
)
async def test_realm_access_mal_forme_donne_401_et_non_500(
    client: httpx.AsyncClient, make_token: TokenFactory, realm_access: Any
) -> None:
    token = make_token(realm_access=realm_access)
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))


async def test_sub_non_texte_donne_401(client: httpx.AsyncClient, make_token: TokenFactory) -> None:
    assert_unauthenticated(await client.get(ME, headers=bearer(make_token(sub=42))))


async def test_sub_vide_donne_401(client: httpx.AsyncClient, make_token: TokenFactory) -> None:
    assert_unauthenticated(await client.get(ME, headers=bearer(make_token(sub=""))))


async def test_role_manquant_donne_403(client: httpx.AsyncClient, make_token: TokenFactory) -> None:
    response = await client.get("/api/v1/_probe/admin", headers=bearer(make_token()))
    assert response.status_code == 403
    body = response.json()
    assert body["title"] == "Accès refusé"
    assert body["type"] == "https://collector.shop/problems/forbidden"
    assert "detail" not in body


async def test_role_present_donne_200(client: httpx.AsyncClient, make_token: TokenFactory) -> None:
    token = make_token(realm_access={"roles": ["admin"]})
    response = await client.get("/api/v1/_probe/admin", headers=bearer(token))
    assert response.status_code == 200


async def test_jwks_en_echec_donne_503(
    client: httpx.AsyncClient, make_token: TokenFactory, jwks_server: JwksServer
) -> None:
    jwks_server.fail = True
    response = await client.get(ME, headers=bearer(make_token()))
    assert response.status_code == 503
    assert response.json()["title"] == "Service d'identité indisponible"


@pytest.mark.parametrize(
    "body",
    [
        "pas un objet",
        {"autre": []},
        {"keys": "non"},
        {"keys": ["non"]},
        {"keys": [{"kty": "RSA", "use": "sig", "kid": "k", "n": "!", "e": "AQAB"}]},
        {"keys": [{"kty": "RSA", "use": "sig", "n": "AQAB", "e": "AQAB"}]},  # sans `kid`
    ],
)
async def test_jwks_mal_forme_donne_503_et_non_500(
    client: httpx.AsyncClient, make_token: TokenFactory, jwks_server: JwksServer, body: Any
) -> None:
    jwks_server.body = body
    response = await client.get(ME, headers=bearer(make_token()))
    assert response.status_code == 503
    assert response.json()["title"] == "Service d'identité indisponible"


async def test_jwks_est_mis_en_cache(
    client: httpx.AsyncClient, make_token: TokenFactory, jwks_server: JwksServer
) -> None:
    for _ in range(5):
        assert (await client.get(ME, headers=bearer(make_token()))).status_code == 200
    assert jwks_server.calls == 1


async def test_kid_inconnu_ne_recharge_le_jwks_qu_une_fois_par_delai_minimal(
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
    for _ in range(3):  # rafale de `kid` inconnus : aucun rechargement avant 30 s
        with pytest.raises(ProblemError):
            await cache.get("inconnu")
    assert jwks_server.calls == 1
    now[0] = 31.0
    jwks_server.keys.append(other_key)
    assert (await cache.get("other-key")).key is not None
    assert jwks_server.calls == 2


async def test_cache_jwks_expire_apres_le_ttl(jwks_server: JwksServer) -> None:
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


async def test_corps_avec_champ_inconnu_donne_422_rfc_9457(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await client.post(
        "/api/v1/_probe/body", json={"name": "ok", "intrus": "valeur-sensible"}
    )
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"] == "https://collector.shop/problems/validation-error"
    assert body["title"] == "Données invalides"
    assert body["errors"] == [{"field": "intrus", "code": "EXTRA_FORBIDDEN"}]
    assert body["correlation_id"] == response.headers["x-request-id"]
    assert "valeur-sensible" not in response.text


async def test_route_inconnue_donne_404_rfc_9457(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/inconnue")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["title"] == "Ressource introuvable"


async def test_erreur_inattendue_donne_500_sans_detail_interne(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/_probe/boom", headers={"X-Request-ID": "req-500"})
    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["x-request-id"] == "req-500"
    body = response.json()
    assert body["title"] == "Erreur interne"
    assert body["correlation_id"] == "req-500"
    assert "secret interne" not in response.text
    assert "RuntimeError" not in response.text


async def test_request_id_valide_est_repris(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/live", headers={"X-Request-ID": "mon-id.42_A"})
    assert response.headers["x-request-id"] == "mon-id.42_A"


@pytest.mark.parametrize("value", ["a" * 129, "avec espace", "a;b", "<b>"])
async def test_request_id_trop_long_ou_invalide_est_remplace(
    client: httpx.AsyncClient, value: str
) -> None:
    response = await client.get("/health/live", headers={"X-Request-ID": value})
    assert response.headers["x-request-id"] != value
    assert len(response.headers["x-request-id"]) == 36  # UUID


async def test_une_ligne_de_log_json_par_requete_avec_correlation_id(
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


async def test_aucun_jeton_ni_raison_dans_les_reponses_et_les_logs(
    client: httpx.AsyncClient, make_token: TokenFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    token = make_token(aud="autre-api")
    response = await client.get(ME, headers=bearer(token))
    logs = capsys.readouterr().out
    assert token not in logs
    assert token.split(".")[1] not in logs
    assert "invalid_audience" in logs  # la raison est dans les logs...
    assert "invalid_audience" not in response.text  # ... et seulement là


async def test_cors_autorise_uniquement_l_origine_du_front(client: httpx.AsyncClient) -> None:
    allowed = await client.get("/health/live", headers={"Origin": "https://app.test.invalid"})
    refused = await client.get("/health/live", headers={"Origin": "https://evil.test.invalid"})
    assert allowed.headers["access-control-allow-origin"] == "https://app.test.invalid"
    assert "access-control-allow-origin" not in refused.headers


async def test_metrics_expose_l_histogramme_avec_les_bornes_de_i3(
    client: httpx.AsyncClient, app: FastAPI
) -> None:
    await client.get("/api/v1/inconnue")
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


async def test_jwks_en_echec_n_est_pas_rappele_pendant_le_delai_minimal(
    client: httpx.AsyncClient, make_token: TokenFactory, jwks_server: JwksServer
) -> None:
    jwks_server.fail = True
    for _ in range(5):
        assert (await client.get(ME, headers=bearer(make_token()))).status_code == 503
    assert jwks_server.calls == 1  # 5 requêtes, 1 seul appel à Keycloak


async def test_cache_vide_et_jwks_en_echec_donne_503_sans_rappel_immediat(
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
    now[0] = 31.0  # le délai minimal est écoulé : une nouvelle tentative est permise
    with pytest.raises(ProblemError):
        await cache.get("test-key-1")
    assert jwks_server.calls == 2


async def test_cles_perimees_servies_apres_un_echec_puis_503_au_dela_de_max_stale(
    jwks_server: JwksServer, capsys: pytest.CaptureFixture[str]
) -> None:
    now = [0.0]
    cache = _cache(jwks_server, now, max_stale=3600)
    await cache.get("test-key-1")
    jwks_server.fail = True
    now[0] = 601.0  # TTL dépassé, Keycloak en panne : les clés précédentes restent utilisées
    assert (await cache.get("test-key-1")).key is not None
    assert jwks_server.calls == 2
    assert "jwks_stale_keys_used" in capsys.readouterr().out
    for _ in range(3):  # pas de rappel pendant le délai minimal
        await cache.get("test-key-1")
    assert jwks_server.calls == 2
    now[0] = 600 + 3600 + 1  # au-delà de TTL + max_stale
    with pytest.raises(ProblemError) as caught:
        await cache.get("test-key-1")
    assert caught.value.status == 503


async def test_kid_inconnu_pendant_une_panne_donne_401_tant_que_les_cles_sont_fraiches(
    jwks_server: JwksServer,
) -> None:
    now = [0.0]
    cache = _cache(jwks_server, now)
    await cache.get("test-key-1")
    jwks_server.fail = True
    now[0] = 40.0
    with pytest.raises(ProblemError) as caught:
        await cache.get("inconnu")
    assert caught.value.status == 401


async def test_algorithme_refuse_est_detecte_avant_la_cle_et_journalise(
    client: httpx.AsyncClient,
    key: TestKey,
    jwks_server: JwksServer,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Sans le contrôle de l'en-tête, la raison serait `invalid_signature` ou autre, et le JWKS
    serait appelé : ce test échoue si le contrôle `alg` est supprimé."""
    now = int(time.time())
    claims = {"iss": "x", "aud": "collector-api", "sub": "u", "exp": now + 60}
    token = jwt.encode(claims, None, algorithm="none", headers={"kid": key.kid})
    assert_unauthenticated(await client.get(ME, headers=bearer(token)))
    logs = capsys.readouterr().out
    assert '"reason": "invalid_algorithm"' in logs
    assert jwks_server.calls == 0


async def test_swagger_ui_retire_et_openapi_json_conserve(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/v1/docs")).status_code == 404
    assert (await client.get("/docs")).status_code == 404
    assert (await client.get("/redoc")).status_code == 404
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert response.json()["openapi"].startswith("3.")


def test_logs_d_uvicorn_en_json(capsys: pytest.CaptureFixture[str]) -> None:
    import logging

    from catalog.main import create_app
    from tests.conftest import build_settings

    create_app(build_settings())
    logging.getLogger("uvicorn.error").info("Application startup complete.")
    logging.getLogger("uvicorn").info("Started server process")
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    entries = [json.loads(line) for line in lines]  # lève si une ligne n'est pas du JSON
    assert {e["event"] for e in entries} == {
        "Application startup complete.",
        "Started server process",
    }
    assert all(e["level"] == "info" and "timestamp" in e for e in entries)


async def test_exception_imprevue_du_chargement_jwks_donne_503_et_non_500(
    client: httpx.AsyncClient, make_token: TokenFactory, jwks_server: JwksServer
) -> None:
    """D-C : une exception que `_fetch` ne prévoyait pas (ici un RuntimeError) donne un 503."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise RuntimeError("panne imprévue")

    jwks = JwksCache(JWKS_URL, 600, 30, transport=httpx.MockTransport(handler))
    with pytest.raises(ProblemError) as raised:
        await jwks.get("test-key-1")
    assert raised.value.status == 503


async def test_le_timeout_du_jwks_est_configurable_et_vaut_2_secondes_par_defaut() -> None:
    """D-A : le délai transmis à httpx vient du paramètre `timeout` (2 s par défaut)."""
    seen: list[float | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.extensions["timeout"]["read"])
        return httpx.Response(200, json={"keys": []})

    default = JwksCache(JWKS_URL, 600, 30, transport=httpx.MockTransport(handler))
    custom = JwksCache(JWKS_URL, 600, 30, timeout=0.5, transport=httpx.MockTransport(handler))
    for cache in (default, custom):
        with pytest.raises(ProblemError):  # aucune clé : 401 `unknown_kid`
            await cache.get("kid")
    assert seen == [2.0, 0.5]
    assert Settings.model_fields["jwks_timeout_seconds"].default == 2.0


@pytest.mark.parametrize("value", [0, 0.5, -1])
def test_delai_minimal_de_rechargement_inferieur_a_1_seconde_est_refuse(value: float) -> None:
    """D-B : rejeté au démarrage (la construction de `Settings` échoue)."""
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://u:p@h/db",
            rabbitmq_url="amqp://u:p@h/",
            jwks_min_refetch_seconds=value,
        )


def test_delai_minimal_de_rechargement_de_1_seconde_est_accepte() -> None:
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
        ("GET", "/api/v1/inconnue", {}, 404),
        ("POST", "/api/v1/_probe/body", {"json": {"name": "ok", "intrus": "x"}}, 422),
    ],
)
async def test_cors_et_request_id_sur_les_reponses_normales_et_d_erreur(
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


async def test_cors_403_porte_les_en_tetes_cors_et_x_request_id(
    client: httpx.AsyncClient, make_token: TokenFactory
) -> None:
    response = await client.get(
        "/api/v1/_probe/admin", headers={**bearer(make_token()), "Origin": FRONT}
    )
    assert response.status_code == 403
    assert response.headers["access-control-allow-origin"] == FRONT
    assert response.headers["x-request-id"]
    assert "x-request-id" in response.headers["access-control-expose-headers"].lower()


async def test_cors_x_request_id_valide_est_repris_sur_une_erreur(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/inconnue", headers={"Origin": FRONT, "X-Request-ID": "req-123.abc_9"}
    )
    assert response.status_code == 404
    assert response.headers["x-request-id"] == "req-123.abc_9"
    assert response.json()["correlation_id"] == "req-123.abc_9"


async def test_cors_requete_preliminaire_options_acceptee(client: httpx.AsyncClient) -> None:
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


async def test_cors_origine_refusee_sans_en_tete_cors_mais_avec_x_request_id(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(ME, headers={"Origin": "https://evil.test.invalid"})
    assert response.status_code == 401
    assert "access-control-allow-origin" not in response.headers
    assert response.headers["x-request-id"]
