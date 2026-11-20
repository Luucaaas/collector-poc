#!/usr/bin/env bash
# Reference run of the load test on the k3d cluster (indicator I3 and requirement ENF-14).
#
#   tests/load/run.sh                      50 users, ramp-up of 1 per second, 6 minutes
#   USERS=20 RUN_TIME=2m tests/load/run.sh short trial (optional variables: USERS,
#                                          SPAWN_RATE, RUN_TIME)
#
# What the script does, in order:
#   1. reads the passwords of admin, alice, bob and chloe from deploy/local/.env and gives them to
#      the Locust command only (assignments as a command prefix, no export): never printed,
#      never a command argument, never written to a file;
#   2. checks that the API and Keycloak answer (TLS verification stays on: the mkcert authority
#      is given to Python by REQUESTS_CA_BUNDLE, nothing disables it);
#   3. records in resultats/<YYYYMMDD-HHMM>/ the date, the tag and the digests read from the pods,
#      the HPA state before, during (every 15 s) and after;
#   4. runs Locust headless (CSV files and HTML report);
#   5. queries Prometheus (temporary kubectl port-forward) and writes resume.md;
#   6. replaces in everything archived the machine name with <machine> and the home
#      directory with <home>: these files are versioned.
# On the cluster, the script only does HTTP traffic and reads (kubectl get, port-forward).
# Exit code: 0 even if a measure exceeds its threshold (the test process does not make it a
# blocker); resume.md and the final message say so clearly. Any other code: the test could not
# run.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${HERE}/../.." && pwd)"
ENV_FILE="${ROOT}/deploy/local/.env"
CTX="k3d-collector"
K="kubectl --context ${CTX} -n collector"
API="https://api.127.0.0.1.sslip.io"
AUTH="https://auth.127.0.0.1.sslip.io"
USERS="${USERS:-50}"
SPAWN_RATE="${SPAWN_RATE:-1}"
RUN_TIME="${RUN_TIME:-6m}"
PROM_PORT=19091

