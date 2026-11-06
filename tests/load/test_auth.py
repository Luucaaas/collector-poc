"""Tests des parties pures de la connexion : PKCE, formulaire, redirection, renouvellement."""

import base64
import hashlib

import pytest

import auth

KEYCLOAK_PAGE = """<!DOCTYPE html><html><body>
<form id="kc-form-login" onsubmit="login.disabled = true; return true;"
 action="https://auth.127.0.0.1.sslip.io/realms/collector/login-actions/authenticate?session_code=abc-DEF&amp;execution=1234&amp;client_id=collector-web&amp;tab_id=xyz"
 method="post">
<input id="username" name="username" type="text" />
</form></body></html>"""


def test_challenge_is_sha256_of_verifier_in_base64url() -> None:
    # Vecteur de l'annexe B de la RFC 7636.
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    assert auth.challenge_for(verifier) == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"


def test_pkce_pair_is_consistent_and_random() -> None:
    verifier, challenge = auth.pkce_pair()
    assert 43 <= len(verifier) <= 128
    expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
    assert challenge == expected.rstrip(b"=").decode()
    assert "=" not in challenge
    assert auth.pkce_pair()[0] != verifier


def test_extract_form_action_decodes_entities() -> None:
    action = auth.extract_form_action(KEYCLOAK_PAGE)
    assert action.endswith("session_code=abc-DEF&execution=1234&client_id=collector-web&tab_id=xyz")
    assert "&amp;" not in action


def test_extract_form_action_ignores_other_forms() -> None:
    page = '<form action="/autre"></form>' + KEYCLOAK_PAGE
    assert "login-actions/authenticate" in auth.extract_form_action(page)


def test_extract_form_action_without_form_fails() -> None:
    with pytest.raises(ValueError, match="introuvable"):
        auth.extract_form_action("<html><body>Erreur</body></html>")


def test_extract_code_from_redirect() -> None:
    location = "https://app.127.0.0.1.sslip.io/?state=S1&session_state=x&iss=y&code=the-code.1"
    assert auth.extract_code(location, "S1") == "the-code.1"


def test_extract_code_rejects_wrong_state() -> None:
    with pytest.raises(ValueError, match="state"):
        auth.extract_code("https://app.127.0.0.1.sslip.io/?state=autre&code=c", "S1")


def test_extract_code_reports_keycloak_error() -> None:
    with pytest.raises(ValueError, match="access_denied"):
        auth.extract_code("https://app.127.0.0.1.sslip.io/?error=access_denied&state=S1", "S1")


def test_extract_code_missing_code() -> None:
    with pytest.raises(ValueError, match="code"):
        auth.extract_code("https://app.127.0.0.1.sslip.io/?state=S1", "S1")


def test_parse_token_response_sets_expiry() -> None:
    payload = {"access_token": "a", "refresh_token": "r", "expires_in": 300}
    tokens = auth.parse_token_response(payload, now=1000.0)
    assert tokens.expires_at == 1300.0
    assert (tokens.access_token, tokens.refresh_token) == ("a", "r")


def test_refresh_schedule_uses_margin() -> None:
    tokens = auth.Tokens("a", "r", expires_at=1300.0)
    assert not auth.needs_refresh(tokens, now=1000.0)  # 300 s restantes
    assert not auth.needs_refresh(tokens, now=1239.0)  # 61 s restantes
    assert auth.needs_refresh(tokens, now=1240.0)  # 60 s restantes : on renouvelle
    assert auth.needs_refresh(tokens, now=1400.0)  # déjà expiré
