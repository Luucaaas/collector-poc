#!/usr/bin/env bash
# Protocol 5: load scaling (HPA from 2 to 5 replicas) and availability (pod deleted under load).
#
#   docs/04-experimentations/05-charge-disponibilite/run.sh
#
# Optional variables (default values in parentheses):
#   NOMINAL_USERS (50) NOMINAL_SECONDS (240)   reference load, ramp-up included
#   PEAK_USERS (200)  PEAK_RATE (5)            peak: users, ramp-up per second
#   PEAK_MAX_WAIT (420)                        maximum wait for the 5 ready replicas, in seconds
#   HOLD_AT_FIVE (60) HOLD_AFTER (60)          hold before the deletion, then after the recovery
#   SCALE_DOWN_MAX (900)                       maximum wait for the return to 2 replicas
#   DELETE_POD (1)                             0: no deletion (calibration run)
#   CAPTURES (1)                               0: no Grafana captures (captures.sh)
#   RESULTS_ROOT                               results folder (default: ./resultats)
#
# DIFFERENCE WITH PROTOCOLS 1 TO 4: this script neither creates nor deletes the cluster. It runs
# on the cluster already deployed by `deploy/local/deploy.sh all <tag>` (the HPA load scaling
# is measured on the real deployment, not on a throwaway cluster). It refuses to start if
# `smoke.sh` fails or if a component is not at 2 replicas.
#
# On the cluster, it only does HTTP traffic, reads (kubectl get, top, port-forward) and ONE
# change: `kubectl delete pod` on a catalog-service pod, during the peak.
# Passwords are read from deploy/local/.env, given only to the processes that need them
# (Locust, Playwright) as a command prefix: never displayed, never as an argument, never written.
#
# Flow:
#   1 checks (smoke.sh, 2 replicas) and environment snapshot;
#   2 continuous sampling every 5 s (HPA, ready replicas, pods, CPU) in the background;
#   3 Locust: nominal load, then peak (tests/load, "peak" profile);
#   4 wait for the 5 ready replicas (or the maximum delay), hold, delete a pod,
#     measure the replacement, hold;
#   5 stop the load, observe the scale-down to 2 replicas;
#   6 summary (tests/load/phases.py), Grafana captures (Playwright), final smoke.sh, anonymization.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${HERE}/../../.." && pwd)"
LOAD="${ROOT}/tests/load"
ENV_FILE="${ROOT}/deploy/local/.env"
CTX="k3d-collector"
K="kubectl --context ${CTX} -n collector"
API="https://api.127.0.0.1.sslip.io"
AUTH="https://auth.127.0.0.1.sslip.io"
NOMINAL_USERS="${NOMINAL_USERS:-50}"
NOMINAL_SECONDS="${NOMINAL_SECONDS:-240}"
PEAK_USERS="${PEAK_USERS:-200}"
PEAK_RATE="${PEAK_RATE:-5}"
PEAK_MAX_WAIT="${PEAK_MAX_WAIT:-420}"
HOLD_AT_FIVE="${HOLD_AT_FIVE:-60}"
HOLD_AFTER="${HOLD_AFTER:-60}"
SCALE_DOWN_MAX="${SCALE_DOWN_MAX:-900}"
DELETE_POD="${DELETE_POD:-1}"
CAPTURES="${CAPTURES:-1}"
PROM_PORT=19092
CATALOG_LABEL="app.kubernetes.io/name=catalog-service"

step() { printf '\n=== %s ===\n' "$*"; }
now() { python3 -c 'import time; print(f"{time.time():.3f}")'; }
elapsed() { python3 -c "print(f'{$2 - $1:.1f}')"; }
read_var() {
  grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | grep . \
    || { echo "Key $1 missing or empty in deploy/local/.env." >&2; return 1; }
}

