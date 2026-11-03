#!/usr/bin/env bash
# Expérimentation 1 : RabbitMQ sur k3d (voir protocole.md).
# Crée le cluster, déploie RabbitMQ (image officielle, StatefulSet), exécute les scénarios
# A (perte du consommateur), B (perte du broker) et C (message empoisonné), affiche les
# résultats, puis supprime le cluster.
# Usage : ./run.sh [--keep]   (--keep conserve le cluster à la fin)
# La sortie complète est aussi écrite dans resultats/run-AAAAMMJJ-HHMM.log.
set -euo pipefail

# --- Versions figées -------------------------------------------------------------------
K3S_IMAGE="rancher/k3s:v1.35.8-k3s1"
ALPINE_IMAGE="alpine:3.24.3"   # image utilitaire : mesure de l'espace disque de la VM Docker
RABBITMQ_IMAGE="rabbitmq:4.3.5-management"             # lu dans manifests/rabbitmq.yaml
APP_IMAGE="exp-rabbitmq-app:local"                      # aio-pika 10.1.1 (voir app/uv.lock)

# --- Paramètres ------------------------------------------------------------------------
CLUSTER="collector-exp1"
NS="exp"
COUNT=1000
RATE=50
KEEP=false
[[ "${1:-}" == "--keep" ]] && KEEP=true

cd "$(dirname "$0")"
MIN_FREE_MB=5000   # l'exécution consomme 1,5 Go (53,4 → 51,9 Go libres) et le kubelet évince sous environ 3,1 Go libres (relevé lors de l'expérimentation 3)

# Journalise toute la sortie (sans codes de couleur) dans resultats/ : le script se relance
# lui-même à travers `tee`.
if [[ -z "${EXP_LOGGING:-}" ]]; then
  export EXP_LOGGING=1
  mkdir -p resultats
  LOG="resultats/run-$(date +%Y%m%d-%H%M).log"
  echo "Journal complet : ${LOG}"
  ./run.sh "$@" 2>&1 | perl -pe 'BEGIN{$|=1} s/\e\[[0-9;]*m//g' | tee "$LOG"
  exit "${PIPESTATUS[0]}"
fi
K="kubectl --context k3d-${CLUSTER}"
WORK=$(mktemp -d)   # fichiers temporaires (identifiants), supprimé à la sortie
grep -q "image: ${RABBITMQ_IMAGE}\$" manifests/rabbitmq.yaml || { echo "Image du manifeste différente de ${RABBITMQ_IMAGE}" >&2; exit 1; }

step() { printf '\n=== %s ===\n' "$*"; }
disk() { echo "Espace disque libre de la VM Docker ($1) : $(docker run --rm "$ALPINE_IMAGE" df -h / | awk 'NR==2 {print $4 " sur " $2 " (" $5 " utilisé)"}')"; }
now() { python3 -c 'import time; print(f"{time.time():.3f}")'; }

diagnostic() {
  echo "--- Diagnostic (échec) : pods et derniers événements ---"
  $K get pods -A -o wide 2>&1 | tail -n 40 || true
  $K get events -A --sort-by=.lastTimestamp 2>&1 | tail -n 25 || true
}

cleanup() {
  local rc=$?   # code de sortie du script, relevé avant toute autre commande
  rm -rf "$WORK"
  [[ "$rc" -ne 0 ]] && diagnostic
  if [[ "$KEEP" == true ]]; then
    echo "Cluster conservé (--keep) : k3d cluster delete ${CLUSTER} pour le supprimer."
  else
    step "Suppression du cluster"
    k3d cluster delete "$CLUSTER" || true
    disk "après suppression du cluster"
    echo "--- k3d cluster list (après suppression) ---"
    k3d cluster list || true
  fi
  echo "Code de sortie de run.sh : ${rc}"
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
  $K -n "$NS" wait --for=condition=complete "job/$1" --timeout="${2:-300}s" >/dev/null ||
    { echo "Le Job $1 n'est pas terminé après ${2:-300} s" >&2; return 1; }
}

