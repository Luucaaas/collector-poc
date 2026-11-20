#!/usr/bin/env bash
# Reproducible security audit of the POC on the k3d cluster (phase 9, criterion 8).
#
#   docs/06-securite/scans/run-scans.sh            everything (about 40 minutes)
#   docs/06-securite/scans/run-scans.sh trivy sonar npm    only these stages
#                                                   (stages: trivy sonar npm zap)
#
# What the script does, in order:
#   1. checks the cluster (smoke.sh) and the tools, reads alice and the passwords from
#      deploy/local/.env: never displayed, never as a command argument;
#   2. records the versions and digests (environnement.txt);
#   3. Trivy 0.76.0: official release binary, SHA-256 sum verified, in a temporary folder
#      outside the repository; deployed images in amd64 AND arm64, all severities, WITHOUT
#      --ignore-unfixed (the CI does use it); repository configuration and rendered Helm chart;
#   4. SonarCloud (public read API) and full npm audit of the front end;
#   5. OWASP ZAP (official image pinned by digest): passive scan of the front end and of the
#      Keycloak login page; ACTIVE scan of the API (catalog then notification), without token, then
#      authenticated (alice);
#   6. masks tokens, the machine name and the home folder in everything archived,
#      then checks the counters (tokens, passwords, machine name, home folder: 0);
#   7. produces resume.md (numeric summary) and replays smoke.sh.
#
# Scope, strictly: the active scan targets ONLY api.127.0.0.1.sslip.io (the local POC). The front end
# (app.) and Keycloak (auth.) are analyzed passively: Keycloak is a third-party product and an active scan
# could lock the demo accounts. No other host, ever. On the cluster, the
# script only does HTTP traffic and reads (kubectl get); the active scan creates demo data
# (categories, shops, articles), which is accepted.
#
# How the ZAP container reaches the cluster: the *.127.0.0.1.sslip.io names point to 127.0.0.1,
# which designates the container itself. `--add-host <name>:host-gateway` makes them resolve to the Docker
# host (the Mac), where k3d publishes Traefik's port 443. The certificate is the mkcert one: a
# copy of the image's Java trust store, plus the mkcert authority (public key
# only), is mounted in the container; TLS verification stays active.
#
# How the token reaches ZAP: pkce_login.py obtains alice's tokens through the real PKCE flow;
# run-scans.sh keeps them in shell variables and gives them to the container with `-e VARIABLE`
# without a value on the command line. zap_hook.py sets the Authorization header in ZAP and
# renews it every 150 s (the access token lasts 5 minutes, an active scan longer).
#
# Compatible with bash 3.2 (macOS). Exit code: 0 even if findings exist (the audit reports,
# it does not block); other code: the audit could not run or a secret leak was seen.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${HERE}/../../.." && pwd)"
ENV_FILE="${ROOT}/deploy/local/.env"
CTX="k3d-collector"
K="kubectl --context ${CTX} -n collector"
API_HOST="api.127.0.0.1.sslip.io"
APP_HOST="app.127.0.0.1.sslip.io"
AUTH_HOST="auth.127.0.0.1.sslip.io"

