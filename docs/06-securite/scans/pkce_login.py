"""Connexion d'alice par le flux Authorization Code + PKCE S256, pour l'audit ZAP.

Réutilise les fonctions pures de tests/load/auth.py (PKCE, lecture du formulaire de Keycloak) : la
connexion traverse exactement ce que traverse le navigateur, sans client en plus dans le realm.

Entrée : variables d'environnement SCAN_USER et SCAN_PASSWORD (jamais en argument de commande),
REQUESTS_CA_BUNDLE (autorité de mkcert, la vérification TLS n'est jamais désactivée).
Sortie : deux lignes sur la sortie standard, le jeton d'accès puis le jeton de rafraîchissement.
run-scans.sh les capture dans des variables du shell sans jamais les afficher. En cas d'échec, le
message ne contient ni mot de passe ni jeton.
"""

import os
import secrets
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests" / "load"))
import auth

KEYCLOAK = "https://auth.127.0.0.1.sslip.io/realms/collector/protocol/openid-connect"
CLIENT_ID = "collector-web"
REDIRECT_URI = "https://app.127.0.0.1.sslip.io/"


def main() -> int:
    user = os.environ.get("SCAN_USER")
    password = os.environ.get("SCAN_PASSWORD")
    if not user or not password:
        print("SCAN_USER et SCAN_PASSWORD doivent être définies.", file=sys.stderr)
        return 1
    verifier, challenge = auth.pkce_pair()
    state = secrets.token_urlsafe(16)
    http = requests.Session()  # garde les cookies de session de Keycloak entre les étapes
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid profile",
        "state": state,
        "nonce": secrets.token_urlsafe(16),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    page = http.get(f"{KEYCLOAK}/auth", params=params, timeout=15)
    if page.status_code != 200:
        print(f"page d'autorisation : HTTP {page.status_code}", file=sys.stderr)
        return 1
    submit = http.post(
        auth.extract_form_action(page.text),
        data={"username": user, "password": password, "credentialId": ""},
        allow_redirects=False,
        timeout=15,
    )
    if submit.status_code != 302:
        print(f"formulaire de connexion : HTTP {submit.status_code}", file=sys.stderr)
        return 1
    code = auth.extract_code(submit.headers.get("Location", ""), state)
    reply = http.post(
        f"{KEYCLOAK}/token",
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code": code,
            "code_verifier": verifier,
        },
        timeout=15,
    )
    if reply.status_code != 200:
        print(f"échange du code : HTTP {reply.status_code}", file=sys.stderr)
        return 1
    tokens = reply.json()
    print(tokens["access_token"])
    print(tokens["refresh_token"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
