#!/usr/bin/env bash
# Audit de sécurité reproductible du POC sur le cluster k3d (phase 9, critère 8).
#
#   docs/06-securite/scans/run-scans.sh            tout (environ 40 minutes)
#   docs/06-securite/scans/run-scans.sh trivy sonar npm    seulement ces étapes
#                                                   (étapes : trivy sonar npm zap)
#
# Ce que fait le script, dans l'ordre :
#   1. vérifie le cluster (smoke.sh) et les outils, lit alice et les mots de passe dans
#      deploy/local/.env : jamais affichés, jamais en argument de commande ;
#   2. note les versions et les digests (environnement.txt) ;
#   3. Trivy 0.76.0 : binaire officiel de la release, somme SHA-256 vérifiée, dans un dossier
#      temporaire hors du dépôt ; images déployées en amd64 ET arm64, toutes sévérités, SANS
#      --ignore-unfixed (la CI, elle, l'utilise) ; configuration du dépôt et chart Helm rendu ;
#   4. SonarCloud (API publique en lecture) et npm audit complet du front ;
#   5. OWASP ZAP (image officielle épinglée par digest) : scan passif du front et de la page de
#      connexion de Keycloak ; scan ACTIF de l'API (catalog puis notification), sans jeton, puis
#      authentifié (alice) ;
#   6. masque dans tout ce qui est archivé les jetons, le nom de la machine et le dossier personnel,
#      puis vérifie les compteurs (jetons, mots de passe, nom de la machine, dossier personnel : 0) ;
#   7. produit resume.md (synthèse chiffrée) et rejoue smoke.sh.
#
# Périmètre, strictement : le scan actif ne vise QUE api.127.0.0.1.sslip.io (le POC local). Le front
# (app.) et Keycloak (auth.) sont analysés en passif : Keycloak est un produit tiers et un scan actif
# pourrait verrouiller les comptes de démonstration. Aucun autre hôte, jamais. Sur le cluster, le
# script ne fait que du trafic HTTP et des lectures (kubectl get) ; le scan actif crée des données
# de démonstration (catégories, boutiques, articles), c'est accepté.
#
# Comment le conteneur ZAP joint le cluster : les noms *.127.0.0.1.sslip.io pointent vers 127.0.0.1,
# qui désigne le conteneur lui-même. `--add-host <nom>:host-gateway` les fait résoudre vers l'hôte
# Docker (le Mac), où k3d publie le port 443 de Traefik. Le certificat est celui de mkcert : une
# copie du magasin de confiance Java de l'image, additionnée de l'autorité de mkcert (clé publique
# seulement), est montée dans le conteneur ; la vérification TLS reste active.
#
# Comment le jeton passe à ZAP : pkce_login.py obtient les jetons d'alice par le vrai flux PKCE ;
# run-scans.sh les garde dans des variables du shell et les donne au conteneur par `-e VARIABLE`
# sans valeur sur la ligne de commande. zap_hook.py pose l'en-tête Authorization dans ZAP et le
# renouvelle toutes les 150 s (le jeton d'accès dure 5 minutes, un scan actif plus longtemps).
#
# Compatible bash 3.2 (macOS). Code de sortie : 0 même si des constats existent (l'audit constate,
# il ne bloque pas) ; autre code : l'audit n'a pas pu se dérouler ou une fuite de secret a été vue.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${HERE}/../../.." && pwd)"
ENV_FILE="${ROOT}/deploy/local/.env"
CTX="k3d-collector"
K="kubectl --context ${CTX} -n collector"
API_HOST="api.127.0.0.1.sslip.io"
APP_HOST="app.127.0.0.1.sslip.io"
AUTH_HOST="auth.127.0.0.1.sslip.io"

