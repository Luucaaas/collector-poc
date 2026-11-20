"""ASGI middleware: correlation identifier, access log and safety net for 500s.

Written as pure ASGI (and not `BaseHTTPMiddleware`) so that structlog's context variables
stay visible in the routes and the error handlers, and to also catch unexpected
exceptions: the 500 response then carries `X-Request-ID` as well.
"""

import re
import time
import uuid
from collections.abc import MutableMapping
from typing import Any

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from notification.errors import problem_response

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,128}")
_QUIET_PATHS = ("/health", "/metrics")  # probes and scraping: logged at DEBUG only

logger = structlog.get_logger()


def resolve_request_id(value: str | None) -> str:
    """Takes the supplied identifier if it is valid (at most 128 characters of `[A-Za-z0-9._-]`),
    otherwise generates one: an arbitrary value must not enter the logs."""
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