# Attend (au plus $2 secondes) qu'une ressource $1 existe dans le namespace.
wait_exists() {
  for _ in $(seq 1 "$2"); do
    $K -n "$NS" get "$1" >/dev/null 2>&1 && return 0
    sleep 1
  done
  echo "Ressource $1 introuvable après $2 s" >&2
  return 1
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
print(n)' || true)
    last=${last:-0}
    [[ "$last" -ge "$target" ]] && return 0
    sleep 0.2
  done
  echo "Le producteur n'a pas atteint ${target} messages confirmés" >&2
  return 1
}

producer_cmd() { # $1 identifiant, $2 nombre de messages, $3 rang du message empoisonné (0 = aucun)
  echo "[\"python\",\"-m\",\"exp.producer\",\"--run-id\",\"$1\",\"--count\",\"$2\",\"--rate\",\"${RATE}\",\"--poison-at\",\"${3:-0}\"]"
}

# $1 identifiant, $2 nombre de messages, $3 horodatage de suppression (horloge de la VM, 0 = aucun),
# $4 identifiant du message empoisonné (vide = aucun)
analyze() {
  local name="analyze-$(echo "$1" | tr 'A-Z' 'a-z')"
  run_job "$name" "[\"python\",\"-m\",\"exp.analyze\",\"--run-id\",\"$1\",\"--expected\",\"$2\",\"--delete-ts\",\"$3\",\"--poison-id\",\"${4:-}\"]"
  wait_job "$name" 400
  $K -n "$NS" logs "job/$name" | sed -n 's/^RESULT //p'
}

# --- 0. Pré-requis et cluster ------------------------------------------------------------
step "0. Pré-requis et environnement"
for tool in docker k3d kubectl uv python3 perl; do
  command -v "$tool" >/dev/null || { echo "Outil manquant : $tool" >&2; exit 1; }
done
docker info >/dev/null
date "+Date de l'exécution : %d/%m/%Y %H:%M"
echo "macOS $(sw_vers -productVersion) $(uname -m) ; Python hôte $(python3 --version | cut -d' ' -f2) ; $(uv --version | cut -d' ' -f1-2)"
echo "Docker moteur $(docker version --format '{{.Server.Version}}') ; $(docker info --format '{{.NCPU}} CPU, {{.MemTotal}} octets de mémoire')"
k3d version | head -1
kubectl version --client | head -1
FREE_MB=$(docker run --rm "$ALPINE_IMAGE" df -m / | awk 'NR==2 {print $4}')
disk "avant"
if [[ "$FREE_MB" -lt "$MIN_FREE_MB" ]]; then
  echo "Espace disque insuffisant : ${FREE_MB} Mo libres, ${MIN_FREE_MB} Mo requis" >&2
  exit 1
fi

step "1. Cluster k3d (1 server, 2 agents)"
k3d cluster delete "$CLUSTER" >/dev/null 2>&1 || true
k3d cluster create "$CLUSTER" --servers 1 --agents 2 --image "$K3S_IMAGE" \
  --k3s-arg "--disable=traefik@server:0" --wait --timeout 600s
$K get nodes -o wide

step "2. Identifiants RabbitMQ (Secret généré, jamais affiché)"
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

step "3. RabbitMQ (StatefulSet, 1 nœud, image ${RABBITMQ_IMAGE})"
$K apply -f manifests/rabbitmq.yaml
# Le pod n'existe qu'une fois créé par le contrôleur de StatefulSet.
wait_exists pod/rabbitmq-0 60
$K -n "$NS" wait --for=condition=Ready pod/rabbitmq-0 --timeout=300s ||
  { echo "Le pod rabbitmq-0 n'est pas Ready après 300 s" >&2; exit 1; }

step "4. Image de l'application"
docker build -q -t "$APP_IMAGE" app
k3d image import "$APP_IMAGE" -c "$CLUSTER"
$K apply -f manifests/consumer.yaml
$K -n "$NS" rollout status deployment/consumer --timeout=120s ||
  { echo "Le déploiement consumer n'est pas prêt après 120 s" >&2; exit 1; }
