"""Configuration des tests : URL de la pile et mots de passe lus dans le `.env` de la pile.

Tout se change par variable d'environnement ; les valeurs par défaut visent la pile locale lancée
par `deploy/compose/up.sh`.
"""

import os
from pathlib import Path
from urllib.parse import quote

REPO = Path(__file__).resolve().parents[2]

CATALOG_URL = os.environ.get("ACCEPTANCE_CATALOG_URL", "http://localhost:8001").rstrip("/")
NOTIFICATION_URL = os.environ.get("ACCEPTANCE_NOTIFICATION_URL", "http://localhost:8002").rstrip(
    "/"
)
KEYCLOAK_URL = os.environ.get("ACCEPTANCE_KEYCLOAK_URL", "http://localhost:8080").rstrip("/")
ENV_FILE = Path(os.environ.get("ACCEPTANCE_ENV_FILE", REPO / "deploy/compose/.env"))
AMQP_HOST = os.environ.get("ACCEPTANCE_AMQP_HOST", "localhost:5672")

REALM = "collector"
TEST_CLIENT = "collector-tests"
EXCHANGE = "article.events"


def read_env(path: Path = ENV_FILE) -> dict[str, str]:
    if not path.exists():
        raise RuntimeError(f"Fichier {path} introuvable : lancer deploy/compose/up.sh d'abord.")
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def amqp_url(env: dict[str, str]) -> str:
    """URL AMQP de l'administrateur RabbitMQ (il peut déclarer une file temporaire)."""
    explicit = os.environ.get("ACCEPTANCE_AMQP_URL")
    if explicit:
        return explicit
    return f"amqp://admin:{quote(env['RABBITMQ_ADMIN_PASSWORD'], safe='')}@{AMQP_HOST}/"