command -v uv >/dev/null || { echo "uv is required (brew install uv)." >&2; exit 1; }
command -v mkcert >/dev/null || { echo "mkcert is required." >&2; exit 1; }
[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env not found: is the cluster deployed?" >&2; exit 1; }
# Shell variables only (no export): given as a prefix to the processes concerned only.
admin_pw="$(read_var ADMIN_PASSWORD)"; alice_pw="$(read_var ALICE_PASSWORD)"
bob_pw="$(read_var BOB_PASSWORD)"; chloe_pw="$(read_var CHLOE_PASSWORD)"
export REQUESTS_CA_BUNDLE="$(mkcert -CAROOT)/rootCA.pem"   # cluster authority, TLS always verified
[[ -f "$REQUESTS_CA_BUNDLE" ]] || { echo "mkcert authority not found (was mkcert -install done?)." >&2; exit 1; }

step "1. Preliminary checks"
RESULTS_ROOT="${RESULTS_ROOT:-${HERE}/resultats}"
export LOAD_RUN_ID="$(date +%Y%m%d-%H%M)"
RESULTS="${RESULTS_ROOT}/${LOAD_RUN_ID}"
[[ ! -e "$RESULTS" ]] || { echo "${RESULTS} already exists (wait a minute)." >&2; exit 1; }
mkdir -p "$RESULTS"
export LOAD_RESULTS_DIR="$RESULTS"
if ! "${ROOT}/deploy/local/smoke.sh" > "${RESULTS}/smoke-avant.txt" 2>&1; then
  echo "smoke.sh fails before the test: stopping (see ${RESULTS}/smoke-avant.txt)." >&2; exit 1
fi
echo "smoke.sh: OK"
for name in catalog-service notification-service frontend; do
  replicas="$($K get deploy "$name" -o jsonpath='{.status.readyReplicas}')"
  [[ "$replicas" == 2 ]] || { echo "${name} is not at 2 ready replicas (${replicas:-0}): stopping." >&2; exit 1; }
done
echo "catalog-service, notification-service, frontend: 2 ready replicas"

sampler=""; portforward=""; locust_pid=""
chrono() { printf '%s\t%s\n' "$(now)" "$1" >> "${RESULTS}/chronologie.tsv"; }
# Anonymizes what is archived: machine name (long and short) and home folder.
sanitize() {
  local short; short="$(hostname -s)"
  local mask='s/\Q$ENV{HOST_SHORT}\E(?:\.[\w-]+)*/<machine>/gi; s{/Us[e]rs/[^\/\s"\x27]+}{<home>}g'
  for file in "${RESULTS}"/*.txt "${RESULTS}"/*.tsv "${RESULTS}"/*.csv "${RESULTS}"/*.json "${RESULTS}"/*.md "${RESULTS}"/*.log "${RESULTS}"/*.html; do
    [[ -f "$file" ]] || continue
    HOST_SHORT="$short" perl -pi -e "$mask" "$file"
  done
  # Compressed files: decompress, mask, recompress.
  for file in "${RESULTS}"/*.gz; do
    [[ -f "$file" ]] || continue
    gunzip -f "$file"
    HOST_SHORT="$short" perl -pi -e "$mask" "${file%.gz}"
    gzip -9 -f "${file%.gz}"
  done
}
cleanup() {
  [[ -z "$sampler" ]] || kill "$sampler" 2>/dev/null || true
  [[ -z "$portforward" ]] || kill "$portforward" 2>/dev/null || true
  if [[ -n "$locust_pid" ]] && kill -0 "$locust_pid" 2>/dev/null; then
    : > "${RESULTS}/arret"; sleep 3; kill "$locust_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT

step "2. Environment"
{
  echo "Start date: $(date '+%d/%m/%Y %H:%M:%S')"
  echo "macOS: $(sw_vers -productVersion), $(uname -m)"
  echo "Docker: $(docker version --format '{{.Server.Version}}'), $(docker info --format '{{.NCPU}} CPU, {{.MemTotal}} bytes of memory')"
  echo "k3d $(k3d version | head -n 1 | awk '{print $3}'), k3s of the nodes $($K get nodes -o jsonpath='{.items[0].status.nodeInfo.kubeletVersion}'), $(kubectl version --client | head -n 1), helm $(helm version --short), mkcert $(mkcert -version)"
  echo "Locust: $(cd "$LOAD" && uv run --quiet locust --version | sed 's/ from .*//')"
  echo "Repository commit: $(git -C "$ROOT" rev-parse --short HEAD)"
  echo
  echo "Deployed images:"
  $K get deploy catalog-service notification-service frontend \
    -o jsonpath='{range .items[*]}  {.metadata.name}{"\t"}{.spec.template.spec.containers[0].image}{"\n"}{end}'
  echo
  echo "Digests read from the pods:"
  $K get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].imageID}{"\n"}{end}' \
    | grep -E '^(catalog-service|notification-service|frontend)-' | sed 's/^/  /'
  echo
  echo "Resources of catalog-service (requests and limits):"
  $K get deploy catalog-service -o jsonpath='  {.spec.template.spec.containers[0].resources}{"\n"}'
  echo
  echo "Nodes:"; kubectl --context "$CTX" top nodes
  echo
  echo "HPA before:"; $K get hpa
  echo
  echo "HPA scale-down policy of catalog-service (empty: Kubernetes defaults):"
  $K get hpa catalog-service -o jsonpath='  {.spec.behavior}{"\n"}'
  echo "Pods before:"; $K get pods -o wide | grep -E '^(NAME|catalog|notification|frontend)'
} > "${RESULTS}/environnement.txt"
{
  echo "Parameters: nominal load ${NOMINAL_USERS} users for ${NOMINAL_SECONDS} s (ramp-up of 1 per second), "
  echo "peak of ${PEAK_USERS} users (ramp-up of ${PEAK_RATE} per second), maximum wait for the 5 replicas ${PEAK_MAX_WAIT} s,"
  echo "hold of ${HOLD_AT_FIVE} s at 5 replicas then ${HOLD_AFTER} s after the recovery, scale-down observation ${SCALE_DOWN_MAX} s at most."
  echo "Run of $(date '+%d/%m/%Y %H:%M'), commit $(git -C "$ROOT" rev-parse --short HEAD), images $($K get deploy catalog-service -o jsonpath='{.spec.template.spec.containers[0].image}' | sed 's/@.*//; s/.*://')."
} > "${RESULTS}/parametres.txt"

