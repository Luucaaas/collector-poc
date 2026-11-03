"""Métriques Prometheus (`/metrics`).

Bornes de l'histogramme de durée : 0,3 s et 0,5 s sont exactement les seuils de l'indicateur I3, ce
qui permet de vérifier le seuil sans interpolation. Avec les bornes par défaut de la bibliothèque
(0,1 / 0,5 / 1 s), un p95 réel de 200 ms est lu à 480 ms (+140 %), contre 247 ms (+23,7 %) avec des
bornes serrées (protocole d'expérimentation 3, §5 et §7).
"""

from fastapi import FastAPI
from prometheus_client import CollectorRegistry, Counter
from prometheus_fastapi_instrumentator import Instrumentator, metrics

LATENCY_BUCKETS = (0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5)


class BusinessMetrics:
    """Compteurs métier (contrats.md §2.3), dans le registre de l'application.

    `outcome` de `events_consumed_total` : `processed`, `requeued` (première erreur, remis en
    file), `rejected` (deuxième erreur, abandonné), `invalid` (JSON ou schéma non conforme) ou
    `ignored` (type d'événement inconnu, acquitté sans traitement).
    """

    def __init__(self, registry: CollectorRegistry) -> None:
        self.notifications_created = Counter(
            "notifications_created_total",
            "Notifications créées, par type",
            ["type"],
            registry=registry,
        )
        self.events_consumed = Counter(
            "events_consumed_total",
            "Événements reçus de RabbitMQ, par type et résultat",
            ["event_type", "outcome"],
            registry=registry,
        )


def setup_metrics(app: FastAPI) -> None:
    # Un registre par application : `create_app()` peut être appelée plusieurs fois (tests).
    registry = CollectorRegistry()
    app.state.business_metrics = BusinessMetrics(registry)
    instrumentator = Instrumentator(excluded_handlers=["/metrics", "/health/.*"], registry=registry)
    instrumentator.add(metrics.requests(registry=registry))
    instrumentator.add(metrics.latency(buckets=LATENCY_BUCKETS, registry=registry))
    instrumentator.instrument(app)
    instrumentator.expose(app, include_in_schema=False)