# Official ZAP image, stable version published more than 14 days ago, pinned by digest
# (multi-architecture index; tag zaproxy/zap-stable:20261026, ZAP 2.17.0).
ZAP_IMAGE="zaproxy/zap-stable@sha256:030d3df57735dacbb83464854758e674dd9ad01d79d12a129a8e58b1fd384238"
# Trivy: same version and sum as .github/workflows/backend.yml (Linux archive). For the Mac,
# the macOS archive is verified with the release sums file, which is first checked to
# contain the sum of the Linux archive pinned in the CI (proof that it is authentic).
TRIVY_VERSION="$(grep -E '^  TRIVY_VERSION:' "${ROOT}/.github/workflows/backend.yml" | sed -E 's/.*"([^"]+)".*/\1/')"
TRIVY_LINUX_SHA256="$(grep -E '^  TRIVY_SHA256:' "${ROOT}/.github/workflows/backend.yml" | awk '{print $2}')"
ZAP_MAX_SCAN_MINUTES="${ZAP_MAX_SCAN_MINUTES:-12}"   # maximum duration of the active scan of one pass

STAGES=("$@")
[[ ${#STAGES[@]} -gt 0 ]] || STAGES=(trivy sonar npm zap)
want() { local s; for s in "${STAGES[@]}"; do [[ "$s" == "$1" ]] && return 0; done; return 1; }

[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env not found: has the cluster been deployed?" >&2; exit 1; }
for tool in docker kubectl helm curl uv mkcert npm perl python3 shasum tar; do
  command -v "$tool" >/dev/null || { echo "${tool} is required." >&2; exit 1; }
done

# Value of a .env key, never displayed.
read_var() {
  grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | grep . \
    || { echo "Key $1 missing or empty in deploy/local/.env." >&2; return 1; }
}

echo "== Preliminary check: the cluster is healthy (smoke.sh)"
"${ROOT}/deploy/local/smoke.sh" >/dev/null 2>&1 \
  || { echo "smoke.sh fails: cluster not healthy, audit interrupted." >&2; exit 1; }

RUN_ID="$(date +%Y%m%d-%H%M)"
RESULTS="${HERE}/resultats/${RUN_ID}"
[[ ! -e "$RESULTS" ]] || { echo "${RESULTS} already exists (wait a minute)." >&2; exit 1; }
mkdir -p "$RESULTS"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/collector-audit.XXXXXX")"
chmod 700 "$WORK"
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT
CAROOT_PEM="$(mkcert -CAROOT)/rootCA.pem"
[[ -f "$CAROOT_PEM" ]] || { echo "mkcert authority not found (was mkcert -install done?)." >&2; exit 1; }
export REQUESTS_CA_BUNDLE="$CAROOT_PEM"

# Deployed image (tag@digest), read from the cluster: we audit what runs, not what we believe.
deployed_image() { $K get deploy "$1" -o jsonpath='{.spec.template.spec.containers[0].image}'; }
IMG_CATALOG="$(deployed_image catalog-service)"
IMG_NOTIFICATION="$(deployed_image notification-service)"
IMG_FRONTEND="$(deployed_image frontend)"

pods_state() { $K get pods --no-headers -o custom-columns=NAME:.metadata.name,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount | sort; }
pods_state > "${RESULTS}/pods-avant.txt"
$K get hpa --no-headers > "${RESULTS}/hpa-avant.txt"

echo "== Environment and versions"
{
  echo "Start date: $(date '+%d/%m/%Y %H:%M:%S')"
  echo "Repository commit: $(git -C "$ROOT" rev-parse --short HEAD)"
  echo "Docker: $(docker version --format '{{.Server.Version}}')"
  echo "ZAP image: ${ZAP_IMAGE}"
  echo "Active target: https://${API_HOST}; passive: https://${APP_HOST} and https://${AUTH_HOST}"
  echo
  echo "Deployed images (read from the cluster):"
  echo "  ${IMG_CATALOG}"
  echo "  ${IMG_NOTIFICATION}"
  echo "  ${IMG_FRONTEND}"
  echo
  echo "Digests read from the pods:"
  $K get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].imageID}{"\n"}{end}' \
    | grep -E '^(catalog-service|notification-service|frontend)-' | sed 's/^/  /'
  echo
  echo "Node: $(node --version 2>/dev/null || echo absent); npm: $(npm --version)"
} > "${RESULTS}/environnement.txt"

# ---------------------------------------------------------------------------------------------
# Trivy
# ---------------------------------------------------------------------------------------------
trivy_install() {
  local arch base archive
  arch="$(uname -m)"
  case "$arch" in arm64) archive="trivy_${TRIVY_VERSION}_macOS-ARM64.tar.gz" ;; \
                  x86_64) archive="trivy_${TRIVY_VERSION}_macOS-64bit.tar.gz" ;; \
                  *) echo "Architecture ${arch} not supported." >&2; return 1 ;; esac
  base="https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}"
  mkdir -p "${WORK}/trivy-dl" "${WORK}/trivy-bin"
  curl -fsSL --retry 3 -o "${WORK}/trivy-dl/sums.txt" "${base}/trivy_${TRIVY_VERSION}_checksums.txt"
  curl -fsSL --retry 3 -o "${WORK}/trivy-dl/${archive}" "${base}/${archive}"
  # 1. the sums file is authentic: it contains the Linux sum pinned in the CI;
  grep -q "^${TRIVY_LINUX_SHA256}  trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz$" "${WORK}/trivy-dl/sums.txt" \
    || { echo "The Trivy sums file does not contain the sum pinned in the CI." >&2; return 1; }
  # 2. the Mac archive matches its sum.
  ( cd "${WORK}/trivy-dl" && grep " ${archive}\$" sums.txt | shasum -a 256 --check --strict - >/dev/null ) \
    || { echo "SHA-256 sum of ${archive} is incorrect." >&2; return 1; }
  tar -xzf "${WORK}/trivy-dl/${archive}" -C "${WORK}/trivy-bin" trivy
  TRIVY="${WORK}/trivy-bin/trivy"
  export TRIVY_CACHE_DIR="${WORK}/trivy-cache"
  echo "Trivy $("$TRIVY" --version | head -1 | sed 's/Version: //') (archive ${archive}, SHA-256 verified)" \
    | tee -a "${RESULTS}/environnement.txt"
}

trivy_images() {
  local name ref arch out
  for name in catalog-service notification-service frontend; do
    case "$name" in
      catalog-service) ref="$IMG_CATALOG" ;;
      notification-service) ref="$IMG_NOTIFICATION" ;;
      frontend) ref="$IMG_FRONTEND" ;;
    esac
    for arch in amd64 arm64; do
      out="${RESULTS}/trivy-${name}-${arch}"
      echo "-- Trivy ${name} (${arch})"
      # --image-src remote: reads the image from GHCR, pulling nothing into Docker.
      "$TRIVY" image --image-src remote --platform "linux/${arch}" --scanners vuln,secret \
        --severity UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL --quiet \
        --format json --output "${out}.json" "$ref"
      "$TRIVY" convert --format table --output "${out}.txt" "${out}.json"
    done
  done
}

