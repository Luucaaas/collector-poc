#!/usr/bin/env bash
# Protocole 5 : montée en charge (HPA de 2 à 5 réplicas) et disponibilité (pod supprimé sous charge).
#
#   docs/04-experimentations/05-charge-disponibilite/run.sh
#
# Variables facultatives (valeurs par défaut entre parenthèses) :
#   NOMINAL_USERS (50) NOMINAL_SECONDS (240)   charge de référence, montée comprise
#   PEAK_USERS (200)  PEAK_RATE (5)            pic : utilisateurs, montée par seconde
#   PEAK_MAX_WAIT (420)                        attente maximale des 5 réplicas prêts, en secondes
#   HOLD_AT_FIVE (60) HOLD_AFTER (60)          maintien avant la suppression, puis après le retour
#   SCALE_DOWN_MAX (900)                       attente maximale du retour à 2 réplicas
#   DELETE_POD (1)                             0 : pas de suppression (essai de calibrage)
#   CAPTURES (1)                               0 : pas de captures Grafana (captures.sh)
#   RESULTS_ROOT                               dossier des résultats (défaut : ./resultats)
#
# DIFFÉRENCE AVEC LES PROTOCOLES 1 À 4 : ce script ne crée ni ne supprime le cluster. Il s'exécute
# sur le cluster déjà déployé par `deploy/local/deploy.sh all <tag>` (la montée en charge de l'HPA
# se mesure sur le déploiement réel, pas sur un cluster jetable). Il refuse de démarrer si
# `smoke.sh` échoue ou si un composant n'est pas à 2 réplicas.
#
# Sur le cluster, il ne fait que du trafic HTTP, des lectures (kubectl get, top, port-forward) et UNE
# modification : `kubectl delete pod` sur un pod de catalog-service, pendant le pic.
# Les mots de passe sont lus dans deploy/local/.env, donnés aux seuls processus qui en ont besoin
# (Locust, Playwright) en préfixe de commande : jamais affichés, jamais en argument, jamais écrits.
#
# Déroulé :
#   1 vérifications (smoke.sh, 2 réplicas) et relevé de l'environnement ;
#   2 relevé continu toutes les 5 s (HPA, réplicas prêts, pods, CPU) en arrière-plan ;
#   3 Locust : charge nominale, puis pic (tests/load, profil « peak ») ;
#   4 attente des 5 réplicas prêts (ou du délai maximal), maintien, suppression d'un pod,
#     mesure du remplacement, maintien ;
#   5 arrêt de la charge, observation de la réduction jusqu'à 2 réplicas ;
#   6 résumé (tests/load/phases.py), captures Grafana (Playwright), smoke.sh final, anonymisation.
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
    || { echo "Clé $1 absente ou vide dans deploy/local/.env." >&2; return 1; }
}

