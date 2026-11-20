"""Prometheus metrics (`/metrics`).

Histogram duration buckets: 0.3 s and 0.5 s are exactly the thresholds of indicator I3, which
makes it possible to check the threshold without interpolation. With the library's default
buckets (0.1 / 0.5 / 1 s), a real p95 of 200 ms is read as 480 ms (+140 %), against 247 ms
(+23.7 %) with tight buckets (experiment protocol 3, §5 and §7).
"""

from fastapi import FastAPI
from prometheus_client import CollectorRegistry, Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator, metrics

LATENCY_BUCKETS = (0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5)

# Notification delay (ENF-14, p95 < 2 s): 2 s is a bucket bound, so reading the threshold in
# Prometheus relies on no interpolation. 0.5 and 1 s frame the "comfortable" zone below,
# 5 and 10 s tell a moderate delay from a clogged queue above.
NOTIFICATION_DELAY_BUCKETS = (0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0)


class BusinessMetrics:
    """Business counters (contrats.md §2.3), in the application's registry.

    `outcome` of `events_consumed_total`: `processed`, `requeued` (first error, put back in the
    queue), `rejected` (second error, dropped), `invalid` (non-compliant JSON or schema) or
    `ignored` (unknown event type, acknowledged without processing).

    `notification_delay_seconds{event_type}`: delay between the event's `occurred_at` and the
    availability (after the commit) of the notifications it created (ENF-14).
    """

    def __init__(self, registry: CollectorRegistry) -> None:
        self.notifications_created = Counter(
            "notifications_created_total",
            "Notifications created, by type",
            ["type"],
            registry=registry,
        )
        self.events_consumed = Counter(
            "events_consumed_total",
            "Events received from RabbitMQ, by type and outcome",
            ["event_type", "outcome"],
            registry=registry,
        )
        self.notification_delay = Histogram(
            "notification_delay_seconds",
            "Delay between the event (occurred_at) and the notification being available, by type",
            ["event_type"],
            buckets=NOTIFICATION_DELAY_BUCKETS,
            registry=registry,
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
