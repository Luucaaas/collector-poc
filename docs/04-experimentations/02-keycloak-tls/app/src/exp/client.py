"""Test client of experiment 2: obtains tokens and replays the authorization matrix.

The Keycloak `collector-tests*` clients use the "Resource Owner Password" flow: it is an
artifact of the experiment (discouraged by RFC 9700, it is not the front end's flow).

Subcommands:
- matrix: from the Mac, through the public URLs (HTTPS, mkcert CA), authorization matrix;
- burst: from the Mac, N requests with the same valid token (counts the JWKS calls);
- iss-internal: from the cluster, token obtained through Keycloak's internal URL, then API call.

Passwords come from the `<USER>_PASSWORD` environment variables. No full token is written:
only claims are displayed.
"""

import base64
import json
import os
import ssl
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

REALM_PATH = "/realms/collector/protocol/openid-connect/token"
KC_PUBLIC = os.environ.get("KC_PUBLIC", "https://auth.127.0.0.1.sslip.io")
KC_INTERNAL = os.environ.get(
    "KC_INTERNAL", "http://keycloak-service.keycloak.svc.cluster.local:8080"
)
API_PUBLIC = os.environ.get("API_PUBLIC", "https://api.127.0.0.1.sslip.io/exp")
API_INTERNAL = os.environ.get("API_INTERNAL", "http://exp-api.exp.svc.cluster.local:8000")


def get_token(client: httpx.Client, base: str, client_id: str, user: str) -> str:
    response = client.post(
        base + REALM_PATH,
        data={
            "grant_type": "password",
            "client_id": client_id,
            "username": user,
            "password": os.environ[f"{user.upper()}_PASSWORD"],
        },
    )
    response.raise_for_status()
    return str(response.json()["access_token"])


def claims_of(token: str) -> dict[str, Any]:
    """Claims without signature verification (display only)."""
    claims: dict[str, Any] = jwt.decode(token, options={"verify_signature": False})
    return claims


def describe(token: str) -> dict[str, Any]:
    claims = claims_of(token)
    return {
        "iss": claims["iss"],
        "aud": claims.get("aud"),
        "azp": claims.get("azp"),
        "roles": claims.get("realm_access", {}).get("roles"),
        "lifespan_s": claims["exp"] - claims["iat"],
    }


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def altered_signature(token: str) -> str:
    header, payload, signature = token.split(".")
    middle = len(signature) // 2
    flipped = "A" if signature[middle] != "A" else "B"
    return ".".join([header, payload, signature[:middle] + flipped + signature[middle + 1 :]])


def signed_by_other_key(token: str, kid: str) -> str:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return jwt.encode(claims_of(token), key, algorithm="RS256", headers={"kid": kid})


def alg_none(token: str) -> str:
    header = json.dumps(
        {"alg": "none", "typ": "JWT", "kid": jwt.get_unverified_header(token)["kid"]}
    )
    return b64url(header.encode()) + "." + token.split(".")[1] + "."


@dataclass
class Case:
    name: str
    path: str
    token: str | None
    expected: int


def call(client: httpx.Client, path: str, token: str | None, request_id: str) -> int:
    headers = {"X-Request-ID": request_id}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return client.get(API_PUBLIC + path, headers=headers).status_code


def host_client() -> httpx.Client:
    context = ssl.create_default_context(cafile=os.environ["CA_FILE"])
    return httpx.Client(verify=context, timeout=15)