# Continuous sampling every 5 s (read-only): HPA, ready replicas, pods, CPU.
sample_loop() {
  while true; do
    ts="$(date +%s)"
    $K get hpa -o jsonpath='{range .items[*]}'"${ts}"'{"\t"}{.metadata.name}{"\t"}{.status.desiredReplicas}{"\t"}{.status.currentReplicas}{"\t"}{.status.currentMetrics[0].resource.current.averageUtilization}{"\n"}{end}' >> "${RESULTS}/hpa.tsv" 2>/dev/null || true
    $K get deploy -o jsonpath='{range .items[*]}'"${ts}"'{"\t"}{.metadata.name}{"\t"}{.status.readyReplicas}{"\n"}{end}' >> "${RESULTS}/ready.tsv" 2>/dev/null || true
    $K get pods -l 'app.kubernetes.io/name in (catalog-service,notification-service)' -o jsonpath='{range .items[*]}'"${ts}"'{"\t"}{.metadata.name}{"\t"}{.status.phase}{"\t"}{.status.containerStatuses[0].ready}{"\t"}{.metadata.deletionTimestamp}{"\n"}{end}' >> "${RESULTS}/pods.tsv" 2>/dev/null || true
    $K top pods --no-headers 2>/dev/null | awk -v ts="$ts" '/^(catalog|notification)-service/ {print ts "\t" $1 "\t" $2 "\t" $3}' >> "${RESULTS}/cpu-pods.tsv" || true
    sleep 5
  done
}
: > "${RESULTS}/hpa.tsv"; : > "${RESULTS}/ready.tsv"; : > "${RESULTS}/pods.tsv"; : > "${RESULTS}/cpu-pods.tsv"
sample_loop & sampler=$!
disown "$sampler"

ready_count() { $K get deploy catalog-service -o jsonpath='{.status.readyReplicas}' 2>/dev/null || true; }
# True if the 3 components are back at 2 replicas (desired, existing and ready).
at_rest() {
  local name state
  for name in catalog-service notification-service frontend; do
    state="$($K get deploy "$name" -o jsonpath='{.status.replicas} {.status.readyReplicas}' 2>/dev/null || true)"
    [[ "$state" == "2 2" ]] || return 1
    [[ "$($K get hpa "$name" -o jsonpath='{.status.desiredReplicas}' 2>/dev/null || true)" == 2 ]] || return 1
  done
}
catalog_at_rest() {
  [[ "$($K get deploy catalog-service -o jsonpath='{.status.replicas} {.status.readyReplicas}' 2>/dev/null || true)" == "2 2" ]] \
    && [[ "$($K get hpa catalog-service -o jsonpath='{.status.desiredReplicas}' 2>/dev/null || true)" == 2 ]]
}

