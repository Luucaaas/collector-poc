#!/usr/bin/env bash
# Expérimentation 2 : Keycloak, Traefik et TLS mkcert sur k3d (voir protocole.md).
# Crée le cluster (ports 80 et 443 publiés), configure Traefik (certificat mkcert par défaut,
# redirection HTTP -> HTTPS), installe PostgreSQL et Keycloak (images officielles) avec le realm
# `collector`, déploie une API FastAPI qui valide les JWT, mesure le TLS,
# la redirection, la matrice d'autorisation, `iss`, le cache JWKS et les ressources, puis supprime
# le cluster.
# Usage : ./run.sh [--keep]   (--keep conserve le cluster à la fin)
# La sortie complète est aussi écrite dans resultats/run-AAAAMMJJ-HHMM.log.
# Le certificat (clé privée comprise) et les mots de passe générés sont écrits dans .local/,
# ignoré par Git ; ils ne sont jamais affichés.
set -euo pipefail

# --- Versions figées -------------------------------------------------------------------
K3S_IMAGE="rancher/k3s:v1.35.8-k3s1"
ALPINE_IMAGE="alpine:3.24.3"   # image utilitaire : mesure de l'espace disque de la VM Docker
# Infrastructure par les images officielles et des manifestes simples : ni opérateur, ni CRD
# ajoutée, ni cert-manager (décision du 03/11/2026).
KEYCLOAK_IMAGE="quay.io/keycloak/keycloak:26.8.0"   # lu dans manifests/keycloak.yaml
POSTGRES_IMAGE="postgres:18.4-alpine"               # lu dans manifests/postgres.yaml
APP_IMAGE="exp-keycloak-tls-app:local"   # FastAPI 0.142.2, PyJWT 2.14.0, httpx 0.28.1, structlog 26.1.0,
                                         # uvicorn 0.52.4 (voir app/uv.lock)

# --- Paramètres ------------------------------------------------------------------------
CLUSTER="collector-exp2"
KC_HOST="auth.127.0.0.1.sslip.io"
API_HOST="api.127.0.0.1.sslip.io"
BURST=200      # requêtes pour mesurer le cache JWKS
KEEP=false
[[ "${1:-}" == "--keep" ]] && KEEP=true

cd "$(dirname "$0")"
MIN_FREE_MB=7000   # l'exécution consomme 3,7 Go (53,5 → 49,8 Go libres) et le kubelet évince sous environ 3,1 Go libres (relevé lors de l'expérimentation 3)

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
WORK=$(mktemp -d)   # fichiers temporaires (realm rendu), supprimé à la sortie
export WORK
LOCAL=".local"
CAROOT_DIR="$(mkcert -CAROOT)"
CA_FILE="${CAROOT_DIR}/rootCA.pem"

step() { printf '\n=== %s ===\n' "$*"; }
disk() { echo "Espace disque libre de la VM Docker ($1) : $(docker run --rm "$ALPINE_IMAGE" df -h / | awk 'NR==2 {print $4 " sur " $2 " (" $5 " utilisé)"}')"; }

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

# Relance une commande jusqu'à ce qu'elle réussisse. $1 nombre d'essais, $2 pause, le reste : commande.
retry() {
  local tries="$1" pause="$2"
  shift 2
  for _ in $(seq 1 "$tries"); do
    "$@" && return 0
    sleep "$pause"
  done
  echo "Échec après ${tries} essais : $*" >&2
  return 1
}