def matrix() -> int:
    with host_client() as client:
        tokens = {
            user: get_token(client, KC_PUBLIC, "collector-tests", user)
            for user in ("alice", "bob", "chloe", "admin")
        }
        noaud = get_token(client, KC_PUBLIC, "collector-tests-noaud", "alice")
        short = get_token(client, KC_PUBLIC, "collector-tests-short", "alice")
        print("ISS_PUBLIC", json.dumps(describe(tokens["chloe"])))
        print("TOKEN_NO_AUDIENCE", json.dumps(describe(noaud)))
        print("SHORT_TOKEN", json.dumps(describe(short)))
        kid = jwt.get_unverified_header(tokens["chloe"])["kid"]
        cases = [
            Case("/public without token", "/api/v1/public", None, 200),
            Case("/me without token", "/api/v1/me", None, 401),
            Case("chloe (buyer) on /me", "/api/v1/me", tokens["chloe"], 200),
            Case("chloe (buyer) on /seller", "/api/v1/seller", tokens["chloe"], 403),
            Case("bob (seller) on /seller", "/api/v1/seller", tokens["bob"], 200),
            Case("alice (seller, buyer) on /seller", "/api/v1/seller", tokens["alice"], 200),
            Case("admin on /seller", "/api/v1/seller", tokens["admin"], 403),
            Case("token without collector-api audience", "/api/v1/me", noaud, 401),
            Case("altered signature", "/api/v1/me", altered_signature(tokens["chloe"]), 401),
            Case(
                "signed by another key (unknown kid)",
                "/api/v1/me",
                signed_by_other_key(tokens["chloe"], "other-key"),
                401,
            ),
            Case(
                "signed by another key (realm kid)",
                "/api/v1/me",
                signed_by_other_key(tokens["chloe"], kid),
                401,
            ),
            Case("none algorithm", "/api/v1/me", alg_none(tokens["chloe"]), 401),
            Case("/health/live probe through the ingress", "/health/live", None, 404),
            Case("short token, before expiry", "/api/v1/me", short, 200),
        ]
        results: list[tuple[str, str, int, int]] = []
        for number, case in enumerate(cases, start=1):
            request_id = f"exp2-case-{number:02d}"
            results.append(
                (
                    request_id,
                    case.name,
                    case.expected,
                    call(client, case.path, case.token, request_id),
                )
            )
        # Short token replayed after its expiry (token exp, plus a 2 s margin).
        wait = claims_of(short)["exp"] + 2 - time.time()
        print(f"Waiting {max(wait, 0):.0f} s for the short token to expire...", flush=True)
        time.sleep(max(wait, 0))
        request_id = f"exp2-case-{len(cases) + 1:02d}"
        results.append(
            (
                request_id,
                "short token, after expiry",
                401,
                call(client, "/api/v1/me", short, request_id),
            )
        )
    print()
    print(f"{'X-Request-ID':<16}{'Case':<44}{'Expected':>8}{'Got':>8}  Verdict")
    ok = 0
    for request_id, name, expected, got in results:
        verdict = "OK" if expected == got else "MISMATCH"
        ok += expected == got
        print(f"{request_id:<16}{name:<44}{expected:>8}{got:>8}  {verdict}")
    print(f"MATRIX {ok}/{len(results)} cases as expected")
    return 0 if ok == len(results) else 1


def burst(count: int) -> int:
    with host_client() as client:
        token = get_token(client, KC_PUBLIC, "collector-tests", "chloe")
        statuses = [call(client, "/api/v1/me", token, f"exp2-burst-{i:03d}") for i in range(count)]
    print(f"BURST {count} /me requests with the same token: {statuses.count(200)} 200 responses")
    return 0 if statuses.count(200) == count else 1


def iss_internal() -> int:
    with httpx.Client(timeout=15) as client:
        token = get_token(client, KC_INTERNAL, "collector-tests", "chloe")
        status = client.get(
            API_INTERNAL + "/api/v1/me",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Request-ID": f"exp2-iss-{uuid.uuid4()}",
            },
        ).status_code
    print("ISS_INTERNAL", json.dumps(describe(token)))
    print(f"API_AFTER_INTERNAL_TOKEN status {status}")
    return 0 if status == 200 else 1


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "matrix":
        return matrix()
    if command == "burst":
        return burst(int(sys.argv[2]))
    if command == "iss-internal":
        return iss_internal()
    print("usage: python -m exp.client matrix | burst N | iss-internal", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
