"""Journaux JSON (structlog). `correlation_id` et `sub` viennent du contexte.

Les journaux d'uvicorn (démarrage, arrêt, erreurs) passent par le même rendu JSON, pour que
`docker logs` et Loki ne reçoivent que du JSON. Le journal d'accès d'uvicorn est désactivé
(`--no-access-log`) : le middleware de corrélation écrit déjà une ligne par requête.
"""

import logging as std_logging
import sys

import structlog


def configure_logging(level: str = "INFO") -> None:
    numeric_level = std_logging.getLevelName(level.upper())
    shared: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.format_exc_info,
    ]
    structlog.configure(
        processors=[*shared, structlog.processors.JSONRenderer()],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
    )

    # Journaux de la bibliothèque standard (uvicorn) rendus par structlog, en JSON.
    handler = std_logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
        )
    )
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = std_logging.getLogger(name)
        logger.handlers = []
        logger.propagate = False
        logger.setLevel(numeric_level)
    std_logging.getLogger("uvicorn").addHandler(handler)
    std_logging.getLogger("uvicorn.error").propagate = True