# Relève mémoire et CPU des pods (metrics-server de k3s). $1 libellé.
top_all() {
  echo "--- Mémoire et CPU des pods ($1) ---"
  local out=""
  for _ in $(seq 1 60); do
    out=$($K top pods -A --no-headers 2>/dev/null | grep -E '^(keycloak|exp|kube-system) ' | grep -E 'keycloak|postgres|exp-api|traefik' || true)
    [[ "$(echo "$out" | grep -c .)" -ge 5 ]] && break
    sleep 3
  done
  echo "$out"
  OUT="$out" LABEL="$1" python3 - <<'PYEOF'
import os

groups = {
    "keycloak-": "Keycloak",
    "postgres-0": "PostgreSQL",
    "exp-api": "API de test",
    "traefik": "Traefik",
}
sums: dict[str, tuple[float, float]] = {}
for line in os.environ["OUT"].splitlines():
    p = line.split()
    if len(p) < 4:
        continue
    pod, cpu, mem = p[1], float(p[2].rstrip("m")), p[3]
    value = float(mem[:-2]) * {"Ki": 1 / 1024, "Mi": 1, "Gi": 1024}[mem[-2:]]
    for prefix, label in groups.items():
        if pod.startswith(prefix):
            c, m = sums.get(label, (0.0, 0.0))
            sums[label] = (c + cpu, m + value)
print(f"RESSOURCES ({os.environ['LABEL']})")
for label, (c, m) in sums.items():
    print(f"  {label:<28}{m:>7.0f} Mi{c:>7.0f} m CPU")
total_m = sum(m for _, m in sums.values())
total_c = sum(c for c, _ in sums.values())
print(f"  {'TOTAL':<28}{total_m:>7.0f} Mi{total_c:>7.0f} m CPU")
PYEOF
}

# --- 0. Pré-requis et environnement ---------------------------------------------------------
step "0. Pré-requis et environnement"
for tool in docker k3d kubectl uv python3 perl curl openssl mkcert lsof; do
  command -v "$tool" >/dev/null || { echo "Outil manquant : $tool" >&2; exit 1; }
done
docker info >/dev/null
[[ -f "$CA_FILE" ]] || { echo "CA mkcert introuvable : lancer mkcert -install (hors de ce script)" >&2; exit 1; }
date "+Date de l'exécution : %d/%m/%Y %H:%M"
echo "macOS $(sw_vers -productVersion) $(uname -m) ; Python hôte $(python3 --version | cut -d' ' -f2) ; $(uv --version | cut -d' ' -f1-2)"
echo "Docker moteur $(docker version --format '{{.Server.Version}}') ; $(docker info --format '{{.NCPU}} CPU, {{.MemTotal}} octets de mémoire')"
k3d version | head -1
kubectl version --client | head -1
echo "mkcert $(mkcert -version) ; $(openssl version) ; $(curl --version | head -1 | cut -d' ' -f1-4)"
echo "Image k3s ${K3S_IMAGE} ; ${KEYCLOAK_IMAGE} ; ${POSTGRES_IMAGE}"
for port in 80 443; do
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Le port ${port} de l'hôte est déjà utilisé :" >&2
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >&2 || true
    exit 1
  fi
done
echo "Ports 80 et 443 de l'hôte : libres"
FREE_MB=$(docker run --rm "$ALPINE_IMAGE" df -m / | awk 'NR==2 {print $4}')
disk "avant"
if [[ "$FREE_MB" -lt "$MIN_FREE_MB" ]]; then
  echo "Espace disque insuffisant : ${FREE_MB} Mo libres, ${MIN_FREE_MB} Mo requis" >&2
  exit 1
fi

step "1. Certificat mkcert et mots de passe (dossier ${LOCAL}/, ignoré par Git)"
mkdir -p "${LOCAL}/certs" "${LOCAL}/secrets"
chmod 700 "${LOCAL}/secrets"
if [[ -f "${LOCAL}/certs/tls.crt" && -f "${LOCAL}/certs/tls.key" ]]; then
  echo "Certificat existant conservé (non régénéré)."
else
  mkcert -cert-file "${LOCAL}/certs/tls.crt" -key-file "${LOCAL}/certs/tls.key" "*.127.0.0.1.sslip.io"
  chmod 600 "${LOCAL}/certs/tls.key"
fi
(
  umask 077
  python3 - <<'PY'
import secrets

users = ["ADMIN", "ALICE", "BOB", "CHLOE"]
with open(".local/secrets/passwords.env", "w") as f:
    for user in users:
        f.write(f"{user}_PASSWORD={secrets.token_urlsafe(18)}\n")
with open(".local/secrets/db.env", "w") as f:
    f.write(f"POSTGRES_PASSWORD={secrets.token_urlsafe(24)}\n")
    f.write(f"KEYCLOAK_DB_PASSWORD={secrets.token_urlsafe(24)}\n")
with open(".local/secrets/admin.env", "w") as f:
    f.write("username=kcadmin\n")
    f.write(f"password={secrets.token_urlsafe(24)}\n")
PY
)
echo "Mots de passe générés dans ${LOCAL}/secrets/ (4 utilisateurs du realm, PostgreSQL, administrateur initial de Keycloak ; non affichés)."

