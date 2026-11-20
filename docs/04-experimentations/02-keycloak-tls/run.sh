#!/usr/bin/env bash
# Experiment 2: Keycloak, Traefik and mkcert TLS on k3d (see protocole.md).
# Creates the cluster (ports 80 and 443 published), configures Traefik (default mkcert certificate,
# HTTP -> HTTPS redirect), installs PostgreSQL and Keycloak (official images) with the realm
# `collector`, deploys a FastAPI API that validates JWTs, measures TLS,
# the redirect, the authorization matrix, `iss`, the JWKS cache and the resources, then deletes
# the cluster.
# Usage: ./run.sh [--keep]   (--keep keeps the cluster at the end)
# The full output is also written to resultats/run-YYYYMMDD-HHMM.log.
# The certificate (private key included) and the generated passwords are written to .local/,
# ignored by Git; they are never displayed.
set -euo pipefail

# --- Pinned versions -------------------------------------------------------------------
K3S_IMAGE="rancher/k3s:v1.35.8-k3s1"
ALPINE_IMAGE="alpine:3.24.3"   # utility image: measures the disk space of the Docker VM
# Infrastructure from official images and simple manifests: no operator, no added CRD,
# no cert-manager (decision of 03/11/2026).
KEYCLOAK_IMAGE="quay.io/keycloak/keycloak:26.8.0"   # read from manifests/keycloak.yaml
POSTGRES_IMAGE="postgres:18.4-alpine"               # read from manifests/postgres.yaml
APP_IMAGE="exp-keycloak-tls-app:local"   # FastAPI 0.142.2, PyJWT 2.14.0, httpx 0.28.1, structlog 26.1.0,
                                         # uvicorn 0.52.4 (see app/uv.lock)

# --- Parameters ------------------------------------------------------------------------
CLUSTER="collector-exp2"
KC_HOST="auth.127.0.0.1.sslip.io"
API_HOST="api.127.0.0.1.sslip.io"
BURST=200      # requests to measure the JWKS cache
KEEP=false
[[ "${1:-}" == "--keep" ]] && KEEP=true

cd "$(dirname "$0")"
MIN_FREE_MB=7000   # the run uses 3.7 GB (53.5 -> 49.8 GB free) and the kubelet evicts below about 3.1 GB free (measured during experiment 3)

# Logs the whole output (without colour codes) to resultats/: the script re-runs
# itself through `tee`.
if [[ -z "${EXP_LOGGING:-}" ]]; then
  export EXP_LOGGING=1
  mkdir -p resultats
  LOG="resultats/run-$(date +%Y%m%d-%H%M).log"
  echo "Full log: ${LOG}"
  ./run.sh "$@" 2>&1 | perl -pe 'BEGIN{$|=1} s/\e\[[0-9;]*m//g' | tee "$LOG"
  exit "${PIPESTATUS[0]}"
fi
K="kubectl --context k3d-${CLUSTER}"
WORK=$(mktemp -d)   # temporary files (rendered realm), removed on exit
export WORK
LOCAL=".local"
CAROOT_DIR="$(mkcert -CAROOT)"
CA_FILE="${CAROOT_DIR}/rootCA.pem"

step() { printf '\n=== %s ===\n' "$*"; }
disk() { echo "Free disk space of the Docker VM ($1): $(docker run --rm "$ALPINE_IMAGE" df -h / | awk 'NR==2 {print $4 " of " $2 " (" $5 " used)"}')"; }

diagnostic() {
  echo "--- Diagnostic (failure): pods and latest events ---"
  $K get pods -A -o wide 2>&1 | tail -n 40 || true
  $K get events -A --sort-by=.lastTimestamp 2>&1 | tail -n 25 || true
}

cleanup() {
  local rc=$?   # exit code of the script, captured before any other command
  rm -rf "$WORK"
  [[ "$rc" -ne 0 ]] && diagnostic
  if [[ "$KEEP" == true ]]; then
    echo "Cluster kept (--keep): k3d cluster delete ${CLUSTER} to remove it."
  else
    step "Deleting the cluster"
    k3d cluster delete "$CLUSTER" || true
    disk "after deleting the cluster"
    echo "--- k3d cluster list (after deletion) ---"
    k3d cluster list || true
  fi
  echo "Exit code of run.sh: ${rc}"
}
trap cleanup EXIT

