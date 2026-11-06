#!/usr/bin/env bash
# Exécution de référence du test de charge sur le cluster k3d (indicateur I3 et exigence ENF-14).
#
#   tests/load/run.sh                      50 utilisateurs, montée de 1 par seconde, 6 minutes
#   USERS=20 RUN_TIME=2m tests/load/run.sh essai court (variables facultatives : USERS,
#                                          SPAWN_RATE, RUN_TIME)
#
# Ce que fait le script, dans l'ordre :
#   1. lit les mots de passe de admin, alice, bob et chloe dans deploy/local/.env et les donne à la
#      seule commande Locust (affectations en préfixe de commande, pas d'export) : jamais affichés,
#      jamais en argument de commande, jamais écrits dans un fichier ;
#   2. vérifie que l'API et Keycloak répondent (la vérification TLS reste active : l'autorité de
#      mkcert est fournie à Python par REQUESTS_CA_BUNDLE, rien ne la désactive) ;
#   3. note dans resultats/<AAAAMMJJ-HHMM>/ la date, le tag et les digests lus sur les pods, l'état
#      de l'HPA avant, pendant (toutes les 15 s) et après ;
#   4. lance Locust sans interface (CSV et rapport HTML) ;
#   5. interroge Prometheus (kubectl port-forward temporaire) et écrit resume.md ;
#   6. remplace dans tout ce qui est archivé le nom de la machine par <machine> et le dossier
#      personnel par <home> : ces fichiers sont versionnés.
# Sur le cluster, le script ne fait que du trafic HTTP et des lectures (kubectl get, port-forward).
# Code de sortie : 0 même si une mesure dépasse son seuil (le processus de test n'en fait pas un
# blocage) ; resume.md et le message final le disent clairement. Autre code : le test n'a pas pu
# se dérouler.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${HERE}/../.." && pwd)"
ENV_FILE="${ROOT}/deploy/local/.env"
CTX="k3d-collector"
K="kubectl --context ${CTX} -n collector"
API="https://api.127.0.0.1.sslip.io"
AUTH="https://auth.127.0.0.1.sslip.io"
USERS="${USERS:-50}"
SPAWN_RATE="${SPAWN_RATE:-1}"
RUN_TIME="${RUN_TIME:-6m}"
PROM_PORT=19091

