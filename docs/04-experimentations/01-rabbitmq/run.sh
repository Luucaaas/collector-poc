#!/usr/bin/env bash
# Expérimentation 1 : RabbitMQ sur k3d (voir protocole.md).
# Crée le cluster, installe l'opérateur et RabbitMQ, exécute les scénarios A (perte du
# consommateur) et B (perte du broker), affiche les résultats, puis supprime le cluster.
# Usage : ./run.sh [--keep]   (--keep conserve le cluster à la fin)
set -euo pipefail

# --- Versions figées -------------------------------------------------------------------
K3S_IMAGE="rancher/k3s:v1.35.8-k3s1"
CERT_MANAGER_MANIFEST="manifests/cert-manager-v1.21.2.yaml"  # cert-manager v1.21.2 (exigé par l'opérateur)
OPERATOR_MANIFEST="manifests/cluster-operator-v2.23.0.yml" # RabbitMQ Cluster Operator v2.23.0
RABBITMQ_IMAGE="rabbitmq:4.3.5-management"                 # référencée dans manifests/rabbitmq-cluster.yaml
APP_IMAGE="exp-rabbitmq-app:local"                         # aio-pika 10.1.1 (voir app/uv.lock)

# --- Paramètres ------------------------------------------------------------------------
CLUSTER="collector-exp1"
NS="exp"
COUNT=1000
RATE=50
KEEP=false
[[ "${1:-}" == "--keep" ]] && KEEP=true

cd "$(dirname "$0")"
K="kubectl --context k3d-${CLUSTER}"

step() { printf '\n=== %s ===\n' "$*"; }
now() { python3 -c 'import time; print(f"{time.time():.3f}")'; }

cleanup() {
  if [[ "$KEEP" == true ]]; then
    echo "Cluster conservé (--keep) : k3d cluster delete ${CLUSTER} pour le supprimer."
  else
    step "Suppression du cluster"
    k3d cluster delete "$CLUSTER" || true
  fi
}
trap cleanup EXIT

# Rend un Job à partir du modèle et attend sa fin. $1 nom, $2 liste JSON de la commande.
run_job() {
  local name="$1" command="$2"
  $K -n "$NS" delete job "$name" --ignore-not-found >/dev/null
  sed -e "s|__NAME__|${name}|" -e "s|__COMMAND__|${command}|" manifests/job.yaml.tmpl |
    $K apply -f - >/dev/null
}

wait_job() {
  $K -n "$NS" wait --for=condition=complete "job/$1" --timeout="${2:-300}s" >/dev/null
}

# Attend que le producteur ait confirmé au moins $2 messages.
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
print(n)' || echo 0)
    [[ "$last" -ge "$target" ]] && return 0
    sleep 0.2
  done
  echo "Le producteur n'a pas atteint ${target} messages confirmés" >&2
  return 1
}

producer_cmd() { # $1 identifiant du scénario
  echo "[\"python\",\"-m\",\"exp.producer\",\"--run-id\",\"$1\",\"--count\",\"${COUNT}\",\"--rate\",\"${RATE}\"]"
}

analyze() { # $1 identifiant, $2 horodatage de suppression (horloge de la VM)
  local name="analyze-$(echo "$1" | tr 'A-Z' 'a-z')"
  run_job "$name" "[\"python\",\"-m\",\"exp.analyze\",\"--run-id\",\"$1\",\"--expected\",\"${COUNT}\",\"--delete-ts\",\"$2\"]"
  wait_job "$name" 400
  $K -n "$NS" logs "job/$name" | sed -n 's/^RESULT //p'
}

# --- 0. Pré-requis et cluster ------------------------------------------------------------
step "0. Pré-requis"
for tool in docker k3d kubectl uv python3; do
  command -v "$tool" >/dev/null || { echo "Outil manquant : $tool" >&2; exit 1; }
done
docker info >/dev/null
k3d version | head -1
kubectl version --client | head -1

step "1. Cluster k3d (1 server, 2 agents)"
k3d cluster delete "$CLUSTER" >/dev/null 2>&1 || true
k3d cluster create "$CLUSTER" --servers 1 --agents 2 --image "$K3S_IMAGE" \
  --k3s-arg "--disable=traefik@server:0" --wait --timeout 600s
$K get nodes -o wide

step "2a. cert-manager (certificats internes des webhooks de l'opérateur)"
$K apply --server-side -f "$CERT_MANAGER_MANIFEST" >/dev/null
$K -n cert-manager wait --for=condition=Available deployment --all --timeout=300s

step "2b. RabbitMQ Cluster Operator"
$K apply --server-side -f "$OPERATOR_MANIFEST" >/dev/null
$K -n rabbitmq-system rollout status deployment/rabbitmq-cluster-operator --timeout=180s
# Le webhook n'est utilisable qu'une fois son certificat émis par cert-manager.
for _ in $(seq 1 90); do
  $K -n rabbitmq-system get secret cluster-operator-webhook-server-cert >/dev/null 2>&1 && break
  sleep 2
done
$K -n rabbitmq-system get secret cluster-operator-webhook-server-cert >/dev/null

step "3. RabbitmqCluster (1 nœud, image ${RABBITMQ_IMAGE})"
$K create namespace "$NS"
$K apply -f manifests/rabbitmq-cluster.yaml
for _ in $(seq 1 60); do $K -n "$NS" get pod rabbitmq-server-0 >/dev/null 2>&1 && break; sleep 2; done
$K -n "$NS" wait --for=condition=Ready pod/rabbitmq-server-0 --timeout=300s
$K -n "$NS" wait --for=condition=AllReplicasReady rabbitmqcluster/rabbitmq --timeout=300s