# Image officielle de ZAP, version stable publiée depuis plus de 14 jours, épinglée par digest
# (index multi-architecture ; tag zaproxy/zap-stable:20261026, ZAP 2.17.0).
ZAP_IMAGE="zaproxy/zap-stable@sha256:030d3df57735dacbb83464854758e674dd9ad01d79d12a129a8e58b1fd384238"
# Trivy : même version et même somme que .github/workflows/backend.yml (archive Linux). Pour le Mac,
# l'archive macOS est vérifiée avec le fichier de sommes de la release, dont on contrôle d'abord
# qu'il contient bien la somme de l'archive Linux épinglée dans la CI (preuve qu'il est authentique).
TRIVY_VERSION="$(grep -E '^  TRIVY_VERSION:' "${ROOT}/.github/workflows/backend.yml" | sed -E 's/.*"([^"]+)".*/\1/')"
TRIVY_LINUX_SHA256="$(grep -E '^  TRIVY_SHA256:' "${ROOT}/.github/workflows/backend.yml" | awk '{print $2}')"
ZAP_MAX_SCAN_MINUTES="${ZAP_MAX_SCAN_MINUTES:-12}"   # durée maximale du scan actif d'une passe

STAGES=("$@")
[[ ${#STAGES[@]} -gt 0 ]] || STAGES=(trivy sonar npm zap)
want() { local s; for s in "${STAGES[@]}"; do [[ "$s" == "$1" ]] && return 0; done; return 1; }

[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env introuvable : le cluster a-t-il été déployé ?" >&2; exit 1; }
for tool in docker kubectl helm curl uv mkcert npm perl python3 shasum tar; do
  command -v "$tool" >/dev/null || { echo "${tool} est requis." >&2; exit 1; }
done

# Valeur d'une clé du .env, jamais affichée.
read_var() {
  grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | grep . \
    || { echo "Clé $1 absente ou vide dans deploy/local/.env." >&2; return 1; }
}

echo "== Vérification préalable : le cluster est sain (smoke.sh)"
"${ROOT}/deploy/local/smoke.sh" >/dev/null 2>&1 \
  || { echo "smoke.sh échoue : cluster non sain, audit interrompu." >&2; exit 1; }

RUN_ID="$(date +%Y%m%d-%H%M)"
RESULTS="${HERE}/resultats/${RUN_ID}"
[[ ! -e "$RESULTS" ]] || { echo "${RESULTS} existe déjà (attendre une minute)." >&2; exit 1; }
mkdir -p "$RESULTS"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/collector-audit.XXXXXX")"
chmod 700 "$WORK"
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT
CAROOT_PEM="$(mkcert -CAROOT)/rootCA.pem"
[[ -f "$CAROOT_PEM" ]] || { echo "Autorité mkcert introuvable (mkcert -install fait ?)." >&2; exit 1; }
export REQUESTS_CA_BUNDLE="$CAROOT_PEM"

# Image déployée (tag@digest), lue sur le cluster : on audite ce qui tourne, pas ce qu'on croit.
deployed_image() { $K get deploy "$1" -o jsonpath='{.spec.template.spec.containers[0].image}'; }
IMG_CATALOG="$(deployed_image catalog-service)"
IMG_NOTIFICATION="$(deployed_image notification-service)"
IMG_FRONTEND="$(deployed_image frontend)"

pods_state() { $K get pods --no-headers -o custom-columns=NOM:.metadata.name,PRET:.status.containerStatuses[0].ready,REDEMARRAGES:.status.containerStatuses[0].restartCount | sort; }
pods_state > "${RESULTS}/pods-avant.txt"
$K get hpa --no-headers > "${RESULTS}/hpa-avant.txt"

echo "== Environnement et versions"
{
  echo "Date de début : $(date '+%d/%m/%Y %H:%M:%S')"
  echo "Commit du dépôt : $(git -C "$ROOT" rev-parse --short HEAD)"
  echo "Docker : $(docker version --format '{{.Server.Version}}')"
  echo "Image ZAP : ${ZAP_IMAGE}"
  echo "Cible active : https://${API_HOST} ; passif : https://${APP_HOST} et https://${AUTH_HOST}"
  echo
  echo "Images déployées (lues sur le cluster) :"
  echo "  ${IMG_CATALOG}"
  echo "  ${IMG_NOTIFICATION}"
  echo "  ${IMG_FRONTEND}"
  echo
  echo "Digests lus sur les pods :"
  $K get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].imageID}{"\n"}{end}' \
    | grep -E '^(catalog-service|notification-service|frontend)-' | sed 's/^/  /'
  echo
  echo "Node : $(node --version 2>/dev/null || echo absent) ; npm : $(npm --version)"
} > "${RESULTS}/environnement.txt"

# ---------------------------------------------------------------------------------------------
# Trivy
# ---------------------------------------------------------------------------------------------
trivy_install() {
  local arch base archive
  arch="$(uname -m)"
  case "$arch" in arm64) archive="trivy_${TRIVY_VERSION}_macOS-ARM64.tar.gz" ;; \
                  x86_64) archive="trivy_${TRIVY_VERSION}_macOS-64bit.tar.gz" ;; \
                  *) echo "Architecture ${arch} non prévue." >&2; return 1 ;; esac
  base="https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}"
  mkdir -p "${WORK}/trivy-dl" "${WORK}/trivy-bin"
  curl -fsSL --retry 3 -o "${WORK}/trivy-dl/sums.txt" "${base}/trivy_${TRIVY_VERSION}_checksums.txt"
  curl -fsSL --retry 3 -o "${WORK}/trivy-dl/${archive}" "${base}/${archive}"
  # 1. le fichier de sommes est authentique : il contient la somme Linux épinglée dans la CI ;
  grep -q "^${TRIVY_LINUX_SHA256}  trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz$" "${WORK}/trivy-dl/sums.txt" \
    || { echo "Le fichier de sommes de Trivy ne contient pas la somme épinglée dans la CI." >&2; return 1; }
  # 2. l'archive du Mac correspond à sa somme.
  ( cd "${WORK}/trivy-dl" && grep " ${archive}\$" sums.txt | shasum -a 256 --check --strict - >/dev/null ) \
    || { echo "Somme SHA-256 de ${archive} incorrecte." >&2; return 1; }
  tar -xzf "${WORK}/trivy-dl/${archive}" -C "${WORK}/trivy-bin" trivy
  TRIVY="${WORK}/trivy-bin/trivy"
  export TRIVY_CACHE_DIR="${WORK}/trivy-cache"
  echo "Trivy $("$TRIVY" --version | head -1 | sed 's/Version: //') (archive ${archive}, SHA-256 vérifiée)" \
    | tee -a "${RESULTS}/environnement.txt"
}

trivy_images() {
  local name ref arch out
  for name in catalog-service notification-service frontend; do
    case "$name" in
      catalog-service) ref="$IMG_CATALOG" ;;
      notification-service) ref="$IMG_NOTIFICATION" ;;
      frontend) ref="$IMG_FRONTEND" ;;
    esac
    for arch in amd64 arm64; do
      out="${RESULTS}/trivy-${name}-${arch}"
      echo "-- Trivy ${name} (${arch})"
      # --image-src remote : lit l'image sur GHCR, sans rien tirer dans Docker.
      "$TRIVY" image --image-src remote --platform "linux/${arch}" --scanners vuln,secret \
        --severity UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL --quiet \
        --format json --output "${out}.json" "$ref"
      "$TRIVY" convert --format table --output "${out}.txt" "${out}.json"
    done
  done
}

