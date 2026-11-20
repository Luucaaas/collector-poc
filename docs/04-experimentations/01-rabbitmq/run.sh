#!/usr/bin/env bash
# Experiment 1: RabbitMQ on k3d (see protocole.md).
# Creates the cluster, deploys RabbitMQ (official image, StatefulSet), runs scenarios
# A (consumer loss), B (broker loss) and C (poison message), prints the
# results, then deletes the cluster.
# Usage: ./run.sh [--keep]   (--keep keeps the cluster at the end)
# The full output is also written to resultats/run-YYYYMMDD-HHMM.log.
set -euo pipefail

# --- Pinned versions -------------------------------------------------------------------
K3S_IMAGE="rancher/k3s:v1.35.8-k3s1"
ALPINE_IMAGE="alpine:3.24.3"   # utility image: measures the disk space of the Docker VM
RABBITMQ_IMAGE="rabbitmq:4.3.5-management"             # read from manifests/rabbitmq.yaml
APP_IMAGE="exp-rabbitmq-app:local"                      # aio-pika 10.1.1 (see app/uv.lock)

# --- Parameters ------------------------------------------------------------------------
CLUSTER="collector-exp1"
NS="exp"
COUNT=1000
RATE=50
KEEP=false
[[ "${1:-}" == "--keep" ]] && KEEP=true

cd "$(dirname "$0")"
MIN_FREE_MB=5000   # the run uses 1.5 GB (53.4 -> 51.9 GB free) and the kubelet evicts below about 3.1 GB free (measured during experiment 3)

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
WORK=$(mktemp -d)   # temporary files (credentials), removed on exit
grep -q "image: ${RABBITMQ_IMAGE}\$" manifests/rabbitmq.yaml || { echo "Manifest image differs from ${RABBITMQ_IMAGE}" >&2; exit 1; }

step() { printf '\n=== %s ===\n' "$*"; }
disk() { echo "Free disk space of the Docker VM ($1): $(docker run --rm "$ALPINE_IMAGE" df -h / | awk 'NR==2 {print $4 " of " $2 " (" $5 " used)"}')"; }
now() { python3 -c 'import time; print(f"{time.time():.3f}")'; }

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

# Renders a Job from the template and waits for it to finish. $1 name, $2 JSON list of the command.
run_job() {
  local name="$1" command="$2"
  $K -n "$NS" delete job "$name" --ignore-not-found >/dev/null
  sed -e "s|__NAME__|${name}|" -e "s|__COMMAND__|${command}|" manifests/job.yaml.tmpl |
    $K apply -f - >/dev/null
}

wait_job() {
  $K -n "$NS" wait --for=condition=complete "job/$1" --timeout="${2:-300}s" >/dev/null ||
    { echo "Job $1 did not complete after ${2:-300} s" >&2; return 1; }
}

# Waits (at most $2 seconds) for a resource $1 to exist in the namespace.
wait_exists() {
  for _ in $(seq 1 "$2"); do
    $K -n "$NS" get "$1" >/dev/null 2>&1 && return 0
    sleep 1
  done
  echo "Resource $1 not found after $2 s" >&2
  return 1
}