step "2. Cluster k3d (1 server, 2 agents, ports 80 et 443 publiés ; Traefik de k3s conservé)"
k3d cluster delete "$CLUSTER" >/dev/null 2>&1 || true
k3d cluster create "$CLUSTER" --servers 1 --agents 2 --image "$K3S_IMAGE" \
  -p "80:80@loadbalancer" -p "443:443@loadbalancer" --wait --timeout 600s
$K get nodes -o wide
disk "après la création du cluster"

step "3. Image de l'API de test"
docker build -q -t "$APP_IMAGE" app
# Client de test sur l'hôte : seulement les dépendances (versions de uv.lock) ; le paquet exp est lu
# par PYTHONPATH (le .pth d'une installation éditable est ignoré quand macOS le marque « hidden »).
uv sync --project app --frozen --no-dev --no-install-project
k3d image import "$APP_IMAGE" -c "$CLUSTER"
disk "après l'import de l'image de l'API"

step "4. Traefik : certificat mkcert par défaut et redirection HTTP -> HTTPS"
retry 90 2 $K get crd tlsstores.traefik.io >/dev/null 2>&1
$K -n kube-system create secret tls mkcert-wildcard --cert "${LOCAL}/certs/tls.crt" --key "${LOCAL}/certs/tls.key"
$K apply -f manifests/traefik-config.yaml
# La redirection n'apparaît dans les arguments de Traefik qu'une fois le chart réinstallé par k3s.
retry 120 2 bash -c "$K -n kube-system get deploy traefik -o jsonpath='{.spec.template.spec.containers[0].args}' | grep -q 'redirections'"
$K -n kube-system rollout status deployment/traefik --timeout=300s
echo "--- Arguments de Traefik relatifs à la redirection ---"
$K -n kube-system get deploy traefik -o jsonpath='{.spec.template.spec.containers[0].args}' | tr ',' '\n' | grep -E 'redirections|"--entryPoints.web.address|--entryPoints.websecure.address' | tr -d '[]"'
echo "--- Image de Traefik ---"
$K -n kube-system get deploy traefik -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
disk "après Traefik"

step "5. PostgreSQL : image officielle ${POSTGRES_IMAGE}, StatefulSet d'un réplica, volume local-path"
$K create namespace keycloak
$K -n keycloak create secret generic postgres-credentials --from-env-file="${LOCAL}/secrets/db.env"
$K -n keycloak create secret generic keycloak-admin --from-env-file="${LOCAL}/secrets/admin.env"
$K apply -f manifests/postgres.yaml
$K -n keycloak rollout status statefulset/postgres --timeout=300s || { echo "ÉCHEC : PostgreSQL non prêt après 300 s" >&2; exit 1; }
$K -n keycloak get statefulset,pvc
echo "--- Rôles et bases (superutilisateur) ---"
$K -n keycloak exec postgres-0 -- psql -U postgres -d postgres -At -F ' | ' \
  -c "select rolname, rolsuper, rolcreatedb, rolcreaterole from pg_roles where rolname in ('postgres','keycloak') order by 1" \
  -c "select datname, pg_get_userbyid(datdba) as owner from pg_database where datname='keycloak'"
echo "--- PostgreSQL : version ---"
$K -n keycloak exec postgres-0 -- psql -U postgres -d postgres -At -c "select version()"
disk "après PostgreSQL"

step "6. Keycloak : image officielle ${KEYCLOAK_IMAGE}, start --import-realm"
# Le realm versionné (sans secret) est rendu ici : les marqueurs ${..._PASSWORD} sont remplacés par
# les mots de passe générés, puis le résultat est monté depuis un Secret dans /opt/keycloak/data/import.
python3 - <<'PYEOF'
import os