trivy_config() {
  local out
  # Chart Helm rendu avec les mêmes values que deploy.sh (digest fictif : seul le gabarit compte).
  mkdir -p "${WORK}/rendered"
  local svc
  for svc in catalog-service notification-service frontend; do
    helm template "$svc" "${ROOT}/deploy/helm/collector-service" -f "${ROOT}/deploy/helm/values/${svc}.yaml" \
      --set image.tag=audit --set "image.digest=sha256:$(printf '0%.0s' $(seq 1 64))" \
      --set serviceMonitor.enabled=true > "${WORK}/rendered/${svc}.yaml"
  done
  echo "-- Trivy config : manifestes de deploy/"
  "$TRIVY" config --quiet --format json --output "${RESULTS}/trivy-config-deploy.json" "${ROOT}/deploy"
  echo "-- Trivy config : Dockerfiles des services et du front"
  "$TRIVY" config --quiet --skip-dirs "${ROOT}/frontend/node_modules" --skip-dirs "${ROOT}/frontend/dist" \
    --format json --output "${RESULTS}/trivy-config-dockerfiles.json" "${ROOT}/services" 
  "$TRIVY" config --quiet --skip-dirs "${ROOT}/frontend/node_modules" --skip-dirs "${ROOT}/frontend/dist" \
    --skip-dirs "${ROOT}/frontend/test-results" --skip-dirs "${ROOT}/frontend/e2e" \
    --format json --output "${RESULTS}/trivy-config-frontend.json" "${ROOT}/frontend"
  echo "-- Trivy config : chart Helm rendu"
  "$TRIVY" config --quiet --format json --output "${RESULTS}/trivy-config-helm-rendu.json" "${WORK}/rendered"
  for out in deploy dockerfiles frontend helm-rendu; do
    "$TRIVY" convert --format table --output "${RESULTS}/trivy-config-${out}.txt" "${RESULTS}/trivy-config-${out}.json"
  done
}

