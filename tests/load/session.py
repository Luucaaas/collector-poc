"""Échanges HTTP avec Keycloak : connexion par le flux PKCE et renouvellement des jetons.

Les requêtes passent par le client de Locust (`HttpSession`) pour partager ses réglages TLS : la
vérification du certificat reste active, l'autorité de mkcert est fournie par la variable
`REQUESTS_CA_BUNDLE` de `run.sh`. Elles portent un nom préfixé « [connexion] » : elles figurent dans
les CSV mais sont exclues des seuils (thresholds.is_load_request).
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
    """Authorization Code + PKCE S256 comme le fait la page web, avec le formulaire de Keycloak."""
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
        raise LoginError(f"page d'autorisation : HTTP {page.status_code}")
    action = extract_form_action(page.text)

    # allow_redirects=False : la redirection mène à la page web (app.), qu'on ne charge pas ;
    # on lit seulement le `code` dans l'en-tête Location.
    submit = client.post(
        action,
        data={"username": username, "password": password, "credentialId": ""},
        allow_redirects=False,
        name=f"{LOGIN} formulaire",
    )
    if submit.status_code != 302:
        raise LoginError(f"formulaire de connexion : HTTP {submit.status_code}")
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
        raise LoginError(f"échange du code : HTTP {reply.status_code}")
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
        raise LoginError(f"renouvellement : HTTP {reply.status_code}")
    return parse_token_response(reply.json())


class TokenHolder:
    """Jeton d'un utilisateur simulé, renouvelé par le jeton de rafraîchissement avant expiration.

    Le renouvellement est vérifié à chaque requête (`headers`), sans minuterie : un utilisateur qui
    attend 10 s entre deux actions ne laisse jamais le jeton expirer sans qu'on le voie.
    """

    def __init__(self, client: HttpSession, username: str) -> None:
        self._client = client
        self._username = username
        self._tokens = login(client, username, config.password_for(username))

    def headers(self) -> dict[str, Any]:
        if needs_refresh(self._tokens, time.monotonic()):
            self._tokens = refresh(self._client, self._tokens)
        return {"Authorization": f"Bearer {self._tokens.access_token}"}
