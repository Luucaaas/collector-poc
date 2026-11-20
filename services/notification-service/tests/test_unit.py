"""Unit tests: X-Request-ID, conversion to RFC 9457, role extraction."""

import uuid

import pytest
from pydantic import ValidationError

from notification.auth import extract_roles
from notification.correlation import resolve_request_id
from notification.errors import ProblemError, problem_body, validation_errors
from notification.schemas import ApiModel


def test_valid_request_id_is_kept() -> None:
    assert resolve_request_id("abc-123_X.y") == "abc-123_X.y"


def test_128_character_request_id_is_kept() -> None:
    value = "a" * 128
    assert resolve_request_id(value) == value


@pytest.mark.parametrize(
    "value", [None, "", "a" * 129, "with space", "carriage\nreturn", "<script>", "é"]
)
def test_missing_or_invalid_request_id_is_replaced_by_a_uuid(value: str | None) -> None:
    result = resolve_request_id(value)
    assert result != value
    uuid.UUID(result)


def test_problem_error_takes_the_default_title_of_the_status() -> None:
    error = ProblemError(403)
    assert error.title == "Accès refusé"


def test_problem_body_follows_the_rfc_9457_format() -> None:
    body = problem_body(422, "Données invalides", "Détail", [{"field": "price", "code": "X"}])
    assert body["type"] == "https://collector.shop/problems/validation-error"
    assert body["status"] == 422
    assert body["errors"] == [{"field": "price", "code": "X"}]
    assert "correlation_id" in body


def test_validation_errors_does_not_copy_the_received_value() -> None:
    class Model(ApiModel):
        name: str

    with pytest.raises(ValidationError) as caught:
        Model.model_validate({"name": "ok", "secret": "sensitive-value"})
    errors = validation_errors(caught.value.errors())
    assert errors == [{"field": "secret", "code": "EXTRA_FORBIDDEN"}]
    assert "sensitive-value" not in str(errors)


def test_extract_roles_reads_realm_access() -> None:
    assert extract_roles({"realm_access": {"roles": ["buyer", "seller"]}}) == {"buyer", "seller"}


def test_extract_roles_without_realm_access_gives_no_role() -> None:
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
def test_extract_roles_malformed_gives_401(claims: dict[str, object]) -> None:
    with pytest.raises(ProblemError) as caught:
        extract_roles(claims)
    assert caught.value.status == 401
