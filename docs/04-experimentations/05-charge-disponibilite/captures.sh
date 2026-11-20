#!/usr/bin/env bash
# Captures of the Grafana dashboard "Collector - service" for a run of protocol 5.
#
#   docs/04-experimentations/05-charge-disponibilite/captures.sh <results folder> [<pattern>]
#
# The pattern (optional) keeps only the captures whose file name contains it, to redo
# the missing ones. Before its limit was raised to 768 Mi, Grafana was killed for lack of
# memory (limit of 384 Mi) during a series of captures (see protocole.md, difficulties).
#
# Launched by run.sh (CAPTURES=1) or separately, on an existing results folder: Prometheus only
# keeps 2 h of measurements, so it must be launched within 2 h of the run.
# Writes 4 PNG files to the results folder: grafana-pic-<service>.png (from 1 min before the peak to
# 15 s after the end of the load) and grafana-retour-<service>.png (from 1 min before the load to
# 30 s after the return to 2 replicas), for catalog-service and notification-service.
# The Grafana password is read from deploy/local/.env and given only to the Playwright process as a
# command prefix (never displayed, never as an argument, never written); the spec puts it
# into the field through `evaluate` and never photographs the login page.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${HERE}/../../.." && pwd)"
RESULTS="${1:?usage: captures.sh <results folder> [<pattern>]}"
PATTERN="${2:-}"
ENV_FILE="${ROOT}/deploy/local/.env"
[[ -f "${RESULTS}/fenetre.json" && -f "${RESULTS}/chronologie.tsv" ]] \
  || { echo "${RESULTS} does not contain fenetre.json and chronologie.tsv." >&2; exit 1; }
RESULTS="$(cd "$RESULTS" && pwd)"
grafana_pw="$(grep -E '^GRAFANA_ADMIN_PASSWORD=' "$ENV_FILE" | head -1 | cut -d= -f2- | grep .)" \
  || { echo "Key GRAFANA_ADMIN_PASSWORD missing or empty in deploy/local/.env." >&2; exit 1; }

plan="$(python3 - "$RESULTS" "$PATTERN" <<'PY'
import json, sys
d, pattern = sys.argv[1], sys.argv[2]
w = json.load(open(f"{d}/fenetre.json"))
ev = {}
for line in open(f"{d}/chronologie.tsv"):
    t, n, *_ = line.rstrip("\n").split("\t")
    ev[n] = float(t)
ms = lambda s: int(s * 1000)
peak_from, peak_to = ms(w["peak_start"] - 60), ms(ev["stop"] + 15)
full_from = ms(w["nominal_start"] - 60)
full_to = ms(ev.get("observation_end", ev["stop"]) + 30)
plan = []
for svc in ("catalog-service", "notification-service"):
    plan.append({"file": f"{d}/grafana-pic-{svc}.png", "service": svc, "from": peak_from, "to": peak_to})
    plan.append({"file": f"{d}/grafana-retour-{svc}.png", "service": svc, "from": full_from, "to": full_to})
print(json.dumps([c for c in plan if pattern in c["file"]]))
PY
)"
cd "${ROOT}/frontend"
E2E_BASE_URL="https://app.127.0.0.1.sslip.io" GRAFANA_CAPTURES=1 \
  GRAFANA_PASSWORD="$grafana_pw" GRAFANA_CAPTURE_PLAN="$plan" npx playwright test