trivy_config() {
  local out
  # Helm chart rendered with the same values as deploy.sh (dummy digest: only the template matters).
  mkdir -p "${WORK}/rendered"
  local svc
  for svc in catalog-service notification-service frontend; do
    helm template "$svc" "${ROOT}/deploy/helm/collector-service" -f "${ROOT}/deploy/helm/values/${svc}.yaml" \
      --set image.tag=audit --set "image.digest=sha256:$(printf '0%.0s' $(seq 1 64))" \
      --set serviceMonitor.enabled=true > "${WORK}/rendered/${svc}.yaml"
  done
  echo "-- Trivy config: manifests of deploy/"
  "$TRIVY" config --quiet --format json --output "${RESULTS}/trivy-config-deploy.json" "${ROOT}/deploy"
  echo "-- Trivy config: Dockerfiles of the services and the front end"
  "$TRIVY" config --quiet --skip-dirs "${ROOT}/frontend/node_modules" --skip-dirs "${ROOT}/frontend/dist" \
    --format json --output "${RESULTS}/trivy-config-dockerfiles.json" "${ROOT}/services" 
  "$TRIVY" config --quiet --skip-dirs "${ROOT}/frontend/node_modules" --skip-dirs "${ROOT}/frontend/dist" \
    --skip-dirs "${ROOT}/frontend/test-results" --skip-dirs "${ROOT}/frontend/e2e" \
    --format json --output "${RESULTS}/trivy-config-frontend.json" "${ROOT}/frontend"
  echo "-- Trivy config: rendered Helm chart"
  "$TRIVY" config --quiet --format json --output "${RESULTS}/trivy-config-helm-rendu.json" "${WORK}/rendered"
  for out in deploy dockerfiles frontend helm-rendu; do
    "$TRIVY" convert --format table --output "${RESULTS}/trivy-config-${out}.txt" "${RESULTS}/trivy-config-${out}.json"
  done
}

# ---------------------------------------------------------------------------------------------
# SonarCloud (public API, without token) and npm audit
# ---------------------------------------------------------------------------------------------
sonar_extract() {
  local svc key
  for svc in catalog-service notification-service; do
    key="Luucaaas_collector-poc_${svc}"
    echo "-- SonarCloud ${svc}"
    curl -fsS "https://sonarcloud.io/api/issues/search?componentKeys=${key}&resolved=false&ps=500" \
      -o "${RESULTS}/sonar-${svc}-issues.json"
    curl -fsS "https://sonarcloud.io/api/hotspots/search?projectKey=${key}&ps=500" \
      -o "${RESULTS}/sonar-${svc}-hotspots.json"
    curl -fsS "https://sonarcloud.io/api/qualitygates/project_status?projectKey=${key}" \
      -o "${RESULTS}/sonar-${svc}-quality-gate.json"
  done
}

npm_audit() {
  echo "-- npm audit (development dependencies included, then shipped ones only)"
  ( cd "${ROOT}/frontend"
    npm audit --json > "${RESULTS}/npm-audit-complet.json" || true
    npm audit --omit=dev --json > "${RESULTS}/npm-audit-prod.json" || true )
}

