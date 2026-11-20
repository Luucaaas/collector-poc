"""Login of alice through the Authorization Code + PKCE S256 flow, for the ZAP audit.

Reuses the pure functions of tests/load/auth.py (PKCE, reading Keycloak's form): the
login goes through exactly what the browser goes through, with no extra client in the realm.

Input: environment variables SCAN_USER and SCAN_PASSWORD (never as a command argument),
REQUESTS_CA_BUNDLE (mkcert authority, TLS verification is never disabled).
Output: two lines on standard output, the access token then the refresh token.
run-scans.sh captures them in shell variables without ever displaying them. On failure, the
message contains neither password nor token.
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
        print("SCAN_USER and SCAN_PASSWORD must be set.", file=sys.stderr)
        return 1
    verifier, challenge = auth.pkce_pair()
    state = secrets.token_urlsafe(16)
    http = requests.Session()  # keeps Keycloak's session cookies between the steps
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
        print(f"authorization page: HTTP {page.status_code}", file=sys.stderr)
        return 1
    submit = http.post(
        auth.extract_form_action(page.text),
        data={"username": user, "password": password, "credentialId": ""},
        allow_redirects=False,
        timeout=15,
    )
    if submit.status_code != 302:
        print(f"login form: HTTP {submit.status_code}", file=sys.stderr)
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
        print(f"code exchange: HTTP {reply.status_code}", file=sys.stderr)
        return 1
    tokens = reply.json()
    print(tokens["access_token"])
    print(tokens["refresh_token"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