[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env introuvable : le cluster a-t-il été déployé (deploy/local/deploy.sh) ?" >&2; exit 1; }
command -v uv >/dev/null || { echo "uv est requis (brew install uv)." >&2; exit 1; }
command -v mkcert >/dev/null || { echo "mkcert est requis (certificat du cluster)." >&2; exit 1; }

# Valeur d'une clé du .env, jamais affichée ; clé absente : message explicite et arrêt.
read_var() {
  grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | grep . \
    || { echo "Clé $1 absente ou vide dans deploy/local/.env." >&2; return 1; }
}
# Variables du shell seulement (pas d'export) : seule la commande Locust les reçoit, en préfixe.
admin_pw="$(read_var ADMIN_PASSWORD)"
alice_pw="$(read_var ALICE_PASSWORD)"
bob_pw="$(read_var BOB_PASSWORD)"
chloe_pw="$(read_var CHLOE_PASSWORD)"

# Autorité de certification de mkcert : Python n'utilise pas le trousseau de macOS.
export REQUESTS_CA_BUNDLE="$(mkcert -CAROOT)/rootCA.pem"
[[ -f "$REQUESTS_CA_BUNDLE" ]] || { echo "Autorité mkcert introuvable (mkcert -install fait ?)." >&2; exit 1; }

echo "== Vérifications préalables"
curl -fsS --cacert "$REQUESTS_CA_BUNDLE" -o /dev/null "${API}/catalog/api/v1/categories" \
  || { echo "${API}/catalog ne répond pas : le cluster est-il lancé ?" >&2; exit 1; }
curl -fsS --cacert "$REQUESTS_CA_BUNDLE" -o /dev/null "${AUTH}/realms/collector/.well-known/openid-configuration" \
  || { echo "${AUTH} ne répond pas : Keycloak est-il prêt ?" >&2; exit 1; }
$K get deploy catalog-service notification-service >/dev/null \
  || { echo "kubectl ne joint pas le cluster ${CTX}." >&2; exit 1; }

export LOAD_RUN_ID="$(date +%Y%m%d-%H%M)"
RESULTS="${HERE}/resultats/${LOAD_RUN_ID}"
[[ ! -e "$RESULTS" ]] || { echo "${RESULTS} existe déjà (attendre une minute)." >&2; exit 1; }
mkdir -p "$RESULTS"
export LOAD_RESULTS_DIR="$RESULTS"

sampler="" ; portforward=""
# Anonymise ce qui est archivé : nom de la machine (long et court, sans tenir compte de la casse)
# et dossier personnel. Idempotent, relancé après la rédaction de resume.md.
sanitize() {
  local short; short="$(hostname -s)"
  for file in "${RESULTS}"/*; do
    HOST_SHORT="$short" perl -pi -e \
      's/\Q$ENV{HOST_SHORT}\E(?:\.[\w-]+)*/<machine>/gi; s{/Us[e]rs/[^\/\s"\x27]+}{<home>}g' "$file"
  done
}
cleanup() {
  [[ -z "$sampler" ]] || kill "$sampler" 2>/dev/null || true
  [[ -z "$portforward" ]] || kill "$portforward" 2>/dev/null || true
}
trap cleanup EXIT

echo "== Environnement et état de l'HPA avant"
{
  echo "Date de début : $(date '+%d/%m/%Y %H:%M:%S')"
  echo "Paramètres : ${USERS} utilisateurs, montée de ${SPAWN_RATE} par seconde, durée totale ${RUN_TIME}"
  echo "Cible : ${API} (TLS vérifié) ; Keycloak : ${AUTH}"
  echo "Locust : $(cd "$HERE" && uv run --quiet locust --version | sed 's/ from .*//')"
  echo "Commit du dépôt : $(git -C "$ROOT" rev-parse --short HEAD)"
  echo
  echo "Images déployées :"
  $K get deploy catalog-service notification-service frontend \
    -o jsonpath='{range .items[*]}  {.metadata.name}{"\t"}{.spec.template.spec.containers[0].image}{"\n"}{end}'
  echo
  echo "Digests lus sur les pods :"
  $K get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].imageID}{"\n"}{end}' \
    | grep -E '^(catalog-service|notification-service|frontend)-' | sed 's/^/  /'
} > "${RESULTS}/environnement.txt"
{ echo "HPA avant l'exécution ($(date '+%H:%M:%S')) :"; $K get hpa; } > "${RESULTS}/hpa-avant.txt"

# Relevé des réplicas toutes les 15 s pendant l'exécution (lecture seule).
( while true; do
    echo "$(date '+%H:%M:%S')"; $K get hpa --no-headers; sleep 15
  done ) > "${RESULTS}/hpa-evolution.txt" 2>&1 &
sampler=$!
disown "$sampler"

echo "== Locust : ${USERS} utilisateurs, ${RUN_TIME} (montée de ${SPAWN_RATE}/s, statistiques remises à zéro au plateau)"
cd "$HERE"
LOAD_ADMIN_PASSWORD="$admin_pw" LOAD_ALICE_PASSWORD="$alice_pw" \
LOAD_BOB_PASSWORD="$bob_pw" LOAD_CHLOE_PASSWORD="$chloe_pw" \
uv run --quiet locust -f locustfile.py --headless \
  -u "$USERS" -r "$SPAWN_RATE" -t "$RUN_TIME" --reset-stats \
  --csv "${RESULTS}/locust" --html "${RESULTS}/rapport.html" \
  --exit-code-on-error 0 --only-summary 2>&1 | tee "${RESULTS}/locust.log" \
  || true
if [[ ! -f "${RESULTS}/locust_stats.csv" ]] || ! grep -q plateau_start "${RESULTS}/fenetre.json" 2>/dev/null; then
  echo "Le plateau n'a pas été atteint (préparation ou connexion en échec) : voir ${RESULTS}/locust.log." >&2
  exit 1
fi
kill "$sampler" 2>/dev/null || true; sampler=""
{ echo "HPA après l'exécution ($(date '+%H:%M:%S')) :"; $K get hpa; } > "${RESULTS}/hpa-apres.txt"

echo "== Prometheus (port-forward ${PROM_PORT}), attente de la dernière collecte"
$K port-forward svc/kps-prometheus "${PROM_PORT}:9090" >/dev/null 2>&1 &
portforward=$!
disown "$portforward"
for _ in $(seq 1 30); do curl -s -o /dev/null --max-time 2 "http://127.0.0.1:${PROM_PORT}/-/ready" && break; sleep 1; done
sleep 35
sanitize
uv run --quiet python report.py "$RESULTS" "http://127.0.0.1:${PROM_PORT}"
sanitize

echo
echo "Résultats : ${RESULTS}"
if grep -q "Hors seuil" "${RESULTS}/resume.md"; then
  echo "ATTENTION : au moins une mesure dépasse son seuil (code de sortie 0 quand même, voir resume.md)."
fi
exit 0