# ---------------------------------------------------------------------------------------------
# ZAP
# ---------------------------------------------------------------------------------------------
# Container resources capped: a first attempt at the full active scan, without a cap, had
# taken 430 % CPU and 4.8 GiB of the 7.75 GiB of the Docker Desktop virtual machine, which also serves
# the cluster: PostgreSQL, Keycloak and other pods had restarted in a loop for
# three minutes (back to normal without intervention, but the scan had been interrupted).
# 2 CPU, 2 GiB of memory for the container, Java heap limited to 1 GiB (-Xmx1g, read by zap.sh).
ZAP_LIMITS=(--memory 2g --memory-swap 2g --cpus 2)
ZAP_JVM="-Xmx1g"
ZAP_COMMON=(--rm "${ZAP_LIMITS[@]}" --add-host "${API_HOST}:host-gateway" --add-host "${APP_HOST}:host-gateway"
            --add-host "${AUTH_HOST}:host-gateway" -v "${WORK}/ts:/ts:ro" -v "${WORK}/wrk:/zap/wrk:rw"
            -e "JAVA_TOOL_OPTIONS=-Djavax.net.ssl.trustStore=/ts/cacerts -Djavax.net.ssl.trustStorePassword=changeit")

zap_setup() {
  mkdir -p "${WORK}/ts" "${WORK}/wrk"
  chmod 777 "${WORK}/wrk"   # the container's `zap` user (uid 1000) must be able to write there
  docker image inspect "$ZAP_IMAGE" >/dev/null 2>&1 || docker pull --quiet "$ZAP_IMAGE" >/dev/null
  cp "$CAROOT_PEM" "${WORK}/ts/rootCA.pem"
  cp "${HERE}/zap_hook.py" "${WORK}/ts/zap_hook.py"
  # Configuration file of zap-api-scan.py: as soon as it is provided and non-empty, ZAP abandons its
  # "API-Minimal" policy (a few rules) and enables ALL the rules of the default policy
  # (injections, XSS, path traversal, etc.). One line is enough: a passive rule left at WARN.
  # Rule 40026 (DOM-based XSS) is disabled: it launches a Firefox browser in the
  # container, useless on a JSON API, and it exhausted the container memory (ZAP killed during the
  # scan, unrelated: observed during the first two attempts).
  printf '10020\tWARN\t(Anti-clickjacking, passive rule left at WARN)\n40026\tIGNORE\t(DOM XSS, browser)\n' > "${WORK}/ts/api-scan.conf"
  # Trust store: copy of the image's one + mkcert authority (public).
  docker run --rm -v "${WORK}/ts:/ts" --entrypoint sh "$ZAP_IMAGE" -c \
    'cp "$(readlink -f /etc/ssl/certs/java/cacerts)" /ts/cacerts &&
     keytool -importcert -noprompt -alias mkcert -file /ts/rootCA.pem -keystore /ts/cacerts -storepass changeit >/dev/null' \
    || { echo "ZAP trust store not created." >&2; return 1; }
  chmod 644 "${WORK}/ts/"*
  docker run --rm --entrypoint sh "$ZAP_IMAGE" -c 'ls /zap/zap-*.jar | head -1' > "${WORK}/zap-version.txt"
  echo "ZAP: $(cat "${WORK}/zap-version.txt" | sed 's#/zap/##'); image ${ZAP_IMAGE}" >> "${RESULTS}/environnement.txt"
}

ZAP_FAILED=0
zap_collect() { # files the reports of a pass (zap-<name>.html, .json, .md) into the results
  local f
  for f in "${WORK}/wrk/zap-$1".*; do [[ -f "$f" ]] && mv "$f" "${RESULTS}/"; done
  # No JSON report: ZAP was killed or failed; this is not let through silently.
  if [[ ! -s "${RESULTS}/zap-$1.json" ]]; then
    echo "WARNING: the ZAP pass \"$1\" produced no report (see zap-$1.log)." >&2
    ZAP_FAILED=1
  fi
  return 0
}

