"""Erreurs au format RFC 9457 (`application/problem+json`), contrats.md §1.3."""

from collections.abc import Sequence
from http import HTTPStatus
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_BASE = "https://collector.shop/problems"
PROBLEM_MEDIA_TYPE = "application/problem+json"

logger = structlog.get_logger()

_TITLES = {
    401: "Non authentifié",
    403: "Accès refusé",
    404: "Ressource introuvable",
    405: "Méthode non autorisée",
    409: "Conflit",
    422: "Données invalides",
    500: "Erreur interne",
    503: "Service indisponible",
}
_SLUGS = {
    401: "unauthenticated",
    403: "forbidden",
    404: "not-found",
    409: "conflict",
    422: "validation-error",
    500: "internal-error",
    503: "service-unavailable",
}


class ProblemError(Exception):
    """Erreur applicative renvoyée telle quelle au client.

    `reason` n'est écrit que dans les journaux, jamais dans la réponse : pour un 401, la raison du
    rejet (signature, `iss`, expiration, etc.) ne doit pas aider un attaquant.
    """

    def __init__(
        self,
        status: int,
        *,
        title: str | None = None,
        detail: str | None = None,
        errors: list[dict[str, str]] | None = None,
        reason: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(reason or title or str(status))
        self.status = status
        self.title = title or _TITLES.get(status, HTTPStatus(status).phrase)
        self.detail = detail
        self.errors = errors
        self.reason = reason
        self.headers = headers


def unauthenticated(reason: str) -> ProblemError:
    """Titre unique pour tous les 401 ; la raison reste dans les journaux."""
    return ProblemError(401, reason=reason, headers={"WWW-Authenticate": "Bearer"})


def forbidden(reason: str) -> ProblemError:
    return ProblemError(403, reason=reason)


def problem_body(
    status: int,
    title: str,
    detail: str | None = None,
    errors: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": f"{PROBLEM_BASE}/{_SLUGS.get(status, 'error')}",
        "title": title,
        "status": status,
    }
    if detail is not None:
        body["detail"] = detail
    if errors is not None:
        body["errors"] = errors
    body["correlation_id"] = structlog.contextvars.get_contextvars().get("correlation_id")
    return body


def problem_response(
    status: int,
    title: str,
    detail: str | None = None,
    errors: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        problem_body(status, title, detail, errors),
        status_code=status,
        media_type=PROBLEM_MEDIA_TYPE,
        headers=headers,
    )


def validation_errors(errors: Sequence[Any]) -> list[dict[str, str]]:
    """Convertit les erreurs Pydantic en `{field, code}`, sans jamais recopier la valeur reçue."""
    result = []
    for error in errors:
        location = [str(part) for part in error["loc"] if part not in ("body", "query", "path")]
        result.append({"field": ".".join(location), "code": str(error["type"]).upper()})
    return result


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProblemError)
    async def handle_problem(request: Request, error: ProblemError) -> JSONResponse:
        if error.reason is not None:
            logger.warning(
                "request_rejected", status=error.status, reason=error.reason, path=request.url.path
            )
        return problem_response(
            error.status, error.title, error.detail, error.errors, error.headers
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, error: RequestValidationError) -> JSONResponse:
        return problem_response(
            422,
            _TITLES[422],
            "La requête contient des données invalides.",
            validation_errors(error.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(request: Request, error: StarletteHTTPException) -> JSONResponse:
        title = _TITLES.get(error.status_code, HTTPStatus(error.status_code).phrase)
        return problem_response(error.status_code, title, headers=dict(error.headers or {}))