# Re-runs a command until it succeeds. $1 number of attempts, $2 pause, the rest: command.
retry() {
  local tries="$1" pause="$2"
  shift 2
  for _ in $(seq 1 "$tries"); do
    "$@" && return 0
    sleep "$pause"
  done
  echo "Failed after ${tries} attempts: $*" >&2
  return 1
}

# Reads memory and CPU of the pods (k3s metrics-server). $1 label.
top_all() {
  echo "--- Memory and CPU of the pods ($1) ---"
  local out=""
  for _ in $(seq 1 60); do
    out=$($K top pods -A --no-headers 2>/dev/null | grep -E '^(keycloak|exp|kube-system) ' | grep -E 'keycloak|postgres|exp-api|traefik' || true)
    [[ "$(echo "$out" | grep -c .)" -ge 5 ]] && break
    sleep 3
  done
  echo "$out"
  OUT="$out" LABEL="$1" python3 - <<'PYEOF'
import os

groups = {
    "keycloak-": "Keycloak",
    "postgres-0": "PostgreSQL",
    "exp-api": "Test API",
    "traefik": "Traefik",
}
sums: dict[str, tuple[float, float]] = {}
for line in os.environ["OUT"].splitlines():
    p = line.split()
    if len(p) < 4:
        continue
    pod, cpu, mem = p[1], float(p[2].rstrip("m")), p[3]
    value = float(mem[:-2]) * {"Ki": 1 / 1024, "Mi": 1, "Gi": 1024}[mem[-2:]]
    for prefix, label in groups.items():
        if pod.startswith(prefix):
            c, m = sums.get(label, (0.0, 0.0))
            sums[label] = (c + cpu, m + value)
print(f"RESOURCES ({os.environ['LABEL']})")
for label, (c, m) in sums.items():
    print(f"  {label:<28}{m:>7.0f} Mi{c:>7.0f} m CPU")
total_m = sum(m for _, m in sums.values())
total_c = sum(c for c, _ in sums.values())
print(f"  {'TOTAL':<28}{total_m:>7.0f} Mi{total_c:>7.0f} m CPU")
PYEOF
}

# --- 0. Prerequisites and environment ---------------------------------------------------------
step "0. Prerequisites and environment"
for tool in docker k3d kubectl uv python3 perl curl openssl mkcert lsof; do
  command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
done
docker info >/dev/null
[[ -f "$CA_FILE" ]] || { echo "mkcert CA not found: run mkcert -install (outside this script)" >&2; exit 1; }
date "+Run date:%d/%m/%Y %H:%M"
echo "macOS $(sw_vers -productVersion) $(uname -m) ; host Python $(python3 --version | cut -d' ' -f2) ; $(uv --version | cut -d' ' -f1-2)"
echo "Docker moteur $(docker version --format '{{.Server.Version}}') ; $(docker info --format '{{.NCPU}} CPU, {{.MemTotal}} bytes of memory')"
k3d version | head -1
kubectl version --client | head -1
echo "mkcert $(mkcert -version) ; $(openssl version) ; $(curl --version | head -1 | cut -d' ' -f1-4)"
echo "k3s image ${K3S_IMAGE} ; ${KEYCLOAK_IMAGE} ; ${POSTGRES_IMAGE}"
for port in 80 443; do
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Host port ${port} is already in use:" >&2
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >&2 || true
    exit 1
  fi
done
echo "Host ports 80 and 443: free"
FREE_MB=$(docker run --rm "$ALPINE_IMAGE" df -m / | awk 'NR==2 {print $4}')
disk "before"
if [[ "$FREE_MB" -lt "$MIN_FREE_MB" ]]; then
  echo "Insufficient disk space: ${FREE_MB} MB free, ${MIN_FREE_MB} MB required" >&2
  exit 1
fi

step "1. mkcert certificate and passwords (${LOCAL}/ folder, ignored by Git)"
mkdir -p "${LOCAL}/certs" "${LOCAL}/secrets"
chmod 700 "${LOCAL}/secrets"
if [[ -f "${LOCAL}/certs/tls.crt" && -f "${LOCAL}/certs/tls.key" ]]; then
  echo "Existing certificate kept (not regenerated)."
