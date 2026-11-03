"""Métriques Prometheus (`/metrics`).

Bornes de l'histogramme de durée : 0,3 s et 0,5 s sont exactement les seuils de l'indicateur I3, ce
qui permet de vérifier le seuil sans interpolation. Avec les bornes par défaut de la bibliothèque
(0,1 / 0,5 / 1 s), un p95 réel de 200 ms est lu à 480 ms (+140 %), contre 247 ms (+23,7 %) avec des
bornes serrées (protocole d'expérimentation 3, §5 et §7).
"""

from fastapi import FastAPI
from prometheus_client import CollectorRegistry
from prometheus_fastapi_instrumentator import Instrumentator, metrics

LATENCY_BUCKETS = (0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5)


def setup_metrics(app: FastAPI) -> None:
    # Un registre par application : `create_app()` peut être appelée plusieurs fois (tests).
    registry = CollectorRegistry()
    instrumentator = Instrumentator(excluded_handlers=["/metrics", "/health/.*"], registry=registry)
    instrumentator.add(metrics.requests(registry=registry))
    instrumentator.add(metrics.latency(buckets=LATENCY_BUCKETS, registry=registry))
    instrumentator.instrument(app)
    instrumentator.expose(app, include_in_schema=False)
