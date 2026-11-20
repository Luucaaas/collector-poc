#!/usr/bin/env bash
# Checks the observability of the `collector` cluster (task P6-04):
#   1. Prometheus targets: the 2 replicas of the 2 services must be `up`;
#   2. a bit of traffic on the public routes (200 loops of 3 requests);
#   3. each dashboard query is run through the Grafana API (/api/ds/query) for
#      each service: none may return an empty series (except the notification delay, not checkable without a
#      notification created; a panel specific to another service is skipped);
#   4. memory and CPU of the pods (metrics-server).
# Prometheus is not exposed: access through `kubectl port-forward` (closed at the end of the script).
# The Grafana password is read from the `grafana-admin` Secret, written to a 600 file
# (netrc format, read by curl) then deleted: never as an argument and never printed.
#
# Usage: deploy/local/check-monitoring.sh
set -euo pipefail

CTX="k3d-collector"
K="kubectl --context ${CTX} -n collector"
HERE="$(cd "$(dirname "$0")" && pwd)"
DASHBOARD="$(cd "${HERE}/../.." && pwd)/deploy/infra/monitoring/dashboards/collector-service.json"
API="https://api.127.0.0.1.sslip.io"
GRAFANA="grafana.127.0.0.1.sslip.io"
tmp="$(mktemp -d)"
pf=""
trap '[[ -z "$pf" ]] || kill "$pf" 2>/dev/null || true; rm -rf "$tmp"' EXIT
chmod 700 "$tmp"

step() { printf '\n=== %s ===\n' "$*"; }

step "1. Prometheus targets (port-forward 19090)"
$K port-forward svc/kps-prometheus 19090:9090 >/dev/null 2>&1 &
pf=$!
disown "$pf"   # avoids the shell's "Terminated" message on close
for _ in $(seq 1 30); do curl -s -o /dev/null --max-time 2 http://127.0.0.1:19090/-/ready && break; sleep 1; done
# Right after `deploy.sh monitoring`, Prometheus has not loaded the ServiceMonitors yet: we
# retry for up to 3 minutes before concluding it failed.
ok=0
for _ in $(seq 1 60); do
  if curl -s http://127.0.0.1:19090/api/v1/targets | python3 -c '
import json, sys
targets = [t for t in json.load(sys.stdin)["data"]["activeTargets"]
           if t["labels"].get("job") in ("catalog-service", "notification-service")]
for t in sorted(targets, key=lambda t: (t["labels"]["job"], t["labels"]["pod"])):
    print(f'"'"'{t["labels"]["job"]:22} {t["labels"]["pod"]:42} {t["health"]}'"'"')
up = [t for t in targets if t["health"] == "up"]
print(f"{len(up)} targets up out of {len(targets)} (expected: 4 out of 4)")
sys.exit(0 if len(targets) == 4 and len(up) == 4 else 1)' > "${tmp}/targets.txt"; then
    ok=1
    break
  fi
  sleep 3
done
cat "${tmp}/targets.txt"
[[ "$ok" == 1 ]] || { echo "Incomplete Prometheus targets." >&2; exit 1; }

step "2. Traffic (600 requests)"
for _ in $(seq 1 200); do
  curl -s -o /dev/null "${API}/catalog/api/v1/categories"
  curl -s -o /dev/null "${API}/catalog/api/v1/articles"
  curl -s -o /dev/null "${API}/notification/api/v1/me/notifications"   # 401 without a token: counted anyway
done
echo "Done. Waiting for two scrape cycles (35 s) so that rate() has two points."
sleep 35

step "3. Dashboard queries through the Grafana API"
( umask 077; printf 'machine %s login admin password %s\n' "$GRAFANA" \
    "$($K get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d)" > "${tmp}/netrc" )
python3 - "$DASHBOARD" "${tmp}/netrc" "$GRAFANA" <<'PY'
import json, re, subprocess, sys
dash = json.load(open(sys.argv[1]))
netrc, host = sys.argv[2], sys.argv[3]
empty = 0
for svc in ("catalog-service", "notification-service"):
    print(f"-- {svc}")
    for panel in dash["panels"]:
        # Panel whose query sets a `job`: specific to that service, skipped for the others.
        fixed = {j for t in panel["targets"] for j in re.findall(r'job="([a-z-]+)"', t["expr"])}
        if fixed and svc not in fixed:
            print(f"   {panel['title'][:30]:30} | skipped: specific to {', '.join(sorted(fixed))}")
            continue
        for target in panel["targets"]:
            body = {"queries": [{"refId": "A", "datasource": {"type": "prometheus", "uid": "prometheus"},
                                 "expr": target["expr"].replace("$service", svc), "range": True,
                                 "intervalMs": 15000, "maxDataPoints": 300}],
                    "from": "now-5m", "to": "now"}
            out = subprocess.run(["curl", "-s", "--netrc-file", netrc, "-H", "Content-Type: application/json",
                                  "-d", json.dumps(body), f"https://{host}/api/ds/query"],
                                 capture_output=True, text=True).stdout
            res = json.loads(out)["results"]["A"]
            series = []
            for frame in res.get("frames", []):
                values = frame["data"]["values"]
                points = [v for v in (values[1] if len(values) > 1 else []) if v is not None and v == v]
                if points:
                    series.append(points[-1])
            if "error" not in res and not series and "notification_delay_seconds" in target["expr"]:
                # No event has created a notification since startup: the panel is empty
                # without the chain being faulty. This is not a failure, but it is not checked.
                print(f"   {panel['title'][:30]:30} | {target['legendFormat'][:32]:32} | not checkable: no notification created since startup (run the Playwright journeys or Locust)")
                continue
            if "error" in res or not series:
                empty += 1
            shown = ", ".join(f"{v:.4g}" for v in series[:3]) or "EMPTY"
            print(f"   {panel['title'][:30]:30} | {target['legendFormat'][:32]:32} | {len(series)} series, last value: {shown}")
sys.exit(1 if empty else 0)
PY
# Note always true, whatever the value read: the p95 is interpolated between the bounds of
# the services' histogram (0.05 / 0.1 / 0.2 / 0.3 / 0.5 / 1 / 2.5 s), its precision is that of
# those bounds.
echo "Reading the p95: value interpolated between the histogram bounds (0.05 / 0.1 / 0.2 / 0.3 / 0.5 / 1 / 2.5 s)."
echo "A p95 of 0.0475 s (0.95 x 0.05) means that all requests are in the first bucket (under 50 ms)."

step "4. Pod memory and CPU (metrics-server)"
$K top pods --no-headers | sort
$K top pods --no-headers | grep -E 'kps|prometheus|grafana' | python3 -c '
import sys
mem = cpu = 0.0
for line in sys.stdin:
    p = line.split()
    cpu += float(p[1].rstrip("m"))
    mem += float(p[2][:-2]) * {"Ki": 1 / 1024, "Mi": 1, "Gi": 1024}[p[2][-2:]]
print(f"TOTAL observability stack: {mem:.0f} Mi, {cpu:.0f} m CPU")'