text = open("realm/collector-realm.json").read()
for user in ("ADMIN", "ALICE", "BOB", "CHLOE"):
    env = dict(line.split("=", 1) for line in open(".local/secrets/passwords.env").read().split())
    text = text.replace("${" + user + "_PASSWORD}", env[user + "_PASSWORD"])
assert "_PASSWORD}" not in text
with open(os.environ["WORK"] + "/collector-realm.json", "w") as f:
    f.write(text)
PYEOF
$K -n keycloak create secret generic keycloak-realm --from-file=collector-realm.json="${WORK}/collector-realm.json"
rm -f "${WORK}/collector-realm.json"
$K apply -f manifests/keycloak.yaml
$K -n keycloak rollout status deployment/keycloak --timeout=600s || { echo "ÉCHEC : Keycloak non prêt après 600 s" >&2; exit 1; }
echo "--- Image de Keycloak ---"
$K -n keycloak get pods -l app=keycloak -o jsonpath='{range .items[*].spec.containers[*]}{.image}{"\n"}{end}'
echo "--- Journal de Keycloak : import du realm ---"
$K -n keycloak logs deploy/keycloak | grep -iE 'import|started in|Listening' | sed -E 's/^[^ ]+ [^ ]+ //' | head -n 8 || true
disk "après Keycloak"
retry 60 3 bash -c "curl -s -o /dev/null -w '%{http_code}' --cacert '${CA_FILE}' https://${KC_HOST}/realms/collector/.well-known/openid-configuration | grep -q 200"
echo "Keycloak répond en HTTPS sur https://${KC_HOST} (realm collector importé)."

step "7. API de test : Deployment, Service, Middleware StripPrefix et Ingress"
$K apply -f manifests/app.yaml
$K -n exp create secret generic exp-users --from-env-file="${LOCAL}/secrets/passwords.env"
$K -n exp rollout status deployment/exp-api --timeout=180s
retry 60 2 bash -c "curl -s -o /dev/null -w '%{http_code}' --cacert '${CA_FILE}' https://${API_HOST}/exp/api/v1/public | grep -q 200"
disk "après l'installation complète"
sleep 60   # laisse Keycloak terminer son initialisation avant le relevé « au repos »
top_all "au repos, 60 s après le démarrage de l'API"

# --- Mesure 1 : TLS --------------------------------------------------------------------------
step "Mesure 1 : TLS (certificat présenté, version négociée, échec sans la CA mkcert)"
for host in "$KC_HOST" "$API_HOST"; do
  echo "--- ${host}:443 ---"
  OUT=$(openssl s_client -connect "${host}:443" -servername "$host" -CAfile "$CA_FILE" -verify_return_error </dev/null 2>&1 || true)
  echo "$OUT" | grep -E 'Protocol *:|Cipher is|Verification|Verify return code' | head -n 4 || true
  # Le sujet et l'émetteur bruts de mkcert contiennent le nom de l'utilisateur et celui de sa machine :
  # seule l'organisation (premier champ O=) est affichée, jamais le CN ni l'OU.
  CERT=$(echo "$OUT" | openssl x509 -noout -subject -issuer -enddate -ext subjectAltName 2>/dev/null)
  echo "  sujet, organisation : $(echo "$CERT" | grep '^subject' | grep -o 'O=[^,]*' | head -n 1)"
  echo "  émetteur, organisation : $(echo "$CERT" | grep '^issuer' | grep -o 'O=[^,]*' | head -n 1)"
  echo "$CERT" | grep -E '^notAfter|DNS:' | sed 's/^ */  /'
  echo "  curl avec la CA mkcert : code HTTP $(curl -s -o /dev/null -w '%{http_code}' --cacert "$CA_FILE" "https://${host}/")"
  # curl de macOS (SecureTransport) consulte aussi le trousseau système, où mkcert -install a mis la CA :
  # même avec --cacert d'un autre bundle, il accepte le certificat. L'échec sans la CA est donc
  # démontré avec httpx (bundle certifi, sans la CA mkcert) et avec openssl.
  echo "  httpx sans la CA mkcert (bundle certifi) : $(HOST="$host" app/.venv/bin/python -c '