else
  mkcert -cert-file "${LOCAL}/certs/tls.crt" -key-file "${LOCAL}/certs/tls.key" "*.127.0.0.1.sslip.io"
  chmod 600 "${LOCAL}/certs/tls.key"
fi
(
  umask 077
  python3 - <<'PY'
import secrets

users = ["ADMIN", "ALICE", "BOB", "CHLOE"]
with open(".local/secrets/passwords.env", "w") as f:
    for user in users:
        f.write(f"{user}_PASSWORD={secrets.token_urlsafe(18)}\n")
with open(".local/secrets/db.env", "w") as f:
    f.write(f"POSTGRES_PASSWORD={secrets.token_urlsafe(24)}\n")
    f.write(f"KEYCLOAK_DB_PASSWORD={secrets.token_urlsafe(24)}\n")
with open(".local/secrets/admin.env", "w") as f:
    f.write("username=kcadmin\n")
    f.write(f"password={secrets.token_urlsafe(24)}\n")
PY
)
echo "Passwords generated in ${LOCAL}/secrets/ (4 realm users, PostgreSQL, initial Keycloak administrator; not displayed)."

step "2. k3d cluster (1 server, 2 agents, ports 80 and 443 published; k3s Traefik kept)"
k3d cluster delete "$CLUSTER" >/dev/null 2>&1 || true
k3d cluster create "$CLUSTER" --servers 1 --agents 2 --image "$K3S_IMAGE" \
  -p "80:80@loadbalancer" -p "443:443@loadbalancer" --wait --timeout 600s
$K get nodes -o wide
disk "after creating the cluster"

step "3. Test API image"
docker build -q -t "$APP_IMAGE" app
# Test client on the host: only the dependencies (uv.lock versions); the exp package is read
# through PYTHONPATH (the .pth of an editable install is ignored when macOS flags it "hidden").
uv sync --project app --frozen --no-dev --no-install-project
k3d image import "$APP_IMAGE" -c "$CLUSTER"
disk "after importing the API image"

step "4. Traefik: default mkcert certificate and HTTP -> HTTPS redirect"
retry 90 2 $K get crd tlsstores.traefik.io >/dev/null 2>&1
$K -n kube-system create secret tls mkcert-wildcard --cert "${LOCAL}/certs/tls.crt" --key "${LOCAL}/certs/tls.key"
$K apply -f manifests/traefik-config.yaml
# The redirect only appears in the Traefik arguments once k3s has reinstalled the chart.
retry 120 2 bash -c "$K -n kube-system get deploy traefik -o jsonpath='{.spec.template.spec.containers[0].args}' | grep -q 'redirections'"
$K -n kube-system rollout status deployment/traefik --timeout=300s
echo "--- Traefik arguments related to the redirect ---"
$K -n kube-system get deploy traefik -o jsonpath='{.spec.template.spec.containers[0].args}' | tr ',' '\n' | grep -E 'redirections|"--entryPoints.web.address|--entryPoints.websecure.address' | tr -d '[]"'
echo "--- Traefik image ---"
$K -n kube-system get deploy traefik -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
disk "after Traefik"

step "5. PostgreSQL: official image ${POSTGRES_IMAGE}, one-replica StatefulSet, local-path volume"
$K create namespace keycloak
$K -n keycloak create secret generic postgres-credentials --from-env-file="${LOCAL}/secrets/db.env"
$K -n keycloak create secret generic keycloak-admin --from-env-file="${LOCAL}/secrets/admin.env"
$K apply -f manifests/postgres.yaml
$K -n keycloak rollout status statefulset/postgres --timeout=300s || { echo "FAILURE: PostgreSQL not ready after 300 s" >&2; exit 1; }
$K -n keycloak get statefulset,pvc
echo "--- Roles and databases (superuser) ---"
$K -n keycloak exec postgres-0 -- psql -U postgres -d postgres -At -F ' | ' \
  -c "select rolname, rolsuper, rolcreatedb, rolcreaterole from pg_roles where rolname in ('postgres','keycloak') order by 1" \
  -c "select datname, pg_get_userbyid(datdba) as owner from pg_database where datname='keycloak'"