disk "après téléchargement de toutes les images"

# Décalage entre l'horloge du Mac et celle du cluster (VM Docker), pour dater les suppressions.
before=$(now)
vm=$($K -n "$NS" exec rabbitmq-0 -c rabbitmq -- date +%s.%N)
after=$(now)
SKEW=$(python3 -c "print(f'{float(\"$vm\") - (float(\"$before\") + float(\"$after\")) / 2:.3f}')")
echo "Décalage horloge cluster - Mac : ${SKEW} s"

# --- Scénario A : perte du consommateur ----------------------------------------------------
# Suppression par kubectl delete pod (sans --force) ; le manifeste du consommateur fixe
# terminationGracePeriodSeconds: 0, donc un délai de grâce de 0 s (arrêt immédiat demandé).
step "Scénario A : suppression du pod consommateur en plein flux"
run_job producer-a "$(producer_cmd A "$COUNT")"
wait_confirmed producer-a $((COUNT / 2))
POD=$($K -n "$NS" get pod -l app=consumer -o jsonpath='{.items[0].metadata.name}')
T0=$(now)
$K -n "$NS" delete pod "$POD" --wait=false
echo "Pod supprimé : ${POD}"
DELETE_TS_A=$(python3 -c "print(float('$T0') + float('$SKEW'))")
wait_job producer-a 300
$K -n "$NS" logs job/producer-a | tail -n 3
RESULT_A=$(analyze A "$COUNT" "$DELETE_TS_A")
echo "$RESULT_A"
$K -n "$NS" wait --for=delete "pod/$POD" --timeout=120s || true

# --- Scénario B : perte du broker -----------------------------------------------------------
step "Scénario B : suppression du pod RabbitMQ en plein flux (volume conservé)"
$K -n "$NS" rollout status deployment/consumer --timeout=120s ||
  { echo "Le déploiement consumer n'est pas prêt après 120 s" >&2; exit 1; }
CONSUMER_POD=$($K -n "$NS" get pod -l app=consumer --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}')
run_job producer-b "$(producer_cmd B "$COUNT")"
wait_confirmed producer-b $((COUNT / 2))
OLD_UID=$($K -n "$NS" get pod rabbitmq-0 -o jsonpath='{.metadata.uid}')
T0=$(now)
$K -n "$NS" delete pod rabbitmq-0 --wait=false
DELETE_TS_B=$(python3 -c "print(float('$T0') + float('$SKEW'))")
GONE_TS_B=""
for _ in $(seq 1 600); do   # au plus 120 s
  uid=$($K -n "$NS" get pod rabbitmq-0 -o jsonpath='{.metadata.uid}' 2>/dev/null || true)
  if [[ -n "$uid" && "$uid" != "$OLD_UID" ]]; then
    GONE_TS_B=$(python3 -c "print(float('$(now)') + float('$SKEW'))")
    break
  fi
  sleep 0.2
done
[[ -n "$GONE_TS_B" ]] || { echo "Le pod rabbitmq-0 n'a pas été recréé en 120 s" >&2; exit 1; }
$K -n "$NS" wait --for=condition=Ready pod/rabbitmq-0 --timeout=300s ||
  { echo "Le pod rabbitmq-0 n'est pas redevenu Ready en 300 s" >&2; exit 1; }