import os
import httpx
try:
    httpx.get("https://" + os.environ["HOST"] + "/")
    print("connexion acceptée")
except httpx.ConnectError as error:
    print("échec attendu :", error)
')"
  OUT=$(openssl s_client -connect "${host}:443" -servername "$host" -verify_return_error </dev/null 2>&1 || true)
  echo "  openssl sans la CA mkcert : $(echo "$OUT" | grep -E 'Verify return code|verify error' | head -n 2 | tr '\n' ' ' || true)"
done

# --- Mesure 2 : redirection ------------------------------------------------------------------
step "Mesure 2 : redirection HTTP -> HTTPS"
for url in "http://${KC_HOST}/realms/collector" "http://${API_HOST}/exp/api/v1/public"; do
  echo "GET ${url} -> $(curl -s -o /dev/null -w 'code %{http_code}, Location %{redirect_url}' "$url")"
done

# --- Mesure 3 : matrice d'autorisation -------------------------------------------------------
step "Mesure 3 : matrice d'autorisation (httpx, par https://${API_HOST}/exp, CA mkcert)"
set -a
# shellcheck disable=SC1091
source "${LOCAL}/secrets/passwords.env"
set +a
MATRIX_RC=0
CA_FILE="$CA_FILE" PYTHONPATH=app/src app/.venv/bin/python -m exp.client matrix || MATRIX_RC=$?
echo "--- Journal de l'API : rejets (reason n'est jamais renvoyé au client) ---"
LOGS=$($K -n exp logs deploy/exp-api | grep '"auth_rejected"' || true) python3 - <<'PYEOF'
import json
import os

for line in os.environ["LOGS"].splitlines():
    d = json.loads(line)
    print(f"{d.get('correlation_id', '-'):<16} statut {d['status']}  reason={d['reason']}  {d['path']}")
PYEOF
echo "Code de sortie de la matrice : ${MATRIX_RC}"

# --- Mesure 4 : iss --------------------------------------------------------------------------
step "Mesure 4 : iss d'un jeton obtenu par l'URL interne (Job dans le cluster)"
$K -n exp delete job iss-internal --ignore-not-found >/dev/null
sed -e "s|__NAME__|iss-internal|" \
  -e 's|__COMMAND__|["python","-m","exp.client","iss-internal"]|' manifests/job.yaml.tmpl | $K apply -f - >/dev/null
$K -n exp wait --for=condition=complete job/iss-internal --timeout=120s >/dev/null || true
$K -n exp logs job/iss-internal
$K -n exp wait --for=condition=complete job/iss-internal --timeout=5s >/dev/null

# --- Mesure 5 : JWKS -------------------------------------------------------------------------
step "Mesure 5 : récupération et cache des clés JWKS (${BURST} requêtes supplémentaires, un même jeton)"
BEFORE=$($K -n exp logs deploy/exp-api | grep -c '"event": "jwks_fetch"' || true)
CA_FILE="$CA_FILE" PYTHONPATH=app/src app/.venv/bin/python -m exp.client burst "$BURST"
AFTER=$($K -n exp logs deploy/exp-api | grep -c '"event": "jwks_fetch"' || true)
REQUESTS=$($K -n exp logs deploy/exp-api | grep -c '"event": "request"' || true)
echo "Appels JWKS avant le lot : ${BEFORE} ; après : ${AFTER}"
echo "Requêtes HTTP journalisées par l'API depuis son démarrage : ${REQUESTS}"
echo "--- Lignes jwks_fetch du journal de l'API ---"
$K -n exp logs deploy/exp-api | grep '"event": "jwks_fetch"'

# --- Mesure 6 : ressources -------------------------------------------------------------------
step "Mesure 6 : ressources"
sleep 20
top_all "après les mesures"
echo "--- kubectl top nodes ---"
$K top nodes || true
disk "fin des mesures"
echo "--- Secrets : aucun mot de passe dans le dépôt ---"
git check-ignore -v "${LOCAL}/certs/tls.key" "${LOCAL}/secrets/passwords.env" || true
[[ "$MATRIX_RC" -eq 0 ]] || { echo "La matrice d'autorisation comporte des écarts" >&2; exit 1; }
