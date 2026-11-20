"""HTTP exchanges with Keycloak: login through the PKCE flow and token renewal.

Requests go through the Locust client (`HttpSession`) to share its TLS settings: certificate
verification stays on, the mkcert authority is provided by the `REQUESTS_CA_BUNDLE` variable of
`run.sh`. They carry a name prefixed « [connexion] »: they appear in the CSV files but are
excluded from the thresholds (thresholds.is_load_request).
"""

import secrets
import time
from typing import Any

from locust.clients import HttpSession

import config
from auth import (
    Tokens,
    extract_code,
    extract_form_action,
    needs_refresh,
    parse_token_response,
    pkce_pair,
)

LOGIN = "[connexion]"


class LoginError(RuntimeError):
    pass


def login(client: HttpSession, username: str, password: str) -> Tokens:
    """Authorization Code + PKCE S256 like the web page does, with the Keycloak form."""
    verifier, challenge = pkce_pair()
    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(16)
    params = {
        "client_id": config.CLIENT_ID,
        "redirect_uri": config.REDIRECT_URI,
        "response_type": "code",
        "scope": "openid profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    page = client.get(f"{config.KEYCLOAK}/auth", params=params, name=f"{LOGIN} page d'autorisation")
    if page.status_code != 200:
        raise LoginError(f"authorization page: HTTP {page.status_code}")
    action = extract_form_action(page.text)

    # allow_redirects=False: the redirect leads to the web page (app.), which is not loaded;
    # only the `code` is read from the Location header.
    submit = client.post(
        action,
        data={"username": username, "password": password, "credentialId": ""},
        allow_redirects=False,
        name=f"{LOGIN} formulaire",
    )
    if submit.status_code != 302:
        raise LoginError(f"login form: HTTP {submit.status_code}")
    code = extract_code(submit.headers.get("Location", ""), state)

    reply = client.post(
        f"{config.KEYCLOAK}/token",
        data={
            "grant_type": "authorization_code",
            "client_id": config.CLIENT_ID,
            "redirect_uri": config.REDIRECT_URI,
            "code": code,
            "code_verifier": verifier,
        },
        name=f"{LOGIN} échange du code",
    )
    if reply.status_code != 200:
        raise LoginError(f"code exchange: HTTP {reply.status_code}")
    return parse_token_response(reply.json())


def refresh(client: HttpSession, tokens: Tokens) -> Tokens:
    reply = client.post(
        f"{config.KEYCLOAK}/token",
        data={
            "grant_type": "refresh_token",
            "client_id": config.CLIENT_ID,
            "refresh_token": tokens.refresh_token,
        },
        name=f"{LOGIN} renouvellement",
    )
    if reply.status_code != 200:
        raise LoginError(f"renewal: HTTP {reply.status_code}")
    return parse_token_response(reply.json())


class TokenHolder:
    """Token of a simulated user, renewed with the refresh token before it expires.

    Renewal is checked on every request (`headers`), without a timer: a user who waits 10 s
    between two actions never lets the token expire unnoticed.
    """

    def __init__(self, client: HttpSession, username: str) -> None:
        self._client = client
        self._username = username
        self._tokens = login(client, username, config.password_for(username))

    def headers(self) -> dict[str, Any]:
        if needs_refresh(self._tokens, time.monotonic()):
            self._tokens = refresh(self._client, self._tokens)
        return {"Authorization": f"Bearer {self._tokens.access_token}"}