# Waits until the producer has confirmed at least $2 messages.
wait_confirmed() {
  local job="$1" target="$2" last=0
  for _ in $(seq 1 600); do
    last=$($K -n "$NS" logs "job/$job" 2>/dev/null |
      python3 -c '
import json, sys
n = 0
for line in sys.stdin:
    try:
        d = json.loads(line)
    except ValueError:
        continue
    if d.get("event") == "progress":
        n = d["confirmed"]
print(n)' || true)
    last=${last:-0}
    [[ "$last" -ge "$target" ]] && return 0
    sleep 0.2
  done
  echo "The producer did not reach ${target} confirmed messages" >&2
  return 1
}

producer_cmd() { # $1 id, $2 number of messages, $3 rank of the poison message (0 = none)
  echo "[\"python\",\"-m\",\"exp.producer\",\"--run-id\",\"$1\",\"--count\",\"$2\",\"--rate\",\"${RATE}\",\"--poison-at\",\"${3:-0}\"]"
}

# $1 id, $2 number of messages, $3 deletion timestamp (VM clock, 0 = none),
# $4 id of the poison message (empty = none)
analyze() {
  local name="analyze-$(echo "$1" | tr 'A-Z' 'a-z')"
  run_job "$name" "[\"python\",\"-m\",\"exp.analyze\",\"--run-id\",\"$1\",\"--expected\",\"$2\",\"--delete-ts\",\"$3\",\"--poison-id\",\"${4:-}\"]"
  wait_job "$name" 400
  $K -n "$NS" logs "job/$name" | sed -n 's/^RESULT //p'
}

# --- 0. Prerequisites and cluster ------------------------------------------------------
step "0. Prerequisites and environment"
for tool in docker k3d kubectl uv python3 perl; do
  command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
done
docker info >/dev/null
date "+Run date:%d/%m/%Y %H:%M"
echo "macOS $(sw_vers -productVersion) $(uname -m) ; host Python $(python3 --version | cut -d' ' -f2) ; $(uv --version | cut -d' ' -f1-2)"
echo "Docker moteur $(docker version --format '{{.Server.Version}}') ; $(docker info --format '{{.NCPU}} CPU, {{.MemTotal}} bytes of memory')"
k3d version | head -1
kubectl version --client | head -1
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

step "2. RabbitMQ credentials (generated Secret, never displayed)"
$K create namespace "$NS"
(
  umask 077
  python3 - "$WORK/rabbitmq.env" <<'PY'
import secrets
import sys

with open(sys.argv[1], "w") as f:
    f.write("RABBITMQ_DEFAULT_USER=exp\n")
    f.write(f"RABBITMQ_DEFAULT_PASS={secrets.token_urlsafe(24)}\n")
PY
)
$K -n "$NS" create secret generic rabbitmq-credentials --from-env-file="$WORK/rabbitmq.env" >/dev/null
rm -f "$WORK/rabbitmq.env"

step "3. RabbitMQ (StatefulSet, 1 node, image ${RABBITMQ_IMAGE})"
$K apply -f manifests/rabbitmq.yaml
# The pod only exists once created by the StatefulSet controller.
wait_exists pod/rabbitmq-0 60
$K -n "$NS" wait --for=condition=Ready pod/rabbitmq-0 --timeout=300s ||
  { echo "Pod rabbitmq-0 is not Ready after 300 s" >&2; exit 1; }

step "4. Application image"
docker build -q -t "$APP_IMAGE" app
k3d image import "$APP_IMAGE" -c "$CLUSTER"
$K apply -f manifests/consumer.yaml
$K -n "$NS" rollout status deployment/consumer --timeout=120s ||
  { echo "Deployment consumer is not ready after 120 s" >&2; exit 1; }
disk "after downloading all the images"

# Offset between the Mac clock and the cluster clock (Docker VM), to date the deletions.
before=$(now)
vm=$($K -n "$NS" exec rabbitmq-0 -c rabbitmq -- date +%s.%N)
after=$(now)
SKEW=$(python3 -c "print(f'{float(\"$vm\") - (float(\"$before\") + float(\"$after\")) / 2:.3f}')")
echo "Cluster - Mac clock offset: ${SKEW} s"

# --- Scenario A: consumer loss -------------------------------------------------------
# Deletion by kubectl delete pod (without --force); the consumer manifest sets
# terminationGracePeriodSeconds: 0, hence a 0 s grace period (immediate stop requested).
step "Scenario A: deleting the consumer pod mid-stream"
run_job producer-a "$(producer_cmd A "$COUNT")"
wait_confirmed producer-a $((COUNT / 2))
POD=$($K -n "$NS" get pod -l app=consumer -o jsonpath='{.items[0].metadata.name}')
T0=$(now)
$K -n "$NS" delete pod "$POD" --wait=false
echo "Pod deleted: ${POD}"
DELETE_TS_A=$(python3 -c "print(float('$T0') + float('$SKEW'))")
wait_job producer-a 300
$K -n "$NS" logs job/producer-a | tail -n 3
RESULT_A=$(analyze A "$COUNT" "$DELETE_TS_A")
echo "$RESULT_A"
$K -n "$NS" wait --for=delete "pod/$POD" --timeout=120s || true

# --- Scenario B: broker loss -----------------------------------------------------------
step "Scenario B: deleting the RabbitMQ pod mid-stream (volume kept)"
$K -n "$NS" rollout status deployment/consumer --timeout=120s ||
  { echo "Deployment consumer is not ready after 120 s" >&2; exit 1; }
CONSUMER_POD=$($K -n "$NS" get pod -l app=consumer --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}')
run_job producer-b "$(producer_cmd B "$COUNT")"
wait_confirmed producer-b $((COUNT / 2))
OLD_UID=$($K -n "$NS" get pod rabbitmq-0 -o jsonpath='{.metadata.uid}')
T0=$(now)
$K -n "$NS" delete pod rabbitmq-0 --wait=false
DELETE_TS_B=$(python3 -c "print(float('$T0') + float('$SKEW'))")
GONE_TS_B=""
for _ in $(seq 1 600); do   # at most 120 s
  uid=$($K -n "$NS" get pod rabbitmq-0 -o jsonpath='{.metadata.uid}' 2>/dev/null || true)
  if [[ -n "$uid" && "$uid" != "$OLD_UID" ]]; then
    GONE_TS_B=$(python3 -c "print(float('$(now)') + float('$SKEW'))")
    break
  fi
  sleep 0.2
done
[[ -n "$GONE_TS_B" ]] || { echo "Pod rabbitmq-0 was not recreated within 120 s" >&2; exit 1; }
$K -n "$NS" wait --for=condition=Ready pod/rabbitmq-0 --timeout=300s ||
  { echo "Pod rabbitmq-0 did not become Ready again within 300 s" >&2; exit 1; }
READY_TS_B=$(python3 -c "print(float('$(now)') + float('$SKEW'))")
echo "--- Cause of the delay before Ready again (pod rabbitmq-0 recreated) ---"
echo "Deletion -> old pod gone, new pod created (clean shutdown): $(python3 -c "print(f'{float(\"$GONE_TS_B\") - float(\"$DELETE_TS_B\"):.3f}')") s"
echo "New pod created -> Ready: $(python3 -c "print(f'{float(\"$READY_TS_B\") - float(\"$GONE_TS_B\"):.3f}')") s"
$K -n "$NS" get pod rabbitmq-0 -o jsonpath='Container started (kubelet): {.status.containerStatuses[0].state.running.startedAt} ; Ready since: {.status.conditions[?(@.type=="Ready")].lastTransitionTime}{"\n"}'
echo "RabbitMQ node log (container runtime timestamps, UTC):"
$K -n "$NS" logs --timestamps pod/rabbitmq-0 | grep -E 'Starting RabbitMQ|node           : |Server startup complete' | cut -c1-110 || true
wait_job producer-b 400
echo "--- Producer log (notable events) ---"
$K -n "$NS" logs job/producer-b | grep -E 'publish_|amqp_|producer_done' || true
echo "--- Consumer log (notable events) ---"
$K -n "$NS" logs "$CONSUMER_POD" | grep -E 'amqp_|handle_failed|consumer_start' || true
RESULT_B=$(analyze B "$COUNT" "$DELETE_TS_B")
echo "$RESULT_B"

# --- Scenario C: poison message -------------------------------------------------------
step "Scenario C: a message whose processing deliberately fails (rank 50 of 100)"
run_job producer-c "$(producer_cmd C 100 50)"
wait_job producer-c 300
$K -n "$NS" logs job/producer-c | tail -n 1
RESULT_C=$(analyze C 100 0 C-00050)
echo "$RESULT_C"
echo "--- Consumer log (requeue and rejection) ---"
$K -n "$NS" logs "$CONSUMER_POD" | grep -E 'message_requeued|message_rejected' || true

# --- Summary --------------------------------------------------------------------------
step "Summary"
disk "end of the scenarios"
echo "--- Memory used (kubectl top) ---"
$K top pods -n "$NS" || true
PROD_B=$($K -n "$NS" logs job/producer-b | grep producer_done)
CONS_LOG=$($K -n "$NS" logs "$CONSUMER_POD" | grep -E 'amqp_' || true)
REJECT_LOG=$($K -n "$NS" logs "$CONSUMER_POD" | grep -E 'message_rejected' || true)
RESULT_A="$RESULT_A" RESULT_B="$RESULT_B" RESULT_C="$RESULT_C" PROD_B="$PROD_B" \
  CONS_LOG="$CONS_LOG" REJECT_LOG="$REJECT_LOG" DELETE_TS_B="$DELETE_TS_B" READY_TS_B="$READY_TS_B" \
  python3 - <<'PY'
import json
import os

a = json.loads(os.environ["RESULT_A"])
b = json.loads(os.environ["RESULT_B"])
c = json.loads(os.environ["RESULT_C"])
prod = json.loads(os.environ["PROD_B"])
delete_b = float(os.environ["DELETE_TS_B"])
ready_b = float(os.environ["READY_TS_B"])
events = [json.loads(x) for x in os.environ["CONS_LOG"].splitlines() if x.strip()]
lost = [e["ts"] for e in events if e["event"] == "amqp_connection_lost"]
back = [e["ts"] for e in events if e["event"] == "amqp_reconnected"]
cons_outage = round(back[-1] - lost[0], 3) if lost and back else None
rejected_logged = len([x for x in os.environ["REJECT_LOG"].splitlines() if "C-00050" in x])

rows = [
    ("Messages to process", a["expected"], b["expected"]),
    ("Distinct messages processed", a["distinct"], b["distinct"]),
    ("Missing messages", a["missing"], b["missing"]),
    ("Duplicates (extra processings)", a["duplicates"], b["duplicates"]),
    ("Redelivered messages (redelivered flag)", a["redelivered_ok"], b["redelivered_ok"]),
    ("Deletion -> last message of the old pod (s)",
     a.get("old_pod_last_after_delete_s"), "-"),
    ("Deletion -> 1st message of the new pod (s)", a.get("new_pod_first_after_delete_s"), "-"),
    ("Silence between old and new pod (s, < 0 = overlap)", a.get("handover_gap_s"), "-"),
    ("Deletion -> last message before the cut (s)", "-",
     round(b["max_gap_start_ts"] - delete_b, 3)),
    ("Deletion -> RabbitMQ pod Ready (s)", "-", round(ready_b - delete_b, 3)),
    ("Pod Ready -> 1st message processed (s)", "-", round(b["max_gap_end_ts"] - ready_b, 3)),
    ("Longest processing silence (s)", a["max_gap_s"], b["max_gap_s"]),
    ("Unavailability seen by the producer (s)", "-", prod["max_outage_s"]),
    ("Unavailability seen by the consumer (s)", "-", cons_outage),
    ("Producer republications", "-", prod["retries"]),
]
print(f"{'Measure':<64}{'A (consumer)':>20}{'B (broker)':>16}")
for label, va, vb in rows:
    print(f"{label:<64}{va!s:>20}{vb!s:>16}")

print()
print("Scenario C: poison message C-00050")
for label, value in [
    ("Healthy messages processed (distinct, out of 99)", c["distinct"]),
    ("Healthy messages missing", c["missing"]),
    ("Processing attempts of the poison message", c["poison_attempts"]),
    ("Successive outcomes", " then ".join(c["poison_outcomes"])),
    ("\"message_rejected\" log lines", rejected_logged),
]:
    print(f"{label:<64}{value!s:>36}")
PY
