#!/usr/bin/env bash
# Runs the Playwright journeys against the k3d cluster (https://app.127.0.0.1.sslip.io).
# The demo account passwords are read from deploy/local/.env and exported into
# the environment of this process only: they are never displayed, passed as arguments or written.
# The mkcert certificate must be trusted by Chromium (mkcert -install done): TLS verification
# is never disabled.
#   ./run-cluster.sh               the 6 journeys
#   CAPTURES=1 ./run-cluster.sh    the screenshot spec (e2e/resultats/captures/)
#   ./run-cluster.sh -g "alice"    options of `playwright test`
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE="../deploy/local/.env"
[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env not found: has the cluster been deployed (deploy/local/deploy.sh)?" >&2; exit 1; }

# Value of a .env key, never displayed; missing key: explicit message and stop.
read_var() {
  grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | grep . \
    || { echo "Key $1 missing or empty in deploy/local/.env." >&2; return 1; }
}

E2E_ADMIN_PASSWORD="$(read_var ADMIN_PASSWORD)"
E2E_ALICE_PASSWORD="$(read_var ALICE_PASSWORD)"
E2E_CHLOE_PASSWORD="$(read_var CHLOE_PASSWORD)"
export E2E_ADMIN_PASSWORD E2E_ALICE_PASSWORD E2E_CHLOE_PASSWORD
export E2E_BASE_URL="https://app.127.0.0.1.sslip.io"

curl -fsS -o /dev/null "$E2E_BASE_URL/" || { echo "$E2E_BASE_URL is not responding (or certificate not trusted): is the cluster running?" >&2; exit 1; }
curl -fsS -o /dev/null "https://auth.127.0.0.1.sslip.io/realms/collector/.well-known/openid-configuration" || { echo "https://auth.127.0.0.1.sslip.io is not responding: is Keycloak ready?" >&2; exit 1; }

exec npx playwright test "$@"
