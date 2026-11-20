"""Prometheus metrics (`/metrics`).

Histogram duration buckets: 0.3 s and 0.5 s are exactly the thresholds of indicator I3, which
makes it possible to check the threshold without interpolation. With the library's default
buckets (0.1 / 0.5 / 1 s), a real p95 of 200 ms is read as 480 ms (+140 %), against 247 ms
(+23.7 %) with tight buckets (experiment protocol 3, §5 and §7).
"""

from fastapi import FastAPI
from prometheus_client import CollectorRegistry, Counter
from prometheus_fastapi_instrumentator import Instrumentator, metrics

LATENCY_BUCKETS = (0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5)


class BusinessMetrics:
    """Business counters (contrats.md §2.3), in the application's registry."""

    def __init__(self, registry: CollectorRegistry) -> None:
        self.articles_published = Counter(
            "articles_published_total", "Published articles", registry=registry
        )
        self.articles_rejected = Counter(
            "articles_rejected_total", "Rejected articles, by reason", ["reason"], registry=registry
        )
        self.price_changes = Counter(
            "price_changes_total", "Effective price changes", registry=registry
        )


def setup_metrics(app: FastAPI) -> None:
    # One registry per application: `create_app()` can be called several times (tests).
    registry = CollectorRegistry()
    app.state.business_metrics = BusinessMetrics(registry)
    instrumentator = Instrumentator(excluded_handlers=["/metrics", "/health/.*"], registry=registry)
    instrumentator.add(metrics.requests(registry=registry))
    instrumentator.add(metrics.latency(buckets=LATENCY_BUCKETS, registry=registry))
    instrumentator.instrument(app)
    instrumentator.expose(app, include_in_schema=False)
