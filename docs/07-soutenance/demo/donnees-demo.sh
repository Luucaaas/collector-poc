#!/usr/bin/env bash
# Demo dataset: 5 categories, one shop per seller (alice, bob),
# 11 credible articles, and chloe who follows the "Figurines" category.
#
#   docs/07-soutenance/demo/donnees-demo.sh
#
# Rerunnable without duplicates (nothing is recreated if it already exists). The data is created through the public
# API, with the real PKCE login flow (like the browser): this is what the
# catalogue shows during the demo.
#
# CLEAN CATALOGUE: the API has no deletion, so test data (Playwright "E2E" walkthrough,
# "Charge" load test) is not erased. The simplest solution is to rebuild
# a fresh cluster the day before (cluster.sh delete, create, deploy.sh all <tag>), then to run this
# script. If the catalogue contains something other than the demo set, the script says so and exits
# with code 3.
#
# Passwords are read from deploy/local/.env and given only to the Python process as a command
# prefix: never displayed, never as an argument, never written.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${HERE}/../../.." && pwd)"
ENV_FILE="${ROOT}/deploy/local/.env"

# Value of a .env key, never displayed; missing or empty key: message and stop.
read_var() {
  grep -m1 -E "^$1=" "$ENV_FILE" | cut -d= -f2- | grep . \
    || { echo "Key $1 missing or empty in deploy/local/.env." >&2; return 1; }
}

command -v uv >/dev/null || { echo "uv is required (brew install uv)." >&2; exit 1; }
command -v mkcert >/dev/null || { echo "mkcert is required." >&2; exit 1; }
[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env not found: is the cluster deployed?" >&2; exit 1; }
admin_pw="$(read_var ADMIN_PASSWORD)"; alice_pw="$(read_var ALICE_PASSWORD)"
bob_pw="$(read_var BOB_PASSWORD)"; chloe_pw="$(read_var CHLOE_PASSWORD)"
# Cluster authority: TLS verification is never disabled.
REQUESTS_CA_BUNDLE="$(mkcert -CAROOT)/rootCA.pem"
[[ -f "$REQUESTS_CA_BUNDLE" ]] || { echo "mkcert authority not found (was mkcert -install done?)." >&2; exit 1; }
export REQUESTS_CA_BUNDLE

# `uv run --project` uses the tests/load environment (requests comes from Locust).
DEMO_ADMIN_PASSWORD="$admin_pw" DEMO_ALICE_PASSWORD="$alice_pw" \
DEMO_BOB_PASSWORD="$bob_pw" DEMO_CHLOE_PASSWORD="$chloe_pw" \
  uv run --quiet --project "${ROOT}/tests/load" python -u "${HERE}/donnees_demo.py"