echo "--- PostgreSQL: version ---"
$K -n keycloak exec postgres-0 -- psql -U postgres -d postgres -At -c "select version()"
disk "after PostgreSQL"

step "6. Keycloak: official image ${KEYCLOAK_IMAGE}, start --import-realm"
# The versioned realm (without secrets) is rendered here: the ${..._PASSWORD} markers are replaced by
# the generated passwords, then the result is mounted from a Secret in /opt/keycloak/data/import.
python3 - <<'PYEOF'
import os

text = open("realm/collector-realm.json").read()
for user in ("ADMIN", "ALICE", "BOB", "CHLOE"):
    env = dict(line.split("=", 1) for line in open(".local/secrets/passwords.env").read().split())
    text = text.replace("${" + user + "_PASSWORD}", env[user + "_PASSWORD"])
assert "_PASSWORD}" not in text
with open(os.environ["WORK"] + "/collector-realm.json", "w") as f:
    f.write(text)
PYEOF
$K -n keycloak create secret generic keycloak-realm --from-file=collector-realm.json="${WORK}/collector-realm.json"
rm -f "${WORK}/collector-realm.json"
$K apply -f manifests/keycloak.yaml
$K -n keycloak rollout status deployment/keycloak --timeout=600s || { echo "FAILURE: Keycloak not ready after 600 s" >&2; exit 1; }
echo "--- Keycloak image ---"
$K -n keycloak get pods -l app=keycloak -o jsonpath='{range .items[*].spec.containers[*]}{.image}{"\n"}{end}'
echo "--- Keycloak log: realm import ---"
$K -n keycloak logs deploy/keycloak | grep -iE 'import|started in|Listening' | sed -E 's/^[^ ]+ [^ ]+ //' | head -n 8 || true
disk "after Keycloak"
retry 60 3 bash -c "curl -s -o /dev/null -w '%{http_code}' --cacert '${CA_FILE}' https://${KC_HOST}/realms/collector/.well-known/openid-configuration | grep -q 200"
echo "Keycloak answers over HTTPS on https://${KC_HOST} (realm collector imported)."

step "7. Test API: Deployment, Service, StripPrefix Middleware and Ingress"
$K apply -f manifests/app.yaml
$K -n exp create secret generic exp-users --from-env-file="${LOCAL}/secrets/passwords.env"
$K -n exp rollout status deployment/exp-api --timeout=180s
retry 60 2 bash -c "curl -s -o /dev/null -w '%{http_code}' --cacert '${CA_FILE}' https://${API_HOST}/exp/api/v1/public | grep -q 200"
disk "after the full installation"
sleep 60   # lets Keycloak finish its initialization before the "idle" reading
top_all "idle, 60 s after the API start"

# --- Measurement 1: TLS --------------------------------------------------------------------------
step "Measurement 1: TLS (presented certificate, negotiated version, failure without the mkcert CA)"
for host in "$KC_HOST" "$API_HOST"; do
  echo "--- ${host}:443 ---"
  OUT=$(openssl s_client -connect "${host}:443" -servername "$host" -CAfile "$CA_FILE" -verify_return_error </dev/null 2>&1 || true)
  echo "$OUT" | grep -E 'Protocol *:|Cipher is|Verification|Verify return code' | head -n 4 || true
  # The raw mkcert subject and issuer contain the user's name and the machine's name:
  # only the organization (first O= field) is displayed, never the CN or the OU.
  CERT=$(echo "$OUT" | openssl x509 -noout -subject -issuer -enddate -ext subjectAltName 2>/dev/null)
  echo "  subject, organization: $(echo "$CERT" | grep '^subject' | grep -o 'O=[^,]*' | head -n 1)"
  echo "  issuer, organization: $(echo "$CERT" | grep '^issuer' | grep -o 'O=[^,]*' | head -n 1)"
  echo "$CERT" | grep -E '^notAfter|DNS:' | sed 's/^ */  /'
  echo "  curl with the mkcert CA: HTTP code $(curl -s -o /dev/null -w '%{http_code}' --cacert "$CA_FILE" "https://${host}/")"
  # macOS curl (SecureTransport) also consults the system keychain, where mkcert -install put the CA:
  # even with --cacert of another bundle, it accepts the certificate. The failure without the CA is
  # therefore demonstrated with httpx (certifi bundle, without the mkcert CA) and with openssl.
  echo "  httpx without the mkcert CA (certifi bundle): $(HOST="$host" app/.venv/bin/python -c '