command -v uv >/dev/null || { echo "uv est requis (brew install uv)." >&2; exit 1; }
command -v mkcert >/dev/null || { echo "mkcert est requis." >&2; exit 1; }
[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env introuvable : le cluster est-il déployé ?" >&2; exit 1; }
# Variables du shell seulement (pas d'export) : donnés en préfixe aux seuls processus concernés.
admin_pw="$(read_var ADMIN_PASSWORD)"; alice_pw="$(read_var ALICE_PASSWORD)"
bob_pw="$(read_var BOB_PASSWORD)"; chloe_pw="$(read_var CHLOE_PASSWORD)"
export REQUESTS_CA_BUNDLE="$(mkcert -CAROOT)/rootCA.pem"   # autorité du cluster, TLS toujours vérifié
[[ -f "$REQUESTS_CA_BUNDLE" ]] || { echo "Autorité mkcert introuvable (mkcert -install fait ?)." >&2; exit 1; }

step "1. Vérifications préalables"
RESULTS_ROOT="${RESULTS_ROOT:-${HERE}/resultats}"
export LOAD_RUN_ID="$(date +%Y%m%d-%H%M)"
RESULTS="${RESULTS_ROOT}/${LOAD_RUN_ID}"
[[ ! -e "$RESULTS" ]] || { echo "${RESULTS} existe déjà (attendre une minute)." >&2; exit 1; }
mkdir -p "$RESULTS"
export LOAD_RESULTS_DIR="$RESULTS"
if ! "${ROOT}/deploy/local/smoke.sh" > "${RESULTS}/smoke-avant.txt" 2>&1; then
  echo "smoke.sh échoue avant le test : arrêt (voir ${RESULTS}/smoke-avant.txt)." >&2; exit 1
fi
echo "smoke.sh : OK"
for name in catalog-service notification-service frontend; do
  replicas="$($K get deploy "$name" -o jsonpath='{.status.readyReplicas}')"
  [[ "$replicas" == 2 ]] || { echo "${name} n'est pas à 2 réplicas prêts (${replicas:-0}) : arrêt." >&2; exit 1; }
done
echo "catalog-service, notification-service, frontend : 2 réplicas prêts"

sampler=""; portforward=""; locust_pid=""
chrono() { printf '%s\t%s\n' "$(now)" "$1" >> "${RESULTS}/chronologie.tsv"; }
# Anonymise ce qui est archivé : nom de la machine (long et court) et dossier personnel.
sanitize() {
  local short; short="$(hostname -s)"
  local mask='s/\Q$ENV{HOST_SHORT}\E(?:\.[\w-]+)*/<machine>/gi; s{/Us[e]rs/[^\/\s"\x27]+}{<home>}g'
  for file in "${RESULTS}"/*.txt "${RESULTS}"/*.tsv "${RESULTS}"/*.csv "${RESULTS}"/*.json "${RESULTS}"/*.md "${RESULTS}"/*.log "${RESULTS}"/*.html; do
    [[ -f "$file" ]] || continue
    HOST_SHORT="$short" perl -pi -e "$mask" "$file"
  done
  # Fichiers compressés : décompression, masquage, recompression.
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

step "2. Environnement"
{
  echo "Date de début : $(date '+%d/%m/%Y %H:%M:%S')"
  echo "macOS : $(sw_vers -productVersion), $(uname -m)"
  echo "Docker : $(docker version --format '{{.Server.Version}}'), $(docker info --format '{{.NCPU}} CPU, {{.MemTotal}} octets de mémoire')"
  echo "k3d $(k3d version | head -n 1 | awk '{print $3}'), k3s des nœuds $($K get nodes -o jsonpath='{.items[0].status.nodeInfo.kubeletVersion}'), $(kubectl version --client | head -n 1), helm $(helm version --short), mkcert $(mkcert -version)"
  echo "Locust : $(cd "$LOAD" && uv run --quiet locust --version | sed 's/ from .*//')"
  echo "Commit du dépôt : $(git -C "$ROOT" rev-parse --short HEAD)"
  echo
  echo "Images déployées :"
  $K get deploy catalog-service notification-service frontend \
    -o jsonpath='{range .items[*]}  {.metadata.name}{"\t"}{.spec.template.spec.containers[0].image}{"\n"}{end}'
  echo
  echo "Digests lus sur les pods :"
  $K get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].imageID}{"\n"}{end}' \
    | grep -E '^(catalog-service|notification-service|frontend)-' | sed 's/^/  /'
  echo
  echo "Ressources de catalog-service (requêtes et limites) :"
  $K get deploy catalog-service -o jsonpath='  {.spec.template.spec.containers[0].resources}{"\n"}'
  echo
  echo "Nœuds :"; kubectl --context "$CTX" top nodes
  echo
  echo "HPA avant :"; $K get hpa
  echo
  echo "Politique de réduction de l'HPA de catalog-service (vide : valeurs par défaut de Kubernetes) :"
  $K get hpa catalog-service -o jsonpath='  {.spec.behavior}{"\n"}'
  echo "Pods avant :"; $K get pods -o wide | grep -E '^(NAME|catalog|notification|frontend)'
} > "${RESULTS}/environnement.txt"
{
  echo "Paramètres : charge nominale ${NOMINAL_USERS} utilisateurs pendant ${NOMINAL_SECONDS} s (montée de 1 par seconde), "
  echo "pic de ${PEAK_USERS} utilisateurs (montée de ${PEAK_RATE} par seconde), attente maximale des 5 réplicas ${PEAK_MAX_WAIT} s,"
  echo "maintien de ${HOLD_AT_FIVE} s à 5 réplicas puis de ${HOLD_AFTER} s après le retour, observation de la réduction ${SCALE_DOWN_MAX} s au plus."
  echo "Exécution du $(date '+%d/%m/%Y %H:%M'), commit $(git -C "$ROOT" rev-parse --short HEAD), images $($K get deploy catalog-service -o jsonpath='{.spec.template.spec.containers[0].image}' | sed 's/@.*//; s/.*://')."
} > "${RESULTS}/parametres.txt"

# Relevé continu toutes les 5 s (lectures seules) : HPA, réplicas prêts, pods, CPU.
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
# Vrai si les 3 composants sont revenus à 2 réplicas (souhaités, existants et prêts).
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

step "3. Locust : charge nominale (${NOMINAL_USERS} utilisateurs, ${NOMINAL_SECONDS} s), puis pic (${PEAK_USERS})"
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

# Attend le début du pic (daté par le profil de charge dans fenetre.json).
peak_start=""
for _ in $(seq 1 $((NOMINAL_SECONDS + 120))); do
  kill -0 "$locust_pid" 2>/dev/null || { echo "Locust s'est arrêté avant le pic (voir locust.log)." >&2; exit 1; }
  peak_start="$(python3 - "${RESULTS}/fenetre.json" <<'PY' 2>/dev/null || true
