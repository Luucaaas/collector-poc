"""Configuration du service, lue dans les variables d'environnement (jamais dans le dépôt)."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables d'environnement du service.

    `DATABASE_URL` n'a pas de valeur par défaut : il contient un mot de passe et vient d'un Secret
    Kubernetes (ou du `.env` local, ignoré par git).
    """

    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = Field(
        description="URL SQLAlchemy, ex. postgresql+psycopg://user:***@host/notification_db"
    )
    rabbitmq_url: str = Field(
        description="URL AMQP, ex. amqp://user:***@host:5672/ (Secret Kubernetes)"
    )
    # Messages non acquittés que le broker confie au consommateur (contrats.md §3.1).
    consumer_prefetch: int = Field(default=10, ge=1)
    # Délai entre deux tentatives de connexion à RabbitMQ tant que le broker est absent.
    amqp_retry_seconds: float = Field(default=1.0, gt=0)
    issuer: str = "https://auth.127.0.0.1.sslip.io/realms/collector"
    jwks_url: str = (
        "http://keycloak.collector.svc.cluster.local:8080"
        "/realms/collector/protocol/openid-connect/certs"
    )
    audience: str = "collector-api"
    cors_origin: str = "https://app.127.0.0.1.sslip.io"
    jwks_ttl_seconds: float = 600.0
    # Borne basse : un délai nul ou négatif ferait rappeler Keycloak à chaque requête.
    jwks_min_refetch_seconds: float = Field(default=30.0, ge=1)
    jwks_max_stale_seconds: float = 3600.0
    # Le verrou du cache est tenu pendant l'appel : un délai court limite l'attente des requêtes.
    jwks_timeout_seconds: float = Field(default=2.0, gt=0)
    db_connect_timeout_seconds: int = 3
    log_level: str = "INFO"