# ---------------------------------------------------------------------------------------------
# SonarCloud (API publique, sans jeton) et npm audit
# ---------------------------------------------------------------------------------------------
sonar_extract() {
  local svc key
  for svc in catalog-service notification-service; do
    key="Luucaaas_collector-poc_${svc}"
    echo "-- SonarCloud ${svc}"
    curl -fsS "https://sonarcloud.io/api/issues/search?componentKeys=${key}&resolved=false&ps=500" \
      -o "${RESULTS}/sonar-${svc}-issues.json"
    curl -fsS "https://sonarcloud.io/api/hotspots/search?projectKey=${key}&ps=500" \
      -o "${RESULTS}/sonar-${svc}-hotspots.json"
    curl -fsS "https://sonarcloud.io/api/qualitygates/project_status?projectKey=${key}" \
      -o "${RESULTS}/sonar-${svc}-quality-gate.json"
  done
}

npm_audit() {
  echo "-- npm audit (dépendances de développement comprises, puis embarquées seulement)"
  ( cd "${ROOT}/frontend"
    npm audit --json > "${RESULTS}/npm-audit-complet.json" || true
    npm audit --omit=dev --json > "${RESULTS}/npm-audit-prod.json" || true )
}

# ---------------------------------------------------------------------------------------------
# ZAP
# ---------------------------------------------------------------------------------------------
# Ressources du conteneur plafonnées : un premier essai du scan actif complet, sans plafond, avait
# pris 430 % de CPU et 4,8 Gio sur les 7,75 Gio de la machine virtuelle de Docker Desktop, qui sert
# aussi le cluster : PostgreSQL, Keycloak et d'autres pods avaient redémarré en boucle pendant
# trois minutes (retour à la normale sans intervention, mais le scan avait été interrompu).
# 2 CPU, 2 Gio de mémoire pour le conteneur, tas Java limité à 1 Gio (-Xmx1g, lu par zap.sh).
ZAP_LIMITS=(--memory 2g --memory-swap 2g --cpus 2)
ZAP_JVM="-Xmx1g"
ZAP_COMMON=(--rm "${ZAP_LIMITS[@]}" --add-host "${API_HOST}:host-gateway" --add-host "${APP_HOST}:host-gateway"
            --add-host "${AUTH_HOST}:host-gateway" -v "${WORK}/ts:/ts:ro" -v "${WORK}/wrk:/zap/wrk:rw"
            -e "JAVA_TOOL_OPTIONS=-Djavax.net.ssl.trustStore=/ts/cacerts -Djavax.net.ssl.trustStorePassword=changeit")