step "3. Locust: nominal load (${NOMINAL_USERS} users, ${NOMINAL_SECONDS} s), then peak (${PEAK_USERS})"
cd "$LOAD"
LOAD_PROFILE=peak LOAD_NOMINAL_USERS="$NOMINAL_USERS" LOAD_NOMINAL_RATE=1 \
LOAD_NOMINAL_SECONDS="$NOMINAL_SECONDS" LOAD_PEAK_USERS="$PEAK_USERS" LOAD_PEAK_RATE="$PEAK_RATE" \
LOAD_MAX_SECONDS=3600 LOAD_REQUEST_LOG="${RESULTS}/requetes.csv" LOAD_STOP_FILE="${RESULTS}/arret" \
LOAD_ADMIN_PASSWORD="$admin_pw" LOAD_ALICE_PASSWORD="$alice_pw" \
LOAD_BOB_PASSWORD="$bob_pw" LOAD_CHLOE_PASSWORD="$chloe_pw" \
uv run --quiet locust -f locustfile.py --headless --host "$API" \
  --csv "${RESULTS}/locust" --html "${RESULTS}/rapport.html" \
  --exit-code-on-error 0 --only-summary > "${RESULTS}/locust.log" 2>&1 &
locust_pid=$!
cd "$HERE"

# Waits for the start of the peak (dated by the load profile in fenetre.json).
peak_start=""
for _ in $(seq 1 $((NOMINAL_SECONDS + 120))); do
  kill -0 "$locust_pid" 2>/dev/null || { echo "Locust stopped before the peak (see locust.log)." >&2; exit 1; }
  peak_start="$(python3 - "${RESULTS}/fenetre.json" <<'PY' 2>/dev/null || true
import json, sys
print(json.load(open(sys.argv[1])).get("peak_start", ""))
PY
)"
  [[ -z "$peak_start" ]] || break
  sleep 1
done
[[ -n "$peak_start" ]] || { echo "The peak did not start." >&2; exit 1; }
echo "Peak started; HPA: $($K get hpa catalog-service --no-headers)"

step "4. Waiting for the 5 ready replicas (at most ${PEAK_MAX_WAIT} s)"
five=0
for _ in $(seq 1 $((PEAK_MAX_WAIT * 2))); do
  kill -0 "$locust_pid" 2>/dev/null || { echo "Locust stopped during the peak." >&2; exit 1; }
  if [[ "$(ready_count)" == 5 ]]; then five=1; chrono five_ready; break; fi
  sleep 0.5
done
if [[ $five -eq 1 ]]; then
  echo "5 replicas ready, hold of ${HOLD_AT_FIVE} s"
  sleep "$HOLD_AT_FIVE"
else
  chrono five_timeout
  echo "5 replicas not reached within ${PEAK_MAX_WAIT} s (ready: $(ready_count)); the deletion takes place anyway." >&2
fi
$K get hpa catalog-service --no-headers

if [[ "$DELETE_POD" == 1 ]]; then
  step "4b. Deleting a catalog-service pod during the peak"
  before_ready="$(ready_count)"
  before_names="$($K get pods -l "$CATALOG_LABEL" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}')"
  victim="$($K get pods -l "$CATALOG_LABEL" -o jsonpath='{range .items[?(@.status.containerStatuses[0].ready==true)]}{.metadata.name}{"\n"}{end}' | head -n 1)"
  echo "Pod deleted: ${victim}; ready before: ${before_ready}"
  chrono delete
  t0="$(now)"
  $K delete pod "$victim" --wait=false >/dev/null
  gone=""; new_ready=""; recovered=""
  for _ in $(seq 1 360); do
    listing="$($K get pods -l "$CATALOG_LABEL" -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.containerStatuses[0].ready}{" "}{.metadata.deletionTimestamp}{"\n"}{end}')"
    if [[ -z "$gone" ]] && ! echo "$listing" | awk '{print $1}' | grep -qx "$victim"; then
      gone=1; chrono old_gone
    fi
    if [[ -z "$new_ready" ]]; then
      # A pod absent from the earlier list, ready and not terminating: the replacement.
      while read -r name ready terminating; do
        [[ -n "$name" && "$ready" == true && -z "$terminating" ]] || continue
        echo "$before_names" | grep -qx "$name" || { new_ready=1; chrono new_ready; break; }
      done <<< "$listing"
    fi
    if [[ -n "$gone" && "$(ready_count)" -ge "$before_ready" ]]; then recovered=1; chrono recovered; break; fi
    sleep 0.5
  done
  [[ -n "$recovered" ]] || echo "Ready replicas not recovered within 180 s after the deletion." >&2
  echo "Replacement measured (see chronologie.tsv); hold of ${HOLD_AFTER} s"
  sleep "$HOLD_AFTER"
