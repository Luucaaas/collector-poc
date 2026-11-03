"""Tests unitaires : X-Request-ID, conversion en RFC 9457, extraction des rôles."""

import uuid

import pytest
from pydantic import ValidationError

from catalog.auth import extract_roles
from catalog.correlation import resolve_request_id
from catalog.errors import ProblemError, problem_body, validation_errors
from catalog.schemas import ApiModel


def test_request_id_valide_est_repris() -> None:
    assert resolve_request_id("abc-123_X.y") == "abc-123_X.y"


def test_request_id_de_128_caracteres_est_repris() -> None:
    value = "a" * 128
    assert resolve_request_id(value) == value


@pytest.mark.parametrize(
    "value", [None, "", "a" * 129, "avec espace", "retour\nligne", "<script>", "é"]
)
def test_request_id_absent_ou_invalide_est_remplace_par_un_uuid(value: str | None) -> None:
    result = resolve_request_id(value)
    assert result != value
    uuid.UUID(result)


def test_problem_error_prend_le_titre_par_defaut_du_statut() -> None:
    error = ProblemError(403)
    assert error.title == "Accès refusé"


def test_problem_body_respecte_le_format_rfc_9457() -> None:
    body = problem_body(422, "Données invalides", "Détail", [{"field": "price", "code": "X"}])
    assert body["type"] == "https://collector.shop/problems/validation-error"
    assert body["status"] == 422
    assert body["errors"] == [{"field": "price", "code": "X"}]
    assert "correlation_id" in body


def test_validation_errors_ne_recopie_pas_la_valeur_recue() -> None:
    class Model(ApiModel):
        name: str

    with pytest.raises(ValidationError) as caught:
        Model.model_validate({"name": "ok", "secret": "valeur-sensible"})
    errors = validation_errors(caught.value.errors())
    assert errors == [{"field": "secret", "code": "EXTRA_FORBIDDEN"}]
    assert "valeur-sensible" not in str(errors)


def test_extract_roles_lit_realm_access() -> None:
    assert extract_roles({"realm_access": {"roles": ["buyer", "seller"]}}) == {"buyer", "seller"}


def test_extract_roles_sans_realm_access_donne_aucun_role() -> None:
    assert extract_roles({}) == frozenset()


@pytest.mark.parametrize(
    "claims",
    [
        {"realm_access": "seller"},
        {"realm_access": ["seller"]},
        {"realm_access": {"roles": "seller"}},
        {"realm_access": {"roles": ["seller", 3]}},
    ],
)
def test_extract_roles_mal_forme_donne_401(claims: dict[str, object]) -> None:
    with pytest.raises(ProblemError) as caught:
        extract_roles(claims)
    assert caught.value.status == 401