zap_setup() {
  mkdir -p "${WORK}/ts" "${WORK}/wrk"
  chmod 777 "${WORK}/wrk"   # l'utilisateur `zap` du conteneur (uid 1000) doit pouvoir y écrire
  docker image inspect "$ZAP_IMAGE" >/dev/null 2>&1 || docker pull --quiet "$ZAP_IMAGE" >/dev/null
  cp "$CAROOT_PEM" "${WORK}/ts/rootCA.pem"
  cp "${HERE}/zap_hook.py" "${WORK}/ts/zap_hook.py"
  # Fichier de configuration de zap-api-scan.py : dès qu'il est fourni et non vide, ZAP abandonne sa
  # politique « API-Minimal » (quelques règles) et active TOUTES les règles de la politique par défaut
  # (injections, XSS, traversée de chemin, etc.). Une ligne suffit : une règle passive laissée à WARN.
  # La règle 40026 (XSS basé sur le DOM) est désactivée : elle lance un navigateur Firefox dans le
  # conteneur, inutile sur une API JSON, et il épuisait la mémoire du conteneur (ZAP tué en cours de
  # scan, sans rapport : constaté lors des deux premiers essais).
  printf '10020\tWARN\t(Anti-clickjacking, règle passive laissée à WARN)\n40026\tIGNORE\t(XSS DOM, navigateur)\n' > "${WORK}/ts/api-scan.conf"
  # Magasin de confiance : copie de celui de l'image + autorité de mkcert (public).
  docker run --rm -v "${WORK}/ts:/ts" --entrypoint sh "$ZAP_IMAGE" -c \
    'cp "$(readlink -f /etc/ssl/certs/java/cacerts)" /ts/cacerts &&
     keytool -importcert -noprompt -alias mkcert -file /ts/rootCA.pem -keystore /ts/cacerts -storepass changeit >/dev/null' \
    || { echo "Magasin de confiance de ZAP non créé." >&2; return 1; }
  chmod 644 "${WORK}/ts/"*
  docker run --rm --entrypoint sh "$ZAP_IMAGE" -c 'ls /zap/zap-*.jar | head -1' > "${WORK}/zap-version.txt"
  echo "ZAP : $(cat "${WORK}/zap-version.txt" | sed 's#/zap/##') ; image ${ZAP_IMAGE}" >> "${RESULTS}/environnement.txt"
}

ZAP_FAILED=0
zap_collect() { # range les rapports d'une passe (zap-<nom>.html, .json, .md) dans les résultats
  local f
  for f in "${WORK}/wrk/zap-$1".*; do [[ -f "$f" ]] && mv "$f" "${RESULTS}/"; done
  # Pas de rapport JSON : ZAP a été tué ou a échoué ; on ne laisse pas passer cela sous silence.
  if [[ ! -s "${RESULTS}/zap-$1.json" ]]; then
    echo "ATTENTION : la passe ZAP « $1 » n'a produit aucun rapport (voir zap-$1.log)." >&2
    ZAP_FAILED=1
  fi
  return 0
}

# Scan passif : spider d'une minute, aucune attaque (zap-baseline.py). `spider.postform=false` : le
# spider ne soumet aucun formulaire (deux premiers essais avaient envoyé le formulaire de connexion
# de Keycloak, vide : une tentative d'authentification n'est pas du « passif »). `--autooff` est
# nécessaire : avec le mode par défaut (Automation Framework), ZAP ignore cette option ; vérifié sur
# un serveur local jetable qui compte les requêtes POST (2 POST sans --autooff, 0 avec).
zap_passive() {
  local name="$1" url="$2" t0=$SECONDS
  echo "-- ZAP passif : ${name} (${url%%\?*})"
  docker run "${ZAP_COMMON[@]}" --name "collector-audit-zap-${name}" "$ZAP_IMAGE" zap-baseline.py -t "$url" -m 1 -I --autooff \
    -z "${ZAP_JVM} -config spider.postform=false" \
    -r "zap-${name}.html" -J "zap-${name}.json" -w "zap-${name}.md" > "${RESULTS}/zap-${name}.log" 2>&1 || true
  echo "${name} : $((SECONDS - t0)) s" >> "${RESULTS}/zap-durees.txt"
  zap_collect "$name"
}

# Spécification OpenAPI d'un service, complétée par l'URL publique (le champ `servers` est absent :
# les routes sont /api/v1/... derrière le préfixe /catalog ou /notification de Traefik).
zap_spec() {
  local svc="$1" prefix="$2"
  curl -fsS --cacert "$CAROOT_PEM" "https://${API_HOST}/${prefix}/api/v1/openapi.json" \
    | python3 -c "
import json, sys
spec = json.load(sys.stdin)
spec['servers'] = [{'url': 'https://${API_HOST}/${prefix}'}]
json.dump(spec, open('${WORK}/wrk/${svc}-openapi.json', 'w'))"
}