import os
import httpx
try:
    httpx.get("https://" + os.environ["HOST"] + "/")
    print("connection accepted")
except httpx.ConnectError as error:
    print("expected failure:", error)
')"
  OUT=$(openssl s_client -connect "${host}:443" -servername "$host" -verify_return_error </dev/null 2>&1 || true)
  echo "  openssl without the mkcert CA: $(echo "$OUT" | grep -E 'Verify return code|verify error' | head -n 2 | tr '\n' ' ' || true)"
done

# --- Measurement 2: redirect ------------------------------------------------------------------
step "Measurement 2: HTTP -> HTTPS redirect"
for url in "http://${KC_HOST}/realms/collector" "http://${API_HOST}/exp/api/v1/public"; do
  echo "GET ${url} -> $(curl -s -o /dev/null -w 'code %{http_code}, Location %{redirect_url}' "$url")"
done

# --- Measurement 3: authorization matrix -------------------------------------------------------
step "Measurement 3: authorization matrix (httpx, through https://${API_HOST}/exp, mkcert CA)"
set -a
# shellcheck disable=SC1091
source "${LOCAL}/secrets/passwords.env"
set +a
MATRIX_RC=0
CA_FILE="$CA_FILE" PYTHONPATH=app/src app/.venv/bin/python -m exp.client matrix || MATRIX_RC=$?
echo "--- API log: rejections (reason is never returned to the client) ---"
LOGS=$($K -n exp logs deploy/exp-api | grep '"auth_rejected"' || true) python3 - <<'PYEOF'
import json
import os

for line in os.environ["LOGS"].splitlines():
    d = json.loads(line)
    print(f"{d.get('correlation_id', '-'):<16} status {d['status']}  reason={d['reason']}  {d['path']}")
PYEOF
echo "Exit code of the matrix: ${MATRIX_RC}"

# --- Measurement 4: iss --------------------------------------------------------------------------
step "Measurement 4: iss of a token obtained through the internal URL (Job in the cluster)"
$K -n exp delete job iss-internal --ignore-not-found >/dev/null
sed -e "s|__NAME__|iss-internal|" \
  -e 's|__COMMAND__|["python","-m","exp.client","iss-internal"]|' manifests/job.yaml.tmpl | $K apply -f - >/dev/null
$K -n exp wait --for=condition=complete job/iss-internal --timeout=120s >/dev/null || true
$K -n exp logs job/iss-internal
$K -n exp wait --for=condition=complete job/iss-internal --timeout=5s >/dev/null

# --- Measurement 5: JWKS -------------------------------------------------------------------------
step "Measurement 5: retrieval and caching of the JWKS keys (${BURST} extra requests, one token)"
BEFORE=$($K -n exp logs deploy/exp-api | grep -c '"event": "jwks_fetch"' || true)
CA_FILE="$CA_FILE" PYTHONPATH=app/src app/.venv/bin/python -m exp.client burst "$BURST"
AFTER=$($K -n exp logs deploy/exp-api | grep -c '"event": "jwks_fetch"' || true)
REQUESTS=$($K -n exp logs deploy/exp-api | grep -c '"event": "request"' || true)
echo "JWKS calls before the batch: ${BEFORE}; after: ${AFTER}"
echo "HTTP requests logged by the API since its start: ${REQUESTS}"
echo "--- jwks_fetch lines of the API log ---"
$K -n exp logs deploy/exp-api | grep '"event": "jwks_fetch"'

# --- Measurement 6: resources -------------------------------------------------------------------
step "Measurement 6: resources"
sleep 20
top_all "after the measurements"
echo "--- kubectl top nodes ---"
$K top nodes || true
disk "end of the measurements"
echo "--- Secrets: no password in the repository ---"
git check-ignore -v "${LOCAL}/certs/tls.key" "${LOCAL}/secrets/passwords.env" || true
[[ "$MATRIX_RC" -eq 0 ]] || { echo "The authorization matrix has discrepancies" >&2; exit 1; }
