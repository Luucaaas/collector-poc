"""JSON logs (structlog). `correlation_id` and `sub` come from the context.

uvicorn's logs (startup, shutdown, errors) go through the same JSON rendering, so that
`docker logs` and Loki only receive JSON. uvicorn's access log is disabled
(`--no-access-log`): the correlation middleware already writes one line per request.
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

    # Standard library logs (uvicorn) rendered by structlog, as JSON.
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
    # Specific to this service: the AMQP connection logs (aio-pika, aiormq) also go
    # through the JSON rendering. Otherwise Python writes them as plain text on stderr per attempt.
    for name in ("aio_pika", "aiormq"):
        logger = std_logging.getLogger(name)
        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(max(numeric_level, std_logging.WARNING))