# Scan actif de l'API d'un service (zap-api-scan.py, politique par défaut de ZAP, toutes règles).
# $1 : nom de la passe ; $2 : service ; $3 : "anonyme" ou "alice".
zap_api() {
  local name="$1" svc="$2" mode="$3" tokens access refresh t0=$SECONDS
  echo "-- ZAP actif : ${name} (${mode}, ${ZAP_MAX_SCAN_MINUTES} min au plus)"
  if [[ "$mode" == "alice" ]]; then
    # Les jetons restent dans des variables du shell ; le mot de passe n'est donné qu'à la commande.
    tokens="$(SCAN_USER=alice SCAN_PASSWORD="$ALICE_PW" \
      uv run --quiet --project "${ROOT}/tests/load" python "${HERE}/pkce_login.py")" \
      || { echo "Connexion d'alice impossible." >&2; return 1; }
    access="$(printf '%s\n' "$tokens" | sed -n 1p)"
    refresh="$(printf '%s\n' "$tokens" | sed -n 2p)"
    tokens=""
    ZAP_ACCESS_TOKEN="$access" ZAP_REFRESH_TOKEN="$refresh" \
    docker run "${ZAP_COMMON[@]}" --name "collector-audit-zap-${name}" -e ZAP_ACCESS_TOKEN -e ZAP_REFRESH_TOKEN "$ZAP_IMAGE" zap-api-scan.py \
      -t "/zap/wrk/${svc}-openapi.json" -f openapi --hook /ts/zap_hook.py -c /ts/api-scan.conf -I -T 10 \
      -z "${ZAP_JVM} -config scanner.maxScanDurationInMins=${ZAP_MAX_SCAN_MINUTES}" \
      -r "zap-${name}.html" -J "zap-${name}.json" -w "zap-${name}.md" > "${RESULTS}/zap-${name}.log" 2>&1 || true
    access=""; refresh=""
  else
    docker run "${ZAP_COMMON[@]}" --name "collector-audit-zap-${name}" "$ZAP_IMAGE" zap-api-scan.py \
      -t "/zap/wrk/${svc}-openapi.json" -f openapi --hook /ts/zap_hook.py -c /ts/api-scan.conf -I -T 10 \
      -z "${ZAP_JVM} -config scanner.maxScanDurationInMins=${ZAP_MAX_SCAN_MINUTES}" \
      -r "zap-${name}.html" -J "zap-${name}.json" -w "zap-${name}.md" > "${RESULTS}/zap-${name}.log" 2>&1 || true
  fi
  echo "${name} : $((SECONDS - t0)) s" >> "${RESULTS}/zap-durees.txt"
  zap_collect "$name"
}

