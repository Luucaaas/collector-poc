#!/usr/bin/env bash
# Lance la pile locale du POC (PostgreSQL, RabbitMQ, Keycloak, catalog et notification).
#   ./up.sh              construit les images des services puis démarre
#   ./up.sh --no-build   utilise CATALOG_IMAGE et NOTIFICATION_IMAGE déjà présentes (CI)
# Crée .env au premier lancement (mots de passe aléatoires, jamais écrasé), rend les fichiers de
# configuration dans rendered/ (ignoré par git), puis attend que toutes les sondes soient saines.
set -euo pipefail
cd "$(dirname "$0")"

BUILD=(--build)
[[ "${1:-}" == "--no-build" ]] && BUILD=()
WAIT_TIMEOUT="${WAIT_TIMEOUT:-300}"   # secondes

command -v docker >/dev/null || { echo "Docker est requis." >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo "Docker ne répond pas : démarrer Docker Desktop." >&2; exit 1; }

if [[ ! -f .env ]]; then
  python3 - <<'PYEOF'
import os
import secrets

lines = []
for line in open(".env.example").read().splitlines():
    if line.endswith("=change-me"):
        line = line.removesuffix("change-me") + secrets.token_urlsafe(18)
    lines.append(line)
with open(".env", "w", opener=lambda path, flags: os.open(path, flags, 0o600)) as out:
    out.write("\n".join(lines) + "\n")
PYEOF
  echo "Fichier .env créé avec des mots de passe générés (non affichés, ignoré par git)."
else
  echo "Fichier .env existant conservé."
fi

python3 render.py .env rendered
echo "Fichiers rendus dans rendered/ (realm Keycloak avec client de test, définitions RabbitMQ)."

docker compose up -d ${BUILD[@]+"${BUILD[@]}"} --wait --wait-timeout "$WAIT_TIMEOUT"
docker compose ps

cat <<'MSG'

Pile prête. Accès (127.0.0.1 seulement) :
  catalog-service       http://localhost:8001/api/v1/categories   (docs : /api/v1/docs)
  notification-service  http://localhost:8002/health/ready
  Keycloak              http://localhost:8080   (realm collector, administrateur : admin)
  RabbitMQ management   http://localhost:15672  (utilisateur admin)
Mots de passe : deploy/compose/.env. Arrêt : ./down.sh (ou ./down.sh --volumes pour tout effacer).
MSG