[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env not found: was the cluster deployed (deploy/local/deploy.sh)?" >&2; exit 1; }
command -v uv >/dev/null || { echo "uv is required (brew install uv)." >&2; exit 1; }
command -v mkcert >/dev/null || { echo "mkcert is required (cluster certificate)." >&2; exit 1; }

# Value of a .env key, never printed; missing key: explicit message and stop.
read_var() {
  grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | grep . \
    || { echo "Key $1 missing or empty in deploy/local/.env." >&2; return 1; }
}
# Shell variables only (no export): only the Locust command receives them, as a prefix.
admin_pw="$(read_var ADMIN_PASSWORD)"
alice_pw="$(read_var ALICE_PASSWORD)"
bob_pw="$(read_var BOB_PASSWORD)"
chloe_pw="$(read_var CHLOE_PASSWORD)"

# mkcert certificate authority: Python does not use the macOS keychain.
export REQUESTS_CA_BUNDLE="$(mkcert -CAROOT)/rootCA.pem"
[[ -f "$REQUESTS_CA_BUNDLE" ]] || { echo "mkcert authority not found (was mkcert -install run?)." >&2; exit 1; }

echo "== Preliminary checks"
curl -fsS --cacert "$REQUESTS_CA_BUNDLE" -o /dev/null "${API}/catalog/api/v1/categories" \
  || { echo "${API}/catalog does not answer: is the cluster running?" >&2; exit 1; }
curl -fsS --cacert "$REQUESTS_CA_BUNDLE" -o /dev/null "${AUTH}/realms/collector/.well-known/openid-configuration" \
  || { echo "${AUTH} does not answer: is Keycloak ready?" >&2; exit 1; }
$K get deploy catalog-service notification-service >/dev/null \
  || { echo "kubectl cannot reach the cluster ${CTX}." >&2; exit 1; }

export LOAD_RUN_ID="$(date +%Y%m%d-%H%M)"
RESULTS="${HERE}/resultats/${LOAD_RUN_ID}"
[[ ! -e "$RESULTS" ]] || { echo "${RESULTS} already exists (wait a minute)." >&2; exit 1; }
mkdir -p "$RESULTS"
export LOAD_RESULTS_DIR="$RESULTS"

sampler="" ; portforward=""
# Anonymizes what is archived: machine name (long and short, case-insensitive) and home
# directory. Idempotent, run again after resume.md is written.
sanitize() {
  local short; short="$(hostname -s)"
  for file in "${RESULTS}"/*; do
    HOST_SHORT="$short" perl -pi -e \
      's/\Q$ENV{HOST_SHORT}\E(?:\.[\w-]+)*/<machine>/gi; s{/Us[e]rs/[^\/\s"\x27]+}{<home>}g' "$file"
  done
}
cleanup() {
  [[ -z "$sampler" ]] || kill "$sampler" 2>/dev/null || true
  [[ -z "$portforward" ]] || kill "$portforward" 2>/dev/null || true
}
trap cleanup EXIT

echo "== Environment and HPA state before"
{
  echo "Date de début : $(date '+%d/%m/%Y %H:%M:%S')"
  echo "Paramètres : ${USERS} utilisateurs, montée de ${SPAWN_RATE} par seconde, durée totale ${RUN_TIME}"
  echo "Cible : ${API} (TLS vérifié) ; Keycloak : ${AUTH}"
  echo "Locust : $(cd "$HERE" && uv run --quiet locust --version | sed 's/ from .*//')"
  echo "Commit du dépôt : $(git -C "$ROOT" rev-parse --short HEAD)"
  echo
  echo "Images déployées :"
  $K get deploy catalog-service notification-service frontend \
    -o jsonpath='{range .items[*]}  {.metadata.name}{"\t"}{.spec.template.spec.containers[0].image}{"\n"}{end}'
  echo
  echo "Digests lus sur les pods :"
  $K get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].imageID}{"\n"}{end}' \
    | grep -E '^(catalog-service|notification-service|frontend)-' | sed 's/^/  /'
} > "${RESULTS}/environnement.txt"
{ echo "HPA avant l'exécution ($(date '+%H:%M:%S')) :"; $K get hpa; } > "${RESULTS}/hpa-avant.txt"

# Replica sampling every 15 s during the run (read-only).
( while true; do
    echo "$(date '+%H:%M:%S')"; $K get hpa --no-headers; sleep 15
  done ) > "${RESULTS}/hpa-evolution.txt" 2>&1 &
sampler=$!
disown "$sampler"

echo "== Locust: ${USERS} users, ${RUN_TIME} (ramp-up of ${SPAWN_RATE}/s, statistics reset at the plateau)"
cd "$HERE"
LOAD_ADMIN_PASSWORD="$admin_pw" LOAD_ALICE_PASSWORD="$alice_pw" \
LOAD_BOB_PASSWORD="$bob_pw" LOAD_CHLOE_PASSWORD="$chloe_pw" \
uv run --quiet locust -f locustfile.py --headless \
  -u "$USERS" -r "$SPAWN_RATE" -t "$RUN_TIME" --reset-stats \
  --csv "${RESULTS}/locust" --html "${RESULTS}/rapport.html" \
  --exit-code-on-error 0 --only-summary 2>&1 | tee "${RESULTS}/locust.log" \
  || true
if [[ ! -f "${RESULTS}/locust_stats.csv" ]] || ! grep -q plateau_start "${RESULTS}/fenetre.json" 2>/dev/null; then
  echo "The plateau was not reached (preparation or login failed): see ${RESULTS}/locust.log." >&2
  exit 1
fi
kill "$sampler" 2>/dev/null || true; sampler=""
{ echo "HPA après l'exécution ($(date '+%H:%M:%S')) :"; $K get hpa; } > "${RESULTS}/hpa-apres.txt"

echo "== Prometheus (port-forward ${PROM_PORT}), waiting for the last scrape"
$K port-forward svc/kps-prometheus "${PROM_PORT}:9090" >/dev/null 2>&1 &
portforward=$!
disown "$portforward"
for _ in $(seq 1 30); do curl -s -o /dev/null --max-time 2 "http://127.0.0.1:${PROM_PORT}/-/ready" && break; sleep 1; done
sleep 35
sanitize
uv run --quiet python report.py "$RESULTS" "http://127.0.0.1:${PROM_PORT}"
sanitize

echo
echo "Results: ${RESULTS}"
if grep -q "Hors seuil" "${RESULTS}/resume.md"; then
  echo "WARNING: at least one measure exceeds its threshold (exit code 0 anyway, see resume.md)."
fi
exit 0