# Passive scan: one-minute spider, no attack (zap-baseline.py). `spider.postform=false`: the
# spider submits no form (the first two attempts had sent Keycloak's empty login
# form: an authentication attempt is not "passive"). `--autooff` is
# necessary: with the default mode (Automation Framework), ZAP ignores this option; verified on
# a throwaway local server that counts POST requests (2 POSTs without --autooff, 0 with).
zap_passive() {
  local name="$1" url="$2" t0=$SECONDS
  echo "-- ZAP passive: ${name} (${url%%\?*})"
  docker run "${ZAP_COMMON[@]}" --name "collector-audit-zap-${name}" "$ZAP_IMAGE" zap-baseline.py -t "$url" -m 1 -I --autooff \
    -z "${ZAP_JVM} -config spider.postform=false" \
    -r "zap-${name}.html" -J "zap-${name}.json" -w "zap-${name}.md" > "${RESULTS}/zap-${name}.log" 2>&1 || true
  echo "${name}: $((SECONDS - t0)) s" >> "${RESULTS}/zap-durees.txt"
  zap_collect "$name"
}

# OpenAPI specification of a service, completed with the public URL (the `servers` field is absent:
# the routes are /api/v1/... behind Traefik's /catalog or /notification prefix).
zap_spec() {
  local svc="$1" prefix="$2"
  curl -fsS --cacert "$CAROOT_PEM" "https://${API_HOST}/${prefix}/api/v1/openapi.json" \
    | python3 -c "
import json, sys
spec = json.load(sys.stdin)
spec['servers'] = [{'url': 'https://${API_HOST}/${prefix}'}]
json.dump(spec, open('${WORK}/wrk/${svc}-openapi.json', 'w'))"
}

# Active scan of a service's API (zap-api-scan.py, ZAP default policy, all rules).
# $1: pass name; $2: service; $3: "anonymous" or "alice".
zap_api() {
  local name="$1" svc="$2" mode="$3" tokens access refresh t0=$SECONDS
  echo "-- ZAP active: ${name} (${mode}, ${ZAP_MAX_SCAN_MINUTES} min at most)"
  if [[ "$mode" == "alice" ]]; then
    # The tokens stay in shell variables; the password is only given to the command.
    tokens="$(SCAN_USER=alice SCAN_PASSWORD="$ALICE_PW" \
      uv run --quiet --project "${ROOT}/tests/load" python "${HERE}/pkce_login.py")" \
      || { echo "Login of alice impossible." >&2; return 1; }
    access="$(printf '%s\n' "$tokens" | sed -n 1p)"
    refresh="$(printf '%s\n' "$tokens" | sed -n 2p)"
    tokens=""
    ZAP_ACCESS_TOKEN="$access" ZAP_REFRESH_TOKEN="$refresh" \
    docker run "${ZAP_COMMON[@]}" --name "collector-audit-zap-${name}" -e ZAP_ACCESS_TOKEN -e ZAP_REFRESH_TOKEN "$ZAP_IMAGE" zap-api-scan.py \
      -t "/zap/wrk/${svc}-openapi.json" -f openapi --hook /ts/zap_hook.py -c /ts/api-scan.conf -I -T 10 \
      -z "${ZAP_JVM} -config scanner.maxScanDurationInMins=${ZAP_MAX_SCAN_MINUTES}" \
      -r "zap-${name}.html" -J "zap-${name}.json" -w "zap-${name}.md" > "${RESULTS}/zap-${name}.log" 2>&1 || true
    access=""; refresh=""
  else
    docker run "${ZAP_COMMON[@]}" --name "collector-audit-zap-${name}" "$ZAP_IMAGE" zap-api-scan.py \
      -t "/zap/wrk/${svc}-openapi.json" -f openapi --hook /ts/zap_hook.py -c /ts/api-scan.conf -I -T 10 \
      -z "${ZAP_JVM} -config scanner.maxScanDurationInMins=${ZAP_MAX_SCAN_MINUTES}" \
      -r "zap-${name}.html" -J "zap-${name}.json" -w "zap-${name}.md" > "${RESULTS}/zap-${name}.log" 2>&1 || true
  fi
  echo "${name}: $((SECONDS - t0)) s" >> "${RESULTS}/zap-durees.txt"
  zap_collect "$name"
}