# ---------------------------------------------------------------------------------------------
# Archivage : masquage et compteurs
# ---------------------------------------------------------------------------------------------
sanitize() {
  local short file
  short="$(hostname -s)"
  for file in "${RESULTS}"/*; do
    [[ -f "$file" ]] || continue
    # jetons (trois segments base64url dont le premier commence par l'en-tête JWT), nom de la machine
    # (long et court, sans tenir compte de la casse) et dossier personnel.
    HOST_SHORT="$short" perl -pi -e \
      's/ey[J]\w[\w-]*(?:\.[\w-]+){0,2}/<jeton-masqué>/g; s/\Q$ENV{HOST_SHORT}\E(?:\.[\w-]+)*/<machine>/gi; s{/Us[e]rs/[^\/\s"\x27]+}{<home>}g' "$file"
  done
}

# Compte les occurrences de ce qui ne doit jamais être archivé. Affiche des nombres, jamais de valeur.
count_leaks() {
  local dir="$1" jwt home host patterns n_jwt n_home n_host n_pw
  jwt="ey$(printf 'J')"; home="/Us$(printf 'e')rs"; host="$(hostname -s)"
  patterns="${WORK}/patterns"; : > "$patterns"; chmod 600 "$patterns"
  # Mots de passe et secrets du .env (valeurs d'au moins 8 caractères), donnés à grep par fichier.
  { grep -E '^[A-Z_]*(PASSWORD|SECRET|TOKEN|KEY)[A-Z_]*=' "$ENV_FILE" | cut -d= -f2- | awk 'length($0) >= 8'; } >> "$patterns" || true
  n_pw="$(grep -rIlF -f "$patterns" "$dir" 2>/dev/null | wc -l | tr -d ' ')"
  n_jwt="$(grep -rIF -- "$jwt" "$dir" 2>/dev/null | wc -l | tr -d ' ')"
  n_host="$(grep -rIiF -- "$host" "$dir" 2>/dev/null | wc -l | tr -d ' ')"
  n_home="$(grep -rIF -- "$home" "$dir" 2>/dev/null | wc -l | tr -d ' ')"
  echo "  ${dir#"${ROOT}/"}"
  echo "    jetons (${jwt}) : ${n_jwt} ; fichiers contenant un mot de passe du .env : ${n_pw}"
  echo "    nom de la machine : ${n_host} ; dossier personnel (${home}) : ${n_home}"
  [[ "${n_jwt}${n_pw}${n_host}${n_home}" == "0000" ]]
}

# ---------------------------------------------------------------------------------------------
# Déroulement
# ---------------------------------------------------------------------------------------------
if want trivy; then
  echo "== Trivy"
  trivy_install
  trivy_images
  trivy_config
  # Version de la base de vulnérabilités (connue seulement une fois la base téléchargée).
  { echo "Base de vulnérabilités de Trivy :"; "$TRIVY" --version | sed -n '2,$p' | sed 's/^/  /'; } >> "${RESULTS}/environnement.txt"
fi
if want sonar; then echo "== SonarCloud"; sonar_extract; fi
if want npm; then echo "== npm audit"; npm_audit; fi

if want zap; then
  echo "== OWASP ZAP"
  ALICE_PW="$(read_var ALICE_PASSWORD)"
  zap_setup
  zap_passive front "https://${APP_HOST}/"
  # Page de connexion publique de Keycloak (PKCE factice : la page s'affiche, rien n'est soumis).
  zap_passive keycloak "https://${AUTH_HOST}/realms/collector/protocol/openid-connect/auth?client_id=collector-web&response_type=code&scope=openid&redirect_uri=https%3A%2F%2F${APP_HOST}%2F&state=audit&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256"
  zap_spec catalog catalog
  zap_spec notification notification
  zap_api api-catalog-anonyme catalog anonyme
  zap_api api-notification-anonyme notification anonyme
  zap_api api-catalog-alice catalog alice
  zap_api api-notification-alice notification alice
  ALICE_PW=""
fi

echo "== Synthèse, puis masquage de ce qui est archivé"
python3 "${HERE}/summarize.py" "$RESULTS" > "${RESULTS}/resume.md"
sanitize
echo "== Compteurs (attendus : 0 partout)"
leaks_ok=1
count_leaks "$RESULTS" || leaks_ok=0
count_leaks "$HERE" || leaks_ok=0

pods_state > "${RESULTS}/pods-apres.txt"
$K get hpa --no-headers > "${RESULTS}/hpa-apres.txt"
echo "== Cluster intact ?"
echo "Redémarrages de conteneurs : $(awk '{n += $3} END {print n + 0}' "${RESULTS}/pods-avant.txt") avant, $(awk '{n += $3} END {print n + 0}' "${RESULTS}/pods-apres.txt") après (pods-*.txt, hpa-*.txt)"
"${ROOT}/deploy/local/smoke.sh" 2>&1 | tail -2
echo
echo "Résultats : ${RESULTS}"
[[ $ZAP_FAILED -eq 0 ]] || { echo "ATTENTION : au moins une passe ZAP n'a pas abouti." >&2; exit 3; }
[[ $leaks_ok -eq 1 ]] || { echo "ATTENTION : un secret, le nom de la machine ou le dossier personnel figure dans les résultats." >&2; exit 2; }
exit 0
