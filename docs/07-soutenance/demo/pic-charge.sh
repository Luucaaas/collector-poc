#!/usr/bin/env bash
# Live load peak (under 2 minutes): short, visual version of protocol 5
# (docs/04-experimentations/05-charge-disponibilite). To watch in the terminal:
#
#   docs/07-soutenance/demo/pic-charge.sh
#
# Flow:
#   1. Locust (tests/load, "peak" profile) sends a peak of 300 simulated users right away
#      (no reference load first: protocol 5 already measured it);
#   2. the screen refreshes every 2 s: HPA, catalog-service pods, requests and failures;
#   3. when the 5 replicas are ready (or after 75 s), a catalog-service pod is deleted
#      after a few seconds: automatically, or immediately if you press the "s" key;
#   4. the replacement is timed, the load continues for 10 s, then stops;
#   5. summary: replicas reached, replacement delay, requests, failures.
# The return to 2 replicas then happens on its own (HPA stabilization window: 5 to 10 minutes measured):
# it is not awaited here.
#
# Optional variables (default values in parentheses):
#   PEAK_USERS (300) PEAK_RATE (20)   simulated users, arrival per second (300 and not 200: the 200 peak
#                                     of protocol 5 follows 4 minutes of reference load; here the peak starts
#                                     cold, 300 reaches the 5 replicas more consistently)
#   AFTER_FIVE (12)                   seconds of waiting at 5 replicas before the automatic deletion
#   MAX_WAIT (75)                     maximum wait for the 5 replicas, then deletion anyway
#   AFTER_DELETE (10)                 seconds of load kept after the replicas are back
#   AUTO (1)                          0: deletes only on the "s" key
#
# On the cluster, this script only does HTTP traffic, reads (kubectl get) and ONE
# change: `kubectl delete pod` on a catalog-service pod. It refuses to start if
# catalog-service is not at 2 ready replicas. Passwords are read from deploy/local/.env and
# given only to the Locust process (never displayed, never as an argument, never written).
# If you interrupt (Ctrl+C), Locust is stopped cleanly.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${HERE}/../../.." && pwd)"
LOAD="${ROOT}/tests/load"
ENV_FILE="${ROOT}/deploy/local/.env"
CTX="k3d-collector"
K="kubectl --context ${CTX} -n collector"
API="https://api.127.0.0.1.sslip.io"
LABEL="app.kubernetes.io/name=catalog-service"
PEAK_USERS="${PEAK_USERS:-300}"
PEAK_RATE="${PEAK_RATE:-20}"
AFTER_FIVE="${AFTER_FIVE:-12}"
MAX_WAIT="${MAX_WAIT:-75}"
AFTER_DELETE="${AFTER_DELETE:-10}"
AUTO="${AUTO:-1}"

now() { perl -MTime::HiRes=time -e 'printf "%.3f\n", time'; }
read_var() {
  grep -m1 -E "^$1=" "$ENV_FILE" | cut -d= -f2- | grep . \
    || { echo "Key $1 missing or empty in deploy/local/.env." >&2; return 1; }
}
ready_count() { $K get deploy catalog-service -o jsonpath='{.status.readyReplicas}' 2>/dev/null || true; }