step "4. Image de l'application"
docker build -q -t "$APP_IMAGE" app
k3d image import "$APP_IMAGE" -c "$CLUSTER"
$K apply -f manifests/consumer.yaml
$K -n "$NS" rollout status deployment/consumer --timeout=120s

# Décalage entre l'horloge du Mac et celle du cluster (VM Docker), pour dater les suppressions.
before=$(now)
vm=$($K -n "$NS" exec rabbitmq-server-0 -c rabbitmq -- date +%s.%N)
after=$(now)
SKEW=$(python3 -c "print(f'{float(\"$vm\") - (float(\"$before\") + float(\"$after\")) / 2:.3f}')")
echo "Décalage horloge cluster - Mac : ${SKEW} s"

# --- Scénario A : perte du consommateur ----------------------------------------------------
step "Scénario A : suppression du pod consommateur en plein flux"
run_job producer-a "$(producer_cmd A)"
wait_confirmed producer-a $((COUNT / 2))
POD=$($K -n "$NS" get pod -l app=consumer -o jsonpath='{.items[0].metadata.name}')
T0=$(now)
$K -n "$NS" delete pod "$POD" --grace-period=0 --force
echo "Pod supprimé : ${POD}"
DELETE_TS_A=$(python3 -c "print(float('$T0') + float('$SKEW'))")
wait_job producer-a 300
$K -n "$NS" logs job/producer-a | tail -n 3
RESULT_A=$(analyze A "$DELETE_TS_A")
echo "$RESULT_A"

# --- Scénario B : perte du broker -----------------------------------------------------------
step "Scénario B : suppression du pod RabbitMQ en plein flux (volume conservé)"
CONSUMER_POD=$($K -n "$NS" get pod -l app=consumer -o jsonpath='{.items[0].metadata.name}')
run_job producer-b "$(producer_cmd B)"
wait_confirmed producer-b $((COUNT / 2))
OLD_UID=$($K -n "$NS" get pod rabbitmq-server-0 -o jsonpath='{.metadata.uid}')
T0=$(now)
$K -n "$NS" delete pod rabbitmq-server-0 --grace-period=0 --force
DELETE_TS_B=$(python3 -c "print(float('$T0') + float('$SKEW'))")
for _ in $(seq 1 120); do
  uid=$($K -n "$NS" get pod rabbitmq-server-0 -o jsonpath='{.metadata.uid}' 2>/dev/null || true)
  [[ -n "$uid" && "$uid" != "$OLD_UID" ]] && break
  sleep 1
done
$K -n "$NS" wait --for=condition=Ready pod/rabbitmq-server-0 --timeout=300s
wait_job producer-b 400
echo "--- Journal du producteur (événements notables) ---"
$K -n "$NS" logs job/producer-b | grep -E 'publish_|amqp_|producer_done' || true
echo "--- Journal du consommateur (événements notables) ---"
$K -n "$NS" logs "$CONSUMER_POD" | grep -E 'amqp_|handle_failed|consumer_start' || true
RESULT_B=$(analyze B "$DELETE_TS_B")
echo "$RESULT_B"

# --- Synthèse -------------------------------------------------------------------------------
step "Synthèse"
echo "--- Mémoire consommée (kubectl top) ---"
$K top pods -n cert-manager || true
$K top pods -n rabbitmq-system || true
$K top pods -n "$NS" || true
PROD_B=$($K -n "$NS" logs job/producer-b | grep producer_done)
CONS_LOG=$($K -n "$NS" logs "$CONSUMER_POD" | grep -E 'amqp_' || true)
RESULT_A="$RESULT_A" RESULT_B="$RESULT_B" PROD_B="$PROD_B" CONS_LOG="$CONS_LOG" python3 - <<'PY'
import json
import os

a = json.loads(os.environ["RESULT_A"])
b = json.loads(os.environ["RESULT_B"])
prod = json.loads(os.environ["PROD_B"])
events = [json.loads(x) for x in os.environ["CONS_LOG"].splitlines() if x.strip()]
lost = [e["ts"] for e in events if e["event"] == "amqp_connection_lost"]
back = [e["ts"] for e in events if e["event"] == "amqp_reconnected"]
cons_outage = round(back[-1] - lost[0], 3) if lost and back else None

rows = [
    ("Messages publiés et confirmés", a["expected"], b["expected"]),
    ("Messages distincts reçus", a["distinct"], b["distinct"]),
    ("Messages manquants", a["missing"], b["missing"]),
    ("Doublons (accusés en trop)", a["duplicates"], b["duplicates"]),
    ("Accusés marqués redelivered", a["redelivered_flag"], b["redelivered_flag"]),
    ("Suppression -> 1er message traité (s)", a.get("delete_to_first_processed_s"),
     b.get("delete_to_first_processed_s")),
    ("Plus grand silence de traitement (s)", a["max_gap_s"], b["max_gap_s"]),
    ("Indisponibilité vue par le producteur (s)", "-", prod["max_outage_s"]),
    ("Indisponibilité vue par le consommateur (s)", "-", cons_outage),
    ("Tentatives de republication du producteur", "-", prod["retries"]),
]
print(f"{'Mesure':<48}{'A (consommateur)':>20}{'B (broker)':>16}")
for label, va, vb in rows:
    print(f"{label:<48}{va!s:>20}{vb!s:>16}")
PY
