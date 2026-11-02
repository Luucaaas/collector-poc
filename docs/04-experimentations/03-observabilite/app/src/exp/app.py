"""Application de test : trois routes aux comportements connus, instrumentée pour Prometheus.

- GET /items : réponse immédiate ;
- GET /slow  : attente fixe de SLOW_SECONDS (200 ms) ;
- GET /fail  : réponse 500.

Les métriques sont exposées sur /metrics, les journaux sont des lignes JSON (structlog) qui
portent l'identifiant de corrélation X-Request-ID (contrats.md §1).
"""

import asyncio
import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator, metrics

SLOW_SECONDS = 0.2

# Bornes de l'histogramme « fin » : plus serrées autour de l'attente de 200 ms que celles de
# la bibliothèque (0,1 / 0,5 / 1 s pour http_request_duration_seconds).
FINE_BUCKETS = (0.05, 0.1, 0.2, 0.25, 0.3, 0.5, 1, 2.5)

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
)
logger = structlog.get_logger()

app = FastAPI(title="Application de test de l'observabilité")

# /metrics et les sondes /health ne sont pas comptées : seules les requêtes de la charge le sont.
(
    Instrumentator(excluded_handlers=["/metrics", "/health/.*"])
    .add(metrics.default())
    .add(
        metrics.latency(
            metric_name="http_request_duration_fine_seconds",
            metric_doc="Durée des requêtes HTTP, bornes serrées autour de 200 ms",
            buckets=FINE_BUCKETS,
        )
    )
    .instrument(app)
    .expose(app, include_in_schema=False)
)


@app.middleware("http")
async def correlation_and_log(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Reprend ou génère X-Request-ID, le renvoie, et journalise chaque requête en JSON."""
    correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = correlation_id
    if not request.url.path.startswith(("/health", "/metrics")):
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )
    return response


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/items")
async def items() -> dict[str, list[int]]:
    return {"items": [1, 2, 3]}


@app.get("/slow")
async def slow() -> dict[str, float]:
    await asyncio.sleep(SLOW_SECONDS)
    return {"waited_s": SLOW_SECONDS}


@app.get("/fail")
async def fail() -> JSONResponse:
    return JSONResponse({"detail": "échec volontaire"}, status_code=500)
