#!/usr/bin/env bash
# Experiment 3: observability with kube-prometheus-stack on k3d (see protocole.md).
# Creates the cluster, installs the lightweight stack, deploys an instrumented FastAPI application,
# sends a known load (ground truth), compares Prometheus measurements to the injected
# values, checks Grafana, reads the stack memory, then deletes the cluster.
# Usage: ./run.sh [--keep]   (--keep keeps the cluster at the end)
# The full output is also written to resultats/run-YYYYMMDD-HHMM.log.
set -euo pipefail

# --- Pinned versions -------------------------------------------------------------------
K3S_IMAGE="rancher/k3s:v1.35.8-k3s1"
STACK_CHART="oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack"
STACK_VERSION="91.9.0"   # published on 02/10/2026; Prometheus 3.15.0, Grafana 13.2.3, operator 0.94.1
ALPINE_IMAGE="alpine:3.24.3"   # utility image: measures the disk space of the Docker VM
APP_IMAGE="exp-observabilite-app:local"   # FastAPI 0.142.2, instrumentator 8.1.0, structlog 26.1.0,
                                          # httpx 0.28.1, uvicorn 0.52.4 (see app/uv.lock)

# --- Parameters ------------------------------------------------------------------------
CLUSTER="collector-exp3"
NS_APP="exp"
NS_MON="monitoring"
TOTAL=3000     # requests of the load
RATE=20        # requests per second (duration: TOTAL / RATE = 150 s)
KEEP=false
[[ "${1:-}" == "--keep" ]] && KEEP=true

cd "$(dirname "$0")"
MIN_FREE_MB=7000   # the run uses 3.7 GB and the kubelet evicts below about 3.1 GB free (measured here, decision log of 02/11/2026)

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
WORK=$(mktemp -d)
PF_PIDS=()
PROM_URL="http://127.0.0.1:19090"
GRAFANA_URL="http://127.0.0.1:13000"
APP_URL="http://127.0.0.1:18000"

step() { printf '\n=== %s ===\n' "$*"; }
disk() { echo "Free disk space of the Docker VM ($1): $(docker run --rm "$ALPINE_IMAGE" df -h / | awk 'NR==2 {print $4 " of " $2 " (" $5 " used)"}')"; }
now() { python3 -c 'import time; print(f"{time.time():.3f}")'; }

