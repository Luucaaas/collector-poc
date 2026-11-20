"""Login through the Authorization Code + PKCE S256 flow of the public client `collector-web`.

This module only holds the pure parts (computations and text parsing), testable without network.
The HTTP exchanges are in `session.py`.

Why this flow rather than a direct password client: the load test must go through exactly what
the browser goes through, without adding to Keycloak a client that would weaken the realm (ADR
of phase 8). A Locust user therefore behaves like the web page: it asks for authorization,
fills in the Keycloak form, gets the `code` from the redirect and exchanges it for tokens with
the `code_verifier`.
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

# Renewal margin: the access token lasts 5 minutes, it is renewed when less than a minute is
# left. A request sent just before expiry therefore never leaves with an expired token, even if
# the Keycloak response is slow.
REFRESH_MARGIN_SECONDS = 60.0


def pkce_pair() -> tuple[str, str]:
    """Returns (code_verifier, code_challenge) for the S256 method (RFC 7636).

    The `code_verifier` is a random secret of 43 characters (32 bytes in unpadded base64url). The
    `code_challenge` is its SHA-256 digest, encoded the same way: only the digest goes out in the
    first request, the secret is only revealed when the code is exchanged.
    """
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")
    return verifier, challenge_for(verifier)


def challenge_for(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


class _LoginFormParser(HTMLParser):
    """Picks the `action` attribute of the Keycloak login form (`kc-form-login`)."""

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
    """Address to send the login form to (the HTML parser already decodes `&amp;`).

    The address contains a `session_code` and a `tab_id` specific to this attempt: it cannot be
    guessed, it has to be read from the page.
    """
    parser = _LoginFormParser()
    parser.feed(page)
    if parser.action is None:
        raise ValueError("Keycloak login form not found in the page.")
    return html.unescape(parser.action)


def extract_code(location: str, expected_state: str) -> str:
    """Reads the `code` from the `Location` header of the final Keycloak redirect.

    Checks the `state`: it is the flow's protection against cross-site request forgery
    (RFC 6749 §10.12), the test honors it as the real client would.
    """
    query = parse_qs(urlsplit(location).query)
    if "error" in query:
        raise ValueError(f"Keycloak refused the authorization: {query['error'][0]}.")
    if query.get("state", [None])[0] != expected_state:
        raise ValueError("The state parameter of the redirect does not match.")
    codes = query.get("code")
    if not codes:
        raise ValueError("No authorization code in the redirect.")
    return codes[0]


@dataclass(frozen=True)
class Tokens:
    access_token: str
    refresh_token: str
    expires_at: float  # monotonic clock (time.monotonic), expiry instant of the access token


def parse_token_response(payload: dict[str, Any], now: float | None = None) -> Tokens:
    """Builds the tokens from the response of the `/token` endpoint."""
    current = time.monotonic() if now is None else now
    return Tokens(
        access_token=str(payload["access_token"]),
        refresh_token=str(payload["refresh_token"]),
        expires_at=current + float(payload["expires_in"]),
    )


def needs_refresh(tokens: Tokens, now: float, margin: float = REFRESH_MARGIN_SECONDS) -> bool:
    """True when the access token has less than `margin` seconds left."""
    return tokens.expires_at - now <= margin