fi

step "5. Stopping the load, observing the scale-down (at most ${SCALE_DOWN_MAX} s)"
: > "${RESULTS}/arret"
chrono stop
wait "$locust_pid" 2>/dev/null || true
locust_pid=""
chrono locust_ended
echo "Load stopped; HPA: $($K get hpa catalog-service --no-headers)"
back2=0
for _ in $(seq 1 $((SCALE_DOWN_MAX / 5))); do
  if [[ $back2 -eq 0 ]] && catalog_at_rest; then back2=1; chrono catalog_back_2; fi
  if at_rest; then chrono all_back_2; break; fi
  sleep 5
done
at_rest || echo "The 3 components did not return to 2 replicas within ${SCALE_DOWN_MAX} s." >&2
sleep 20   # a few more points on the charts
chrono observation_end
kill "$sampler" 2>/dev/null || true; sampler=""

step "6. Events, summary, captures"
# Events of the test, with their absolute time (those of a previous run are discarded).
$K get events -o json | python3 -c '
import calendar, json, sys, time
start = float(sys.argv[1])
rows = []
for e in json.load(sys.stdin)["items"]:
    obj = e["involvedObject"]
    if not (obj["kind"] == "HorizontalPodAutoscaler" or obj["name"].startswith(("catalog-service", "notification-service"))):
        continue
    stamp = e.get("lastTimestamp") or e.get("eventTime") or e["metadata"]["creationTimestamp"]
    epoch = calendar.timegm(time.strptime(stamp[:19], "%Y-%m-%dT%H:%M:%S"))
    if epoch >= start:
        rows.append((epoch, e["type"], e["reason"], obj["kind"] + "/" + obj["name"], e["message"]))
for epoch, kind, reason, name, message in sorted(rows):
    print(time.strftime("%H:%M:%S", time.localtime(epoch)), kind, reason, name, message)
' "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["nominal_start"] - 60)' "${RESULTS}/fenetre.json")" > "${RESULTS}/evenements.txt"
$K port-forward svc/kps-prometheus "${PROM_PORT}:9090" >/dev/null 2>&1 &
portforward=$!
disown "$portforward"
for _ in $(seq 1 30); do curl -s -o /dev/null --max-time 2 "http://127.0.0.1:${PROM_PORT}/-/ready" && break; sleep 1; done
sleep 35   # two scrape cycles (15 s) after the end
sanitize
(cd "$LOAD" && uv run --quiet python phases.py "$RESULTS" "http://127.0.0.1:${PROM_PORT}")
sanitize

if [[ "$CAPTURES" == 1 ]]; then
  step "6b. Captures of the Grafana dashboard"
  "${HERE}/captures.sh" "$RESULTS" || echo "Grafana captures failed (see above)." >&2
fi

step "7. End: cluster state and smoke.sh"
$K get hpa; $K get pods -o wide | grep -E '^(NAME|catalog|notification|frontend)'
"${ROOT}/deploy/local/smoke.sh" > "${RESULTS}/smoke-apres.txt" 2>&1 \
  && echo "smoke.sh: OK" || echo "smoke.sh: FAILURE (see smoke-apres.txt)" >&2
$K get hpa > "${RESULTS}/hpa-apres.txt"
gzip -9 -f "${RESULTS}/requetes.csv"
rm -f "${RESULTS}/arret"
sanitize
echo "Results: ${RESULTS}"