cleanup() {
  local rc=$?   # exit code of the script, captured before any other command
  for pid in "${PF_PIDS[@]:-}"; do [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true; done
  rm -rf "$WORK"
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

# Opens (or reopens if it dropped) a port forward. $1 namespace, $2 service,
# $3 local port, $4 service port, $5 test path.
forward() {
  if curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$3$5"; then return 0; fi
  $K -n "$1" port-forward "svc/$2" "$3:$4" >/dev/null 2>&1 &
  PF_PIDS+=("$!")
  disown "$!"
  for _ in $(seq 1 60); do
    curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$3$5" && return 0
    sleep 0.5
  done
  echo "Port forward to $2 failed" >&2
  return 1
}

# Reads memory and CPU of each pod (k3s metrics-server). $1 label.
top_all() {
  echo "--- Memory and CPU of the pods ($1) ---"
  local out=""
  for _ in $(seq 1 60); do
    out=$($K top pods -n "$NS_MON" --no-headers 2>/dev/null || true)
    [[ -n "$out" ]] && break
    sleep 2
  done
  echo "Namespace ${NS_MON}:"
  echo "$out"
  echo "Namespace ${NS_APP}:"
  $K top pods -n "$NS_APP" --no-headers 2>/dev/null || true
  echo "$out" | python3 -c '
import sys
mem = cpu = 0.0
for line in sys.stdin:
    p = line.split()
    if len(p) < 3:
        continue
    cpu += float(p[1].rstrip("m"))
    value = float(p[2][:-2])
    unit = p[2][-2:]
    mem += value * {"Ki": 1 / 1024, "Mi": 1, "Gi": 1024}[unit]
print(f"TOTAL stack ({sys.argv[1]}): {mem:.0f} Mi, {cpu:.0f} m CPU")' "$1"
}

# --- 0. Prerequisites and environment ---------------------------------------------------------
step "0. Prerequisites and environment"
for tool in docker k3d kubectl helm uv python3 perl curl; do
  command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
done
docker info >/dev/null
date "+Run date:%d/%m/%Y %H:%M"
echo "macOS $(sw_vers -productVersion) $(uname -m) ; host Python $(python3 --version | cut -d' ' -f2) ; $(uv --version | cut -d' ' -f1-2)"
echo "Docker moteur $(docker version --format '{{.Server.Version}}') ; $(docker info --format '{{.NCPU}} CPU, {{.MemTotal}} bytes of memory')"
k3d version | head -1
kubectl version --client | head -1
echo "Helm $(helm version --short)"
echo "Chart ${STACK_CHART} version ${STACK_VERSION}"
FREE_MB=$(docker run --rm "$ALPINE_IMAGE" df -m / | awk 'NR==2 {print $4}')
disk "before"
if [[ "$FREE_MB" -lt "$MIN_FREE_MB" ]]; then
  echo "Insufficient disk space: ${FREE_MB} MB free, ${MIN_FREE_MB} MB required" >&2
  exit 1
fi

step "1. Cluster k3d (1 server, 2 agents)"
k3d cluster delete "$CLUSTER" >/dev/null 2>&1 || true
k3d cluster create "$CLUSTER" --servers 1 --agents 2 --image "$K3S_IMAGE" \
  --k3s-arg "--disable=traefik@server:0" --wait --timeout 600s
$K get nodes -o wide

step "2. Application image"
docker build -q -t "$APP_IMAGE" app
k3d image import "$APP_IMAGE" -c "$CLUSTER"

step "3. kube-prometheus-stack ${STACK_VERSION} (lightweight values)"
helm --kube-context "k3d-${CLUSTER}" upgrade --install kps "$STACK_CHART" --version "$STACK_VERSION" \
  --namespace "$NS_MON" --create-namespace -f values/kube-prometheus-stack.yaml --wait --timeout 10m
for _ in $(seq 1 90); do
  $K -n "$NS_MON" get pod prometheus-kps-prometheus-0 >/dev/null 2>&1 && break
  sleep 2
done
$K -n "$NS_MON" wait --for=condition=Ready pod/prometheus-kps-prometheus-0 --timeout=300s
$K -n "$NS_MON" get pods -o wide
echo "--- Stack images ---"
$K -n "$NS_MON" get pods -o jsonpath='{range .items[*].spec.containers[*]}{.image}{"\n"}{end}' | sort -u
disk "after downloading the stack"

step "4. Test application, ServiceMonitor and dashboard"
$K apply -f manifests/app.yaml
$K -n "$NS_APP" rollout status deployment/exp-app --timeout=180s
$K apply -f manifests/servicemonitor.yaml
# The versioned dashboard is published in a ConfigMap that the Grafana sidecar loads.
$K -n "$NS_MON" create configmap exp-dashboard --from-file=dashboards/collector-service.json \
  --dry-run=client -o yaml | $K apply -f -
$K -n "$NS_MON" label configmap exp-dashboard grafana_dashboard=1 --overwrite

step "5. Collection: waiting for the Prometheus target"
forward "$NS_MON" kps-prometheus 19090 9090 /-/ready
UP=""
for _ in $(seq 1 120); do
  UP=$(curl -s --max-time 5 --get "${PROM_URL}/api/v1/query" --data-urlencode 'query=up{job="exp-app"}' |
    python3 -c 'import json,sys; r=json.load(sys.stdin)["data"]["result"]; print(r[0]["value"][1] if r else "")' || true)
  [[ "$UP" == "1" ]] && break
  sleep 2
done
echo "up{job=\"exp-app\"} = ${UP:-absent}"
[[ "$UP" == "1" ]] || { echo "The exp-app target is not being scraped" >&2; exit 1; }
sleep 30   # lets metrics-server read the idle stack
top_all "idle, before the load"

# --- Measurement 4: scrape delay -------------------------------------------------------------
step "Measurement 4: delay between a request and its visibility in Prometheus (5 attempts)"
forward "$NS_APP" exp-app 18000 8000 /health/live
PROM_URL="$PROM_URL" APP_URL="$APP_URL" python3 - <<'PY'
import json
import os
import time
import urllib.parse
import urllib.request

prom, app = os.environ["PROM_URL"], os.environ["APP_URL"]
query = 'sum(http_requests_total{job="exp-app",handler="/items"})'


def value() -> float:
    url = f"{prom}/api/v1/query?" + urllib.parse.urlencode({"query": query})
    result = json.load(urllib.request.urlopen(url, timeout=10))["data"]["result"]
    return float(result[0]["value"][1]) if result else 0.0


baseline = value()
pauses = [3.1, 7.7, 1.9, 11.3, 0.0]
delays = []
for i in range(1, 6):
    t0 = time.time()
    urllib.request.urlopen(app + "/items", timeout=10).read()
    while value() <= baseline:
        time.sleep(0.25)
        if time.time() - t0 > 60:
            raise SystemExit("request never visible in Prometheus")
    delays.append(time.time() - t0)
    baseline = value()
    print(f"Attempt {i}: visible after {delays[-1]:.2f} s")
    # Uneven pauses: without them, attempts spaced about 15 s apart would each time land
    # on the same point of the scrape cycle (observed on a first run).
    time.sleep(pauses[i - 1])
print(f"DELAY min {min(delays):.2f} s, mean {sum(delays) / len(delays):.2f} s, "
      f"max {max(delays):.2f} s (ServiceMonitor interval: 15 s)")
PY

# --- Known load ------------------------------------------------------------------------
step "6. Load: ${TOTAL} requests at ${RATE} per second (85 % /items, 10 % /slow, 5 % /fail)"
$K -n "$NS_APP" delete job loadgen --ignore-not-found >/dev/null
sed -e "s|__NAME__|loadgen|" \
  -e "s|__COMMAND__|[\"python\",\"-m\",\"exp.loadgen\",\"--url\",\"http://exp-app.${NS_APP}.svc:8000\",\"--total\",\"${TOTAL}\",\"--rate\",\"${RATE}\"]|" \
  manifests/job.yaml.tmpl | $K apply -f - >/dev/null
$K -n "$NS_APP" wait --for=condition=complete job/loadgen --timeout=400s >/dev/null
LOAD_RESULT=$($K -n "$NS_APP" logs job/loadgen | sed -n 's/^RESULT //p')
echo "$LOAD_RESULT"
echo "Waiting for three scrape cycles (45 s) after the end of the load..."
sleep 45
top_all "just after the load"

# --- Grafana --------------------------------------------------------------------------------
step "7. Grafana: health, data source, dashboard loaded by the sidecar"
forward "$NS_MON" kps-grafana 13000 80 /api/health
GRAFANA_PASSWORD=$($K -n "$NS_MON" get secret kps-grafana -o jsonpath='{.data.admin-password}' | base64 -d) \
  GRAFANA_URL="$GRAFANA_URL" EXPRS_FILE="$WORK/exprs.json" python3 - <<'PY'
import base64
import json
import os
import time
import urllib.parse
import urllib.request

base = os.environ["GRAFANA_URL"]
auth = "Basic " + base64.b64encode(f"admin:{os.environ['GRAFANA_PASSWORD']}".encode()).decode()


def get(path: str) -> object:
    request = urllib.request.Request(base + path, headers={"Authorization": auth})
    return json.load(urllib.request.urlopen(request, timeout=15))


print("GET /api/health:", json.dumps(get("/api/health")))
health = get("/api/datasources/uid/prometheus/health")
print("Prometheus data source (uid prometheus):", json.dumps(health))
found = []
for _ in range(60):  # the sidecar copies the ConfigMap into Grafana within a few seconds
    found = get("/api/search?" + urllib.parse.urlencode({"query": "Collector"}))
    if found:
        break
    time.sleep(2)
print("GET /api/search?query=Collector:", json.dumps(found, ensure_ascii=False))
dash = get("/api/dashboards/uid/collector-service")["dashboard"]
exprs = {}
for panel in dash["panels"]:
    print(f"Panel {panel['id']} '{panel['title']}':")
    for target in panel["targets"]:
        print(f"  [{target['refId']}] {target['expr']}")
        exprs[f"{panel['id']}{target['refId']}"] = target["expr"]
json.dump(exprs, open(os.environ["EXPRS_FILE"], "w"))
assert health["status"] == "OK" and found and len(dash["panels"]) == 5
print("GRAFANA OK: healthy data source, dashboard loaded, 5 panels")
PY

# --- Measurements 1 to 3: Prometheus against ground truth ------------------------------------
step "Measurements 1 to 3: Prometheus against the injected values (queries read from Grafana)"
forward "$NS_MON" kps-prometheus 19090 9090 /-/ready
LOAD_RESULT="$LOAD_RESULT" PROM_URL="$PROM_URL" EXPRS_FILE="$WORK/exprs.json" TOTAL="$TOTAL" RATE="$RATE" \
  python3 - <<'PY'
import json
import os
import urllib.parse
import urllib.request

prom = os.environ["PROM_URL"]
load = json.loads(os.environ["LOAD_RESULT"])
exprs = json.load(open(os.environ["EXPRS_FILE"]))
total, rate = int(os.environ["TOTAL"]), float(os.environ["RATE"])


def query(expr: str, at: float | None = None) -> list[dict[str, object]]:
    params = {"query": expr}
    if at is not None:
        params["time"] = f"{at:.3f}"
    url = f"{prom}/api/v1/query?" + urllib.parse.urlencode(params)
    return json.load(urllib.request.urlopen(url, timeout=15))["data"]["result"]  # type: ignore[no-any-return]


def scalar(expr: str, at: float) -> float:
    return float(query(expr, at)[0]["value"][1])  # type: ignore[index]


end = load["end_ts"]
print(f"Load: start {load['start_ts']}, end {end} (cluster clock), "
      f"duration {end - load['start_ts']:.1f} s")
print("Requests sent:", json.dumps(load["statuses"]))

# Exact counters: the 5 /items requests of measurement 4 are added to the load.
sent: dict[str, int] = {}
for key, count in load["statuses"].items():
    path = key.split()[0]
    sent[path] = sent.get(path, 0) + count
sent["/items"] += 5
print()
print(f"{'Counter http_requests_total':<34}{'Sent':>10}{'Prometheus':>12}{'Gap':>8}")
for row in query('sum by (handler) (http_requests_total{job="exp-app"})'):
    handler = row["metric"]["handler"]  # type: ignore[index]
    seen = float(row["value"][1])  # type: ignore[index]
    print(f"{handler:<34}{sent[handler]:>10}{seen:>12.0f}{seen - sent[handler]:>+8.0f}")

print()
print(f"Instants evaluated: end of the load ({end}), 1-minute window.")
rows = []
inj_rate = rate
got = scalar(exprs["1A"], end)
rows.append(("1. Throughput (req/s)", f"{inj_rate:.2f}", f"{got:.3f}", f"{got - inj_rate:+.3f}",
             f"{(got - inj_rate) / inj_rate * 100:+.1f} %"))
inj_err = load["statuses"].get("/fail 500", 0) / total
got = scalar(exprs["2A"], end)
rows.append(("2. 5xx error rate", f"{inj_err * 100:.2f} %", f"{got * 100:.3f} %",
             f"{(got - inj_err) * 100:+.3f} pt", f"{(got - inj_err) / inj_err * 100:+.1f} %"))
slow_s = 0.2
client = load["client_p95_s"]
for label, key, ref in (
    ("3a. p95 /slow, tight buckets (B)", "3B", slow_s),
    ("3b. p95 /slow, default buckets (C)", "3C", slow_s),
    ("3c. p95 all routes, tight buckets (A)", "3A", slow_s),
):
    got = scalar(exprs[key], end)
    rows.append((label, f"{ref:.3f} s", f"{got:.4f} s", f"{got - ref:+.4f} s",
                 f"{(got - ref) / ref * 100:+.1f} %"))
print(f"{'Measure':<44}{'Injected':>12}{'Prometheus':>14}{'Gap':>13}{'Relative gap':>15}")
for r in rows:
    print(f"{r[0]:<44}{r[1]:>12}{r[2]:>14}{r[3]:>13}{r[4]:>15}")
print()
print("Infrastructure panels (queries read from Grafana, evaluated at the end of the load):")
for key, label in (("4A", "Replicas of the exp-app Deployment"), ("5A", "CPU per pod (cores)")):
    result = query(exprs[key], end)
    if not result:
        raise SystemExit(f"The query of panel {key[0]} returns no value")
    for row in result:
        print(f"  {label}: {row['value'][1]}  {row['metric']}")  # type: ignore[index]
print()
print("p95 latency measured client-side (httpx, load generator):",
      json.dumps(client))
PY

# --- Correlated JSON logs (contrats.md §1) ----------------------------------------------------
step "8. JSON logs and X-Request-ID"
forward "$NS_APP" exp-app 18000 8000 /health/live
curl -s -D - -o /dev/null -H 'X-Request-ID: exp3-corr-check' "${APP_URL}/items" | grep -i '^x-request-id'
sleep 1
$K -n "$NS_APP" logs deploy/exp-app | grep 'exp3-corr-check'
echo "--- Last log line of the load ---"
$K -n "$NS_APP" logs deploy/exp-app | grep -v exp3-corr-check | tail -n 1

# --- Summary -------------------------------------------------------------------------------
step "Summary"
disk "end of the measurements"
echo "--- kubectl top nodes ---"
$K top nodes || true