import json, sys
print(json.load(open(sys.argv[1])).get("peak_start", ""))
PY
)"
  [[ -z "$peak_start" ]] || break
  sleep 1
done
[[ -n "$peak_start" ]] || { echo "Le pic n'a pas démarré." >&2; exit 1; }
echo "Pic démarré ; HPA : $($K get hpa catalog-service --no-headers)"

step "4. Attente des 5 réplicas prêts (au plus ${PEAK_MAX_WAIT} s)"
five=0
for _ in $(seq 1 $((PEAK_MAX_WAIT * 2))); do
  kill -0 "$locust_pid" 2>/dev/null || { echo "Locust s'est arrêté pendant le pic." >&2; exit 1; }
  if [[ "$(ready_count)" == 5 ]]; then five=1; chrono five_ready; break; fi
  sleep 0.5
done
if [[ $five -eq 1 ]]; then
  echo "5 réplicas prêts, maintien ${HOLD_AT_FIVE} s"
  sleep "$HOLD_AT_FIVE"
else
  chrono five_timeout
  echo "5 réplicas non atteints en ${PEAK_MAX_WAIT} s (prêts : $(ready_count)) ; la suppression a lieu quand même." >&2
fi
$K get hpa catalog-service --no-headers

if [[ "$DELETE_POD" == 1 ]]; then
  step "4b. Suppression d'un pod de catalog-service pendant le pic"
  before_ready="$(ready_count)"
  before_names="$($K get pods -l "$CATALOG_LABEL" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}')"
  victim="$($K get pods -l "$CATALOG_LABEL" -o jsonpath='{range .items[?(@.status.containerStatuses[0].ready==true)]}{.metadata.name}{"\n"}{end}' | head -n 1)"
  echo "Pod supprimé : ${victim} ; prêts avant : ${before_ready}"
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
      # Un pod absent de la liste d'avant, prêt et non en cours d'arrêt : le remplaçant.
      while read -r name ready terminating; do
        [[ -n "$name" && "$ready" == true && -z "$terminating" ]] || continue
        echo "$before_names" | grep -qx "$name" || { new_ready=1; chrono new_ready; break; }
      done <<< "$listing"
    fi
    if [[ -n "$gone" && "$(ready_count)" -ge "$before_ready" ]]; then recovered=1; chrono recovered; break; fi
    sleep 0.5
  done
  [[ -n "$recovered" ]] || echo "Réplicas prêts non retrouvés en 180 s après la suppression." >&2
  echo "Remplacement mesuré (voir chronologie.tsv) ; maintien ${HOLD_AFTER} s"
  sleep "$HOLD_AFTER"
fi

step "5. Arrêt de la charge, observation de la réduction (au plus ${SCALE_DOWN_MAX} s)"
: > "${RESULTS}/arret"
chrono stop
wait "$locust_pid" 2>/dev/null || true
locust_pid=""
chrono locust_ended
echo "Charge arrêtée ; HPA : $($K get hpa catalog-service --no-headers)"
back2=0
for _ in $(seq 1 $((SCALE_DOWN_MAX / 5))); do
  if [[ $back2 -eq 0 ]] && catalog_at_rest; then back2=1; chrono catalog_back_2; fi
  if at_rest; then chrono all_back_2; break; fi
  sleep 5
done
at_rest || echo "Les 3 composants ne sont pas revenus à 2 réplicas en ${SCALE_DOWN_MAX} s." >&2
sleep 20   # quelques points de plus sur les graphiques
chrono observation_end
kill "$sampler" 2>/dev/null || true; sampler=""

step "6. Événements, résumé, captures"
# Événements du test, avec leur heure absolue (ceux d'une exécution précédente sont écartés).
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
sleep 35   # deux cycles de collecte (15 s) après la fin
sanitize
(cd "$LOAD" && uv run --quiet python phases.py "$RESULTS" "http://127.0.0.1:${PROM_PORT}")
sanitize

if [[ "$CAPTURES" == 1 ]]; then
  step "6b. Captures du tableau de bord Grafana"
  "${HERE}/captures.sh" "$RESULTS" || echo "Captures Grafana en échec (voir ci-dessus)." >&2
fi

step "7. Fin : état du cluster et smoke.sh"
$K get hpa; $K get pods -o wide | grep -E '^(NAME|catalog|notification|frontend)'
"${ROOT}/deploy/local/smoke.sh" > "${RESULTS}/smoke-apres.txt" 2>&1 \
  && echo "smoke.sh : OK" || echo "smoke.sh : ÉCHEC (voir smoke-apres.txt)" >&2
$K get hpa > "${RESULTS}/hpa-apres.txt"
gzip -9 -f "${RESULTS}/requetes.csv"
rm -f "${RESULTS}/arret"
sanitize
echo "Résultats : ${RESULTS}"
