#!/usr/bin/env bash
# Runs the Playwright journeys against the docker compose stack (deploy/compose/up.sh already run).
# The demo account passwords are read from deploy/compose/.env and exported into
# the environment of this process only: they are never displayed, passed as arguments or written.
#   ./run-compose.sh              all the journeys
#   ./run-compose.sh -g "alice"   options of `playwright test`
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE="../deploy/compose/.env"
[[ -f "$ENV_FILE" ]] || { echo "deploy/compose/.env not found: run deploy/compose/up.sh first." >&2; exit 1; }

# Value of a .env key, never displayed; missing key: explicit message and stop.
read_var() {
  grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | grep . \
    || { echo "Key $1 missing or empty in deploy/compose/.env." >&2; return 1; }
}

E2E_ADMIN_PASSWORD="$(read_var ADMIN_PASSWORD)"
E2E_ALICE_PASSWORD="$(read_var ALICE_PASSWORD)"
E2E_CHLOE_PASSWORD="$(read_var CHLOE_PASSWORD)"
export E2E_ADMIN_PASSWORD E2E_ALICE_PASSWORD E2E_CHLOE_PASSWORD

curl -fsS -o /dev/null http://localhost:8001/health/ready || { echo "catalog-service is not responding: is the compose stack running?" >&2; exit 1; }

exec npx playwright test "$@"