command -v uv >/dev/null || { echo "uv is required (brew install uv)." >&2; exit 1; }
command -v mkcert >/dev/null || { echo "mkcert is required." >&2; exit 1; }
[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env not found: is the cluster deployed?" >&2; exit 1; }
admin_pw="$(read_var ADMIN_PASSWORD)"; alice_pw="$(read_var ALICE_PASSWORD)"
bob_pw="$(read_var BOB_PASSWORD)"; chloe_pw="$(read_var CHLOE_PASSWORD)"
REQUESTS_CA_BUNDLE="$(mkcert -CAROOT)/rootCA.pem"
[[ -f "$REQUESTS_CA_BUNDLE" ]] || { echo "mkcert authority not found (was mkcert -install done?)." >&2; exit 1; }
export REQUESTS_CA_BUNDLE

[[ "$(ready_count)" == 2 ]] || { echo "catalog-service is not at 2 ready replicas: wait for the return to rest (preparer.sh --rapide)." >&2; exit 1; }

WORK="$(mktemp -d)"
LOG="${WORK}/requests.csv"
STOP="${WORK}/stop"
locust_pid=""
tty_mode=0; [[ -t 1 ]] && tty_mode=1
cleanup() {
  if [[ -n "$locust_pid" ]] && kill -0 "$locust_pid" 2>/dev/null; then
    : > "$STOP"; sleep 3; kill "$locust_pid" 2>/dev/null || true
  fi
  [[ -t 0 ]] && stty echo 2>/dev/null || true
  rm -rf "$WORK"
}
trap cleanup EXIT
trap 'echo; echo "Interrupted: stopping Locust."; exit 130' INT TERM

# Number of requests and failures of the load (the "[...]" setup and login lines are excluded).
counts() {
  awk -F, 'NR > 1 && $2 !~ /^\[/ {n++; f += $5} END {printf "%d %d", n, f}' "$LOG" 2>/dev/null || printf '0 0'
}

# Displays the monitoring screen.
screen() {   # $1: message of the status line
  local elapsed total failed
  elapsed="$(python3 -c "print(int($(now) - $t_start))")"
  read -r total failed <<< "$(counts)"
  [[ $tty_mode -eq 1 ]] && printf '\033[H\033[2J'
  echo "LOAD PEAK: ${PEAK_USERS} simulated users, t = ${elapsed} s"
  echo "Requests sent: ${total}    failures: ${failed}"
  echo
  $K get hpa catalog-service || true
  echo
  $K get pods -l "$LABEL" || true
  echo
  echo "$1"
}

: > "$LOG"
echo "Starting Locust (login of admin and chloe, creation of the load category)..."
cd "$LOAD"
LOAD_PROFILE=peak LOAD_NOMINAL_USERS=1 LOAD_NOMINAL_RATE=1 LOAD_NOMINAL_SECONDS=0 \
LOAD_PEAK_USERS="$PEAK_USERS" LOAD_PEAK_RATE="$PEAK_RATE" LOAD_MAX_SECONDS=600 \
LOAD_REQUEST_LOG="$LOG" LOAD_STOP_FILE="$STOP" \
LOAD_ADMIN_PASSWORD="$admin_pw" LOAD_ALICE_PASSWORD="$alice_pw" \
LOAD_BOB_PASSWORD="$bob_pw" LOAD_CHLOE_PASSWORD="$chloe_pw" \
uv run --quiet locust -f locustfile.py --headless --host "$API" \
  --exit-code-on-error 0 --only-summary > "${WORK}/locust.log" 2>&1 &
locust_pid=$!
cd "$HERE"

t_start="$(now)"
max_ready=2; t_five=""
victim=""; t_delete=""; t_new_ready=""; t_recovered=""; fails_at_delete=0
phase=waiting   # waiting -> deleted -> holding
five_since=""
manual=0

# Monitoring loop: one turn every 2 s (`read -t` also serves as a pause and reads the "s" key).
while true; do
  kill -0 "$locust_pid" 2>/dev/null || { echo "Locust stopped (see below)." >&2; tail -5 "${WORK}/locust.log" >&2; exit 1; }
  ready="$(ready_count)"; ready="${ready:-0}"
  t_now="$(now)"
  (( ready > max_ready )) && max_ready=$ready
  if [[ -z "$t_five" && "$ready" -ge 5 ]]; then t_five="$t_now"; fi

  case "$phase" in
    waiting)
      since_start="$(python3 -c "print($t_now - $t_start)")"
      msg="Waiting for the 5 ready replicas (ready: ${ready}/5)."
      [[ -n "$t_five" ]] && msg="5 replicas ready in $(python3 -c "print(f'{$t_five - $t_start:.0f}')") s."
      [[ "$AUTO" == 1 ]] && msg="${msg} Key "s": delete a pod now (otherwise, ${AFTER_FIVE} s after the 5 replicas)." \
        || msg="${msg} Key "s": delete a pod now."
      go=0
      [[ $manual -eq 1 ]] && go=1
      if [[ "$AUTO" == 1 ]]; then
        [[ -n "$t_five" ]] && python3 -c "import sys; sys.exit(0 if $t_now - $t_five >= $AFTER_FIVE else 1)" && go=1
        python3 -c "import sys; sys.exit(0 if $t_now - $t_start >= $MAX_WAIT else 1)" && go=1
      fi
      if [[ $go -eq 1 ]]; then
        victim="$($K get pods -l "$LABEL" -o jsonpath='{range .items[?(@.status.containerStatuses[0].ready==true)]}{.metadata.name}{"\n"}{end}' | sed -n 1p)"
        [[ -n "$victim" ]] || { echo "No ready pod to delete." >&2; exit 1; }
        before_ready="$ready"
        before_names="$($K get pods -l "$LABEL" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}')"
        read -r _ fails_at_delete <<< "$(counts)"
        t_delete="$(now)"
        $K delete pod "$victim" --wait=false >/dev/null
        phase=deleted
        msg="Pod deleted: ${victim}. Kubernetes replaces it."
      fi
      screen "$msg"
      ;;
    deleted)
      listing="$($K get pods -l "$LABEL" -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.containerStatuses[0].ready}{" "}{.metadata.deletionTimestamp}{"\n"}{end}')"
      if [[ -z "$t_new_ready" ]]; then
        while read -r name state terminating; do
          [[ -n "$name" && "$state" == true && -z "$terminating" ]] || continue
          grep -qx "$name" <<< "$before_names" || { t_new_ready="$(now)"; break; }
        done <<< "$listing"
      fi
      if [[ -n "$t_new_ready" && "$ready" -ge "$before_ready" ]]; then
        t_recovered="$(now)"; phase=holding
      fi
      screen "Pod deleted: ${victim}. Waiting for the ready replacement."
      # Maximum delay: with no replacement after 120 s, leave the loop (summary without replacement).
      if python3 -c "import sys; sys.exit(0 if $t_now - $t_delete >= 120 else 1)"; then
        echo "No ready replacement after 120 s: stopping the load." >&2
        break
      fi
      ;;
    holding)
      screen "Replacement ready in $(python3 -c "print(f'{$t_new_ready - $t_delete:.1f}')") s. The load continues for ${AFTER_DELETE} s more."
      python3 -c "import sys; sys.exit(0 if $t_now - $t_recovered >= $AFTER_DELETE else 1)" && break
      ;;
  esac

  if [[ -t 0 ]]; then
    key=""; read -r -s -n 1 -t 2 key || true
    [[ "$key" == s || "$key" == S ]] && manual=1
  else
    sleep 2
  fi