READY_TS_B=$(python3 -c "print(float('$(now)') + float('$SKEW'))")
echo "--- Cause du délai de retour à Ready (pod rabbitmq-0 recréé) ---"
echo "Suppression -> ancien pod disparu, nouveau pod créé (arrêt propre) : $(python3 -c "print(f'{float(\"$GONE_TS_B\") - float(\"$DELETE_TS_B\"):.3f}')") s"
echo "Nouveau pod créé -> Ready : $(python3 -c "print(f'{float(\"$READY_TS_B\") - float(\"$GONE_TS_B\"):.3f}')") s"
$K -n "$NS" get pod rabbitmq-0 -o jsonpath='Conteneur démarré (kubelet) : {.status.containerStatuses[0].state.running.startedAt} ; Ready depuis : {.status.conditions[?(@.type=="Ready")].lastTransitionTime}{"\n"}'
echo "Journal du nœud RabbitMQ (horodatages du moteur de conteneurs, UTC) :"
$K -n "$NS" logs --timestamps pod/rabbitmq-0 | grep -E 'Starting RabbitMQ|node           : |Server startup complete' | cut -c1-110 || true
wait_job producer-b 400
echo "--- Journal du producteur (événements notables) ---"
$K -n "$NS" logs job/producer-b | grep -E 'publish_|amqp_|producer_done' || true
echo "--- Journal du consommateur (événements notables) ---"
$K -n "$NS" logs "$CONSUMER_POD" | grep -E 'amqp_|handle_failed|consumer_start' || true
RESULT_B=$(analyze B "$COUNT" "$DELETE_TS_B")
echo "$RESULT_B"

# --- Scénario C : message empoisonné --------------------------------------------------------
step "Scénario C : un message dont le traitement échoue volontairement (rang 50 sur 100)"
run_job producer-c "$(producer_cmd C 100 50)"
wait_job producer-c 300
$K -n "$NS" logs job/producer-c | tail -n 1
RESULT_C=$(analyze C 100 0 C-00050)
echo "$RESULT_C"
echo "--- Journal du consommateur (remise en file et rejet) ---"
$K -n "$NS" logs "$CONSUMER_POD" | grep -E 'message_requeued|message_rejected' || true

# --- Synthèse -------------------------------------------------------------------------------
step "Synthèse"
disk "fin des scénarios"
echo "--- Mémoire consommée (kubectl top) ---"
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
    ("Messages à traiter", a["expected"], b["expected"]),
    ("Messages distincts traités", a["distinct"], b["distinct"]),
    ("Messages manquants", a["missing"], b["missing"]),
    ("Doublons (traitements en trop)", a["duplicates"], b["duplicates"]),
    ("Messages relivrés (drapeau redelivered)", a["redelivered_ok"], b["redelivered_ok"]),
    ("Suppression -> dernier message de l'ancien pod (s)",
     a.get("old_pod_last_after_delete_s"), "-"),
    ("Suppression -> 1er message du nouveau pod (s)", a.get("new_pod_first_after_delete_s"), "-"),
    ("Silence entre ancien et nouveau pod (s, < 0 = chevauchement)", a.get("handover_gap_s"), "-"),
    ("Suppression -> dernier message avant la coupure (s)", "-",
     round(b["max_gap_start_ts"] - delete_b, 3)),
    ("Suppression -> pod RabbitMQ Ready (s)", "-", round(ready_b - delete_b, 3)),
    ("Pod Ready -> 1er message traité (s)", "-", round(b["max_gap_end_ts"] - ready_b, 3)),
    ("Plus long silence de traitement (s)", a["max_gap_s"], b["max_gap_s"]),
    ("Indisponibilité vue par le producteur (s)", "-", prod["max_outage_s"]),
    ("Indisponibilité vue par le consommateur (s)", "-", cons_outage),
    ("Republications du producteur", "-", prod["retries"]),
]
print(f"{'Mesure':<64}{'A (consommateur)':>20}{'B (broker)':>16}")
for label, va, vb in rows:
    print(f"{label:<64}{va!s:>20}{vb!s:>16}")

print()
print("Scénario C : message empoisonné C-00050")
for label, value in [
    ("Messages sains traités (distincts, sur 99)", c["distinct"]),
    ("Messages sains manquants", c["missing"]),
    ("Tentatives de traitement du message empoisonné", c["poison_attempts"]),
    ("Issues successives", " puis ".join(c["poison_outcomes"])),
    ("Lignes de journal « message_rejected »", rejected_logged),
]:
    print(f"{label:<64}{value!s:>36}")
PY
