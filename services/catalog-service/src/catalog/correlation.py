"""Middleware ASGI : identifiant de corrélation, journal d'accès et filet de sécurité des 500.

Écrit en ASGI pur (et non `BaseHTTPMiddleware`) pour que les variables de contexte de structlog
restent visibles dans les routes et les gestionnaires d'erreurs, et pour attraper aussi les
exceptions inattendues : la réponse 500 porte alors elle aussi `X-Request-ID`.
"""

import re
import time
import uuid
from collections.abc import MutableMapping
from typing import Any

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from catalog.errors import problem_response

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,128}")
_QUIET_PATHS = ("/health", "/metrics")  # sondes et collecte : journalisées en DEBUG seulement

logger = structlog.get_logger()


def resolve_request_id(value: str | None) -> str:
    """Reprend l'identifiant fourni s'il est valide (au plus 128 caractères de `[A-Za-z0-9._-]`),
    sinon en génère un : une valeur arbitraire ne doit pas entrer dans les journaux."""
    if value is not None and _VALID_REQUEST_ID.fullmatch(value):
        return value
    return str(uuid.uuid4())


class CorrelationMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        correlation_id = resolve_request_id(Headers(scope=scope).get(REQUEST_ID_HEADER))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        started = time.perf_counter()
        status = 500
        response_started = False

        async def send_with_id(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = correlation_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        except Exception:
            logger.exception("unhandled_error", path=scope["path"])
            if not response_started:
                response = problem_response(500, "Erreur interne")
                status = 500
                await response(scope, receive, send_with_id)
        finally:
            self._log(scope, status, started)
            structlog.contextvars.clear_contextvars()

    @staticmethod
    def _log(scope: MutableMapping[str, Any], status: int, started: float) -> None:
        log = logger.debug if scope["path"].startswith(_QUIET_PATHS) else logger.info
        log(
            "request",
            method=scope["method"],
            path=scope["path"],
            status=status,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )
