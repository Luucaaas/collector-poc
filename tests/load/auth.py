"""Connexion par le flux Authorization Code + PKCE S256 du client public `collector-web`.

Ce module ne contient que les parties pures (calculs et lecture de texte), testables sans réseau.
Les échanges HTTP sont dans `session.py`.

Pourquoi ce flux plutôt qu'un client à mot de passe direct : le test de charge doit traverser
exactement ce que traverse le navigateur, sans ajouter à Keycloak un client qui affaiblirait le
realm (ADR de la phase 8). Un utilisateur Locust fait donc comme la page web : il demande
l'autorisation, remplit le formulaire de Keycloak, récupère le `code` sur la redirection et
l'échange contre des jetons avec le `code_verifier`.
"""

import base64
import hashlib
import html
import secrets
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qs, urlsplit

# Marge de renouvellement : le jeton d'accès dure 5 minutes, on le renouvelle quand il lui reste
# moins d'une minute. Une requête lancée juste avant l'expiration ne part donc jamais avec un jeton
# périmé, même si la réponse de Keycloak tarde.
REFRESH_MARGIN_SECONDS = 60.0


def pkce_pair() -> tuple[str, str]:
    """Renvoie (code_verifier, code_challenge) pour la méthode S256 (RFC 7636).

    Le `code_verifier` est un secret aléatoire de 43 caractères (32 octets en base64url sans
    remplissage). Le `code_challenge` en est l'empreinte SHA-256, encodée de la même façon : seule
    l'empreinte part dans la première requête, le secret n'est révélé qu'à l'échange du code.
    """
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")
    return verifier, challenge_for(verifier)


def challenge_for(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


class _LoginFormParser(HTMLParser):
    """Relève l'attribut `action` du formulaire de connexion de Keycloak (`kc-form-login`)."""

    def __init__(self) -> None:
        super().__init__()
        self.action: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "form" or self.action is not None:
            return
        values = dict(attrs)
        if values.get("id") == "kc-form-login" and values.get("action"):
            self.action = values["action"]


def extract_form_action(page: str) -> str:
    """Adresse où envoyer le formulaire de connexion (le parseur HTML décode déjà `&amp;`).

    L'adresse contient un `session_code` et un `tab_id` propres à cette tentative : elle ne se
    devine pas, il faut la lire dans la page.
    """
    parser = _LoginFormParser()
    parser.feed(page)
    if parser.action is None:
        raise ValueError("Formulaire de connexion Keycloak introuvable dans la page.")
    return html.unescape(parser.action)


def extract_code(location: str, expected_state: str) -> str:
    """Lit le `code` dans l'en-tête `Location` de la redirection finale de Keycloak.

    Vérifie le `state` : c'est la protection contre la falsification de requête inter-sites du
    flux (RFC 6749 §10.12), le test la respecte comme le ferait le client réel.
    """
    query = parse_qs(urlsplit(location).query)
    if "error" in query:
        raise ValueError(f"Keycloak a refusé l'autorisation : {query['error'][0]}.")
    if query.get("state", [None])[0] != expected_state:
        raise ValueError("Le paramètre state de la redirection ne correspond pas.")
    codes = query.get("code")
    if not codes:
        raise ValueError("Pas de code d'autorisation dans la redirection.")
    return codes[0]


@dataclass(frozen=True)
class Tokens:
    access_token: str
    refresh_token: str
    expires_at: float  # horloge monotone (time.monotonic), instant d'expiration du jeton d'accès


def parse_token_response(payload: dict[str, Any], now: float | None = None) -> Tokens:
    """Construit les jetons depuis la réponse du point de terminaison `/token`."""
    current = time.monotonic() if now is None else now
    return Tokens(
        access_token=str(payload["access_token"]),
        refresh_token=str(payload["refresh_token"]),
        expires_at=current + float(payload["expires_in"]),
    )


def needs_refresh(tokens: Tokens, now: float, margin: float = REFRESH_MARGIN_SECONDS) -> bool:
    """Vrai quand il reste moins de `margin` secondes au jeton d'accès."""
    return tokens.expires_at - now <= margin
