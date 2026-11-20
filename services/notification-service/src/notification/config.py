"""Service configuration, read from the environment variables (never from the repository)."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment variables of the service.

    `DATABASE_URL` has no default value: it contains a password and comes from a Kubernetes Secret
    (or from the local `.env`, ignored by git).
    """

    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = Field(
        description="URL SQLAlchemy, ex. postgresql+psycopg://user:***@host/notification_db"
    )
    rabbitmq_url: str = Field(
        description="URL AMQP, ex. amqp://user:***@host:5672/ (Secret Kubernetes)"
    )
    # Unacknowledged messages that the broker hands to the consumer (contrats.md §3.1).
    consumer_prefetch: int = Field(default=10, ge=1)
    # Delay between two RabbitMQ connection attempts while the broker is absent.
    amqp_retry_seconds: float = Field(default=1.0, gt=0)
    issuer: str = "https://auth.127.0.0.1.sslip.io/realms/collector"
    jwks_url: str = (
        "http://keycloak.collector.svc.cluster.local:8080"
        "/realms/collector/protocol/openid-connect/certs"
    )
    audience: str = "collector-api"
    cors_origin: str = "https://app.127.0.0.1.sslip.io"
    jwks_ttl_seconds: float = 600.0
    # Lower bound: a zero or negative delay would make Keycloak be called again on every request.
    jwks_min_refetch_seconds: float = Field(default=30.0, ge=1)
    jwks_max_stale_seconds: float = 3600.0
    # The cache lock is held during the call: a short timeout limits how long requests wait.
    jwks_timeout_seconds: float = Field(default=2.0, gt=0)
    db_connect_timeout_seconds: int = 3
    log_level: str = "INFO"