done

# Stopping the load, then summary.
: > "$STOP"
t_stop="$(now)"
wait "$locust_pid" 2>/dev/null || true
locust_pid=""
read -r total failed <<< "$(counts)"
summary="$(python3 - "$LOG" "${t_delete:-0}" "${t_recovered:-$(now)}" <<'PY'
import csv, sys
log, t_delete, t_recovered = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
rows = [r for r in csv.DictReader(open(log)) if not r["name"].startswith("[")]
s5xx = sum(1 for r in rows if r["status"].startswith("5"))
window = [r for r in rows if t_delete <= float(r["epoch"]) <= t_recovered]
failed_window = sum(1 for r in window if r["failed"] == "1")
reads = sorted(float(r["response_ms"]) for r in rows if r["name"] == "GET /articles")
p95 = reads[int(0.95 * (len(reads) - 1))] if reads else 0
print(f"{s5xx} {len(window)} {failed_window} {p95:.0f}")
PY
)"
read -r s5xx window_total window_failed p95 <<< "$summary"
[[ $tty_mode -eq 1 ]] && printf '\033[H\033[2J'
# The summary is displayed then saved (timestamped, without secrets) to resultats/.
mkdir -p "${HERE}/resultats"
SUMMARY_FILE="${HERE}/resultats/pic-$(date +%Y%m%d-%H%M%S).txt"
{
echo "================ LOAD PEAK SUMMARY ================"
echo "Load                : ${PEAK_USERS} simulated users, ${total} requests in $(python3 -c "print(f'{$t_stop - $t_start:.0f}')") s"
if [[ -n "$t_five" ]]; then
  echo "HPA scale-up        : 2 to ${max_ready} ready replicas, 5 reached $(python3 -c "print(f'{$t_five - $t_start:.0f}')") s after the start"
else
  echo "HPA scale-up        : 2 to ${max_ready} ready replicas (5 not reached)"
fi
echo "Pod deleted        : ${victim:-none}"
if [[ -n "$t_new_ready" ]]; then
  echo "Replacement        : replacement ready in $(python3 -c "print(f'{$t_new_ready - $t_delete:.1f}')") s, workforce complete again in $(python3 -c "print(f'{$t_recovered - $t_delete:.1f}')") s"
  echo "During the replacement: ${window_failed} failure(s) out of ${window_total} requests"
fi
echo "Failures in total: ${failed} out of ${total} requests (including ${s5xx} 5xx response(s))"
echo "Catalogue read: p95 = ${p95} ms (I3 threshold: 300 ms)"
echo "Return to 2 replicas: on its own, within 5 to 10 minutes (HPA stabilization window, measured by protocol 5 and the rehearsals)."
echo "========================================================="
} | tee "$SUMMARY_FILE"
echo "Summary saved: ${SUMMARY_FILE#"${ROOT}"/}"
