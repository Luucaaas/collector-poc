#!/usr/bin/env bash
# Starts the POC's local stack (PostgreSQL, RabbitMQ, Keycloak, catalog and notification).
#   ./up.sh              builds the service images then starts
#   ./up.sh --no-build   uses the CATALOG_IMAGE and NOTIFICATION_IMAGE already present (CI)
# Creates .env on first run (random passwords, never overwritten), renders the
# configuration files into rendered/ (ignored by git), then waits until all the probes are healthy.
set -euo pipefail
cd "$(dirname "$0")"

BUILD=(--build)
[[ "${1:-}" == "--no-build" ]] && BUILD=()
WAIT_TIMEOUT="${WAIT_TIMEOUT:-300}"   # seconds

command -v docker >/dev/null || { echo "Docker is required." >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo "Docker is not responding: start Docker Desktop." >&2; exit 1; }

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
  echo ".env file created with generated passwords (not shown, ignored by git)."
else
  echo "Existing .env file kept."
fi

python3 render.py .env rendered
echo "Files rendered in rendered/ (Keycloak realm with test client, RabbitMQ definitions)."

docker compose up -d ${BUILD[@]+"${BUILD[@]}"} --wait --wait-timeout "$WAIT_TIMEOUT"
docker compose ps

cat <<'MSG'

Stack ready. Access (127.0.0.1 only):
  catalog-service       http://localhost:8001/api/v1/categories   (docs: /api/v1/docs)
  notification-service  http://localhost:8002/health/ready
  Keycloak              http://localhost:8080   (collector realm, administrator: admin)
  RabbitMQ management   http://localhost:15672  (user admin)
Passwords: deploy/compose/.env. Stop: ./down.sh (or ./down.sh --volumes to erase everything).
MSG