# ---------------------------------------------------------------------------------------------
# Archiving: masking and counters
# ---------------------------------------------------------------------------------------------
sanitize() {
  local short file
  short="$(hostname -s)"
  for file in "${RESULTS}"/*; do
    [[ -f "$file" ]] || continue
    # tokens (three base64url segments whose first starts with the JWT header), machine name
    # (long and short, case-insensitive) and home folder.
    HOST_SHORT="$short" perl -pi -e \
      's/ey[J]\w[\w-]*(?:\.[\w-]+){0,2}/<masked-token>/g; s/\Q$ENV{HOST_SHORT}\E(?:\.[\w-]+)*/<machine>/gi; s{/Us[e]rs/[^\/\s"\x27]+}{<home>}g' "$file"
  done
}

# Counts the occurrences of what must never be archived. Prints numbers, never a value.
count_leaks() {
  local dir="$1" jwt home host patterns n_jwt n_home n_host n_pw
  jwt="ey$(printf 'J')"; home="/Us$(printf 'e')rs"; host="$(hostname -s)"
  patterns="${WORK}/patterns"; : > "$patterns"; chmod 600 "$patterns"
  # Passwords and secrets of the .env (values of at least 8 characters), given to grep by file.
  { grep -E '^[A-Z_]*(PASSWORD|SECRET|TOKEN|KEY)[A-Z_]*=' "$ENV_FILE" | cut -d= -f2- | awk 'length($0) >= 8'; } >> "$patterns" || true
  n_pw="$(grep -rIlF -f "$patterns" "$dir" 2>/dev/null | wc -l | tr -d ' ')"
  n_jwt="$(grep -rIF -- "$jwt" "$dir" 2>/dev/null | wc -l | tr -d ' ')"
  n_host="$(grep -rIiF -- "$host" "$dir" 2>/dev/null | wc -l | tr -d ' ')"
  n_home="$(grep -rIF -- "$home" "$dir" 2>/dev/null | wc -l | tr -d ' ')"
  echo "  ${dir#"${ROOT}/"}"
  echo "    tokens (${jwt}): ${n_jwt}; files containing a .env password: ${n_pw}"
  echo "    machine name: ${n_host}; home folder (${home}): ${n_home}"
  [[ "${n_jwt}${n_pw}${n_host}${n_home}" == "0000" ]]
}

# ---------------------------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------------------------
if want trivy; then
  echo "== Trivy"
  trivy_install
  trivy_images
  trivy_config
  # Version of the vulnerability database (known only once the database is downloaded).
  { echo "Trivy vulnerability database:"; "$TRIVY" --version | sed -n '2,$p' | sed 's/^/  /'; } >> "${RESULTS}/environnement.txt"
fi
if want sonar; then echo "== SonarCloud"; sonar_extract; fi
if want npm; then echo "== npm audit"; npm_audit; fi

if want zap; then
  echo "== OWASP ZAP"
  ALICE_PW="$(read_var ALICE_PASSWORD)"
  zap_setup
  zap_passive front "https://${APP_HOST}/"
  # Public Keycloak login page (dummy PKCE: the page is displayed, nothing is submitted).
  zap_passive keycloak "https://${AUTH_HOST}/realms/collector/protocol/openid-connect/auth?client_id=collector-web&response_type=code&scope=openid&redirect_uri=https%3A%2F%2F${APP_HOST}%2F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256"
  zap_spec catalog catalog
  zap_spec notification notification
  zap_api api-catalog-anonyme catalog anonymous
  zap_api api-notification-anonyme notification anonymous
  zap_api api-catalog-alice catalog alice
  zap_api api-notification-alice notification alice
  ALICE_PW=""
fi

echo "== Summary, then masking of what is archived"
python3 "${HERE}/summarize.py" "$RESULTS" > "${RESULTS}/resume.md"
sanitize
echo "== Counters (expected: 0 everywhere)"
leaks_ok=1
count_leaks "$RESULTS" || leaks_ok=0
count_leaks "$HERE" || leaks_ok=0

pods_state > "${RESULTS}/pods-apres.txt"
$K get hpa --no-headers > "${RESULTS}/hpa-apres.txt"
echo "== Cluster intact?"
echo "Container restarts: $(awk '{n += $3} END {print n + 0}' "${RESULTS}/pods-avant.txt") before, $(awk '{n += $3} END {print n + 0}' "${RESULTS}/pods-apres.txt") after (pods-*.txt, hpa-*.txt)"
"${ROOT}/deploy/local/smoke.sh" 2>&1 | tail -2
echo
echo "Results: ${RESULTS}"
[[ $ZAP_FAILED -eq 0 ]] || { echo "WARNING: at least one ZAP pass did not complete." >&2; exit 3; }
[[ $leaks_ok -eq 1 ]] || { echo "WARNING: a secret, the machine name or the home folder appears in the results." >&2; exit 2; }
exit 0
