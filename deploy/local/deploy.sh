#!/usr/bin/env bash
# Déploiement sur le cluster k3d `collector`.
#
# Usage : deploy/local/deploy.sh infra | realm | monitoring | services <tag> | all <tag>
#   infra : génère les mots de passe manquants dans deploy/local/.env, crée ou met à jour les
#           Secrets et ConfigMaps, applique les manifestes de deploy/infra (PostgreSQL, RabbitMQ,
#           Keycloak + Ingress `auth.`) et attend que tout soit prêt. Relançable sans effet de bord.
#   realm : applique le realm Keycloak (deploy/keycloak/collector-realm.json) à un cluster existant.
#           `start --import-realm` ignore un realm déjà présent : la commande arrête Keycloak,
#           recrée sa base PostgreSQL (tout ce qu'elle contient revient au JSON et au Secret keycloak-admin :
#           sessions, et toute modification faite à la main dans la console), le redémarre et attend
#           la configuration OpenID. Jamais lancée par `infra` ni `all`. Voir deploy/README.md.
#   services <tag> : déploie catalog-service, notification-service et le front (frontend) depuis
#           les images publiées par la CI (ghcr.io/luucaaas/<composant>:<tag>, ex. sha-bec38ed)
#           avec le chart Helm deploy/helm/collector-service. Refuse un tag absent de GHCR pour
#           l'un des trois avant tout changement ; attend les pods, lance smoke.sh ; en cas
#           d'échec, revient à la révision précédente (`helm rollback`) et sort en erreur.
#   monitoring : installe kube-prometheus-stack allégé (Prometheus, opérateur, Grafana,
#           kube-state-metrics) dans le namespace `collector`, charge le tableau de bord, expose
#           Grafana en HTTPS (https://grafana.127.0.0.1.sslip.io). Mot de passe administrateur
#           généré dans .env. Active le ServiceMonitor des services déjà déployés. Relançable.
#   all <tag> : `infra`, `monitoring` puis `services <tag>` (le CRD ServiceMonitor existe ainsi
#           avant que le chart des services en crée un).
#
# Variable facultative : DEPLOY_VALUES=<fichier de values Helm> est ajouté (`-f`) après les values
# de chaque composant (services et front), pour `services` et `all`. Sert à déployer une configuration volontairement
# défaillante et à démontrer le retour arrière (ex. limite de mémoire trop basse), sans modifier le script.
set -euo pipefail

CLUSTER="collector"
CTX="k3d-${CLUSTER}"
NS="collector"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "${HERE}/../.." && pwd)"
INFRA_DIR="${REPO}/deploy/infra"
COMPOSE_DIR="${REPO}/deploy/compose"
ENV_FILE="${HERE}/.env"
K="kubectl --context ${CTX} -n ${NS}"
H="helm --kube-context ${CTX} -n ${NS}"
CHART_DIR="${REPO}/deploy/helm/collector-service"
VALUES_DIR="${REPO}/deploy/helm/values"
REGISTRY="ghcr.io/luucaaas"
# Services FastAPI (Secrets, ServiceMonitor) et composants déployés par le chart (services + front).
SERVICES=(catalog-service notification-service)
COMPONENTS=(catalog-service notification-service frontend)
# Pile d'observabilité : version du chart fixée (expérimentation 3), valeurs dans deploy/infra/monitoring.
STACK_CHART="oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack"
STACK_VERSION="91.9.0"
MON_DIR="${INFRA_DIR}/monitoring"
digest=()   # digests des images (rempli par check_images)
tmp=""   # dossier temporaire des fichiers contenant des mots de passe (créé par ensure_tmp)

step() { printf '\n=== %s ===\n' "$*"; }

check_prerequisites() {
  for tool in kubectl python3 openssl curl; do
    command -v "$tool" >/dev/null || { echo "Outil manquant : $tool" >&2; exit 1; }
  done
  kubectl --context "$CTX" get namespace "$NS" >/dev/null 2>&1 \
    || { echo "Cluster ${CLUSTER} absent ou sans namespace ${NS} : lancer 'deploy/local/cluster.sh create'." >&2; exit 1; }
}

# Ajoute au .env chaque variable du modèle qui y manque (ou y est vide), avec un mot de passe
# aléatoire. base64 de 18 octets = 24 caractères ; '+' et '/' remplacés pour rester utilisables
# dans une URL. Rien n'est affiché : seuls les noms des variables créées le sont.
generate_env() {
  step "Mots de passe (deploy/local/.env)"
  if [[ ! -f "$ENV_FILE" ]]; then
    ( umask 077 && : > "$ENV_FILE" )
  fi
  chmod 600 "$ENV_FILE"
  local created=() line key
  while IFS= read -r line; do
    [[ "$line" == *=change-me ]] || continue
    key="${line%%=*}"
    if ! grep -q "^${key}=." "$ENV_FILE"; then
      # Clé présente mais vide (« KEY= ») : on retire la ligne pour ne pas la dupliquer.
      if grep -q "^${key}=$" "$ENV_FILE"; then
        ( umask 077 && grep -v "^${key}=$" "$ENV_FILE" > "${ENV_FILE}.tmp" || true )
        mv "${ENV_FILE}.tmp" "$ENV_FILE"
      fi
      printf '%s=%s\n' "$key" "$(openssl rand -base64 18 | tr '+/' '-_')" >> "$ENV_FILE"
      created+=("$key")
    fi
  done < "${HERE}/.env.example"
  if [[ ${#created[@]} -gt 0 ]]; then
    echo "Générés : ${created[*]}"
  else
    echo "Tous présents : mots de passe inchangés."
  fi
}

# Écrit la valeur d'une variable du .env dans un fichier du dossier temporaire (600). Les mots de
# passe passent ainsi à kubectl par fichier (--from-file), jamais en argument de commande, où `ps`
# les montrerait. Appelée directement (pas dans « $(…) ») : son `exit 1` arrête bien le script si
# la valeur est absente ou vide, on ne crée donc jamais un Secret avec un mot de passe vide.
write_value() {
  local key="$1" value
  value="$(grep "^${key}=" "$ENV_FILE" | head -n 1 | cut -d= -f2- || true)"
  if [[ -z "$value" ]]; then
    echo "Variable ${key} absente ou vide dans ${ENV_FILE}." >&2
    exit 1
  fi
  ( umask 077 && printf '%s' "$value" > "${tmp}/${key}" )
}

# Applique un objet généré à sec : `create … --dry-run=client -o yaml | apply` rend la commande
# relançable (créé la première fois, mis à jour ensuite).
apply_generated() { $K "$@" --dry-run=client -o yaml | $K apply -f - >/dev/null; }

# Pour les Secrets : `apply` côté client recopierait leurs données (mots de passe en base64) dans
# l'annotation last-applied-configuration. L'application côté serveur n'en écrit pas ; on retire
# aussi l'annotation d'un Secret créé par une version précédente du script.
apply_secret() {
  local name="$4"   # arguments : create secret generic <nom> …
  $K "$@" --dry-run=client -o yaml | $K apply --server-side --force-conflicts -f - >/dev/null
  $K annotate secret "$name" kubectl.kubernetes.io/last-applied-configuration- >/dev/null
}

# Crée (une seule fois par exécution) le dossier temporaire 700 des fichiers contenant des mots de
# passe. Variable globale : le trap EXIT s'exécute après le retour des fonctions ; les fichiers
# sont toujours supprimés à la sortie du script.
ensure_tmp() {
  [[ -z "$tmp" ]] || return 0
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  chmod 700 "$tmp"
}

create_secrets() {
  step "Secrets et ConfigMaps"
  ensure_tmp
  # Realm Keycloak (sans client de test) et définitions RabbitMQ : rendus par le script de la pile compose.
  python3 "${COMPOSE_DIR}/render.py" "$ENV_FILE" "$tmp" --cluster
  local key
  for key in POSTGRES_PASSWORD CATALOG_DB_PASSWORD NOTIFICATION_DB_PASSWORD KEYCLOAK_DB_PASSWORD KEYCLOAK_ADMIN_PASSWORD; do
    write_value "$key"
  done
  apply_secret create secret generic postgres-credentials \
    --from-file=POSTGRES_PASSWORD="${tmp}/POSTGRES_PASSWORD" \
    --from-file=CATALOG_DB_PASSWORD="${tmp}/CATALOG_DB_PASSWORD" \
    --from-file=NOTIFICATION_DB_PASSWORD="${tmp}/NOTIFICATION_DB_PASSWORD" \
    --from-file=KEYCLOAK_DB_PASSWORD="${tmp}/KEYCLOAK_DB_PASSWORD"
  apply_generated create configmap postgres-init --from-file=10-roles.sh="${COMPOSE_DIR}/postgres-init/10-roles.sh"
  apply_generated create configmap rabbitmq-config --from-file=rabbitmq.conf="${COMPOSE_DIR}/rabbitmq.conf"
  apply_secret create secret generic rabbitmq-definitions \
    --from-file=rabbitmq-definitions.json="${tmp}/rabbitmq-definitions.json"
  apply_secret create secret generic keycloak-admin \
    --from-file=password="${tmp}/KEYCLOAK_ADMIN_PASSWORD"
  apply_secret create secret generic keycloak-realm \
    --from-file=collector-realm.json="${tmp}/collector-realm.json"
  echo "postgres-credentials, postgres-init, rabbitmq-config, rabbitmq-definitions, keycloak-admin, keycloak-realm : à jour."
}

infra() {
  check_prerequisites
  generate_env
  create_secrets
  step "Manifestes de l'infrastructure"
  $K apply -f "${INFRA_DIR}/postgres.yaml" -f "${INFRA_DIR}/rabbitmq.yaml"
  # PostgreSQL d'abord : Keycloak a besoin de sa base `keycloak`.
  $K rollout status statefulset/postgres --timeout=300s
  $K apply -f "${INFRA_DIR}/keycloak.yaml"
  $K rollout status statefulset/rabbitmq --timeout=300s
  $K rollout status deployment/keycloak --timeout=600s
  wait_openid
  $K get pods
}

# Attend (au plus 60 s) la configuration OpenID du realm par l'Ingress HTTPS ; sort en erreur sinon.
wait_openid() {
  local code="" _
  step "Contrôle HTTPS de Keycloak"
  # Le realm est importé avant que Keycloak soit prêt ; l'Ingress met quelques secondes à apparaître.
  for _ in $(seq 1 30); do
    code=$(curl -s --max-time 10 -o /dev/null -w '%{http_code}' "https://auth.127.0.0.1.sslip.io/realms/collector/.well-known/openid-configuration" || true)
    [[ "$code" == 200 ]] && break
    sleep 2
  done
  echo "https://auth.127.0.0.1.sslip.io/realms/collector/.well-known/openid-configuration : HTTP ${code}"
  [[ "$code" == 200 ]] || exit 1
}

# Applique le realm JSON à un cluster existant. Keycloak (`start --import-realm`) saute l'import
# d'un realm déjà présent en base, et la commande `import` exige un serveur arrêté : on repart donc
# d'une base `keycloak` vide, que le démarrage suivant remplit depuis le JSON (source de vérité).
# Toute la base est recréée : realm `collector` (comptes, rôles, clients) repris du JSON, realm
# `master` et compte d'administration recréés depuis le Secret keycloak-admin. Sont perdus : les
# sessions et toute modification faite à la main dans la console d'administration.
# Commande explicite : jamais appelée par `infra` ni `all`. Relançable.
realm() {
  check_prerequisites
  generate_env
  ensure_tmp
  step "Secret keycloak-realm"
  python3 "${COMPOSE_DIR}/render.py" "$ENV_FILE" "$tmp" --cluster
  apply_secret create secret generic keycloak-realm \
    --from-file=collector-realm.json="${tmp}/collector-realm.json"
  step "Arrêt de Keycloak"
  $K scale deployment/keycloak --replicas=0
  # Si une étape suivante échoue, Keycloak ne doit pas rester arrêté : il est relancé à la sortie
  # (la base peut alors être absente ou vide : relancer `deploy.sh realm`).
  trap 'rm -rf "$tmp"; echo "deploy.sh realm interrompu : Keycloak relancé ; relancer deploy.sh realm." >&2; $K scale deployment/keycloak --replicas=1 >/dev/null 2>&1 || true' EXIT
  $K wait --for=delete pod -l app=keycloak --timeout=120s
  step "Base keycloak recréée"
  # Superutilisateur par le socket local du pod (aucun mot de passe en argument). Un -c par ordre :
  # DROP/CREATE DATABASE ne tolèrent pas un bloc de transaction. L'accès est retiré à PUBLIC comme
  # dans postgres-init/10-roles.sh.
  $K exec postgres-0 -- psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
    -c 'DROP DATABASE IF EXISTS keycloak WITH (FORCE)' \
    -c 'CREATE DATABASE keycloak OWNER keycloak' \
    -c 'REVOKE ALL ON DATABASE keycloak FROM PUBLIC'
  step "Redémarrage de Keycloak"
  $K scale deployment/keycloak --replicas=1
  trap 'rm -rf "$tmp"' EXIT
  $K rollout status deployment/keycloak --timeout=600s
  wait_openid
  local scopes
  scopes="$(curl -s --max-time 10 "https://auth.127.0.0.1.sslip.io/realms/collector/.well-known/openid-configuration" \
    | python3 -c 'import json,sys; print(" ".join(json.load(sys.stdin)["scopes_supported"]))')"
  echo "scopes_supported : ${scopes}"
}

# --- Observabilité --------------------------------------------------------------------------

# Attend (au plus 5 min) qu'une ressource existe : le pod Prometheus est créé par l'opérateur
# après l'installation du chart, il n'existe pas encore quand `helm --wait` rend la main.
wait_exists() {
  local _
  for _ in $(seq 1 150); do
    $K get "$@" >/dev/null 2>&1 && return 0
    sleep 2
  done
  echo "Ressource introuvable : $*" >&2
  return 1
}

monitoring() {
  for tool in helm; do
    command -v "$tool" >/dev/null || { echo "Outil manquant : $tool" >&2; exit 1; }
  done
  check_prerequisites
  generate_env

  step "Secret du mot de passe de Grafana"
  ensure_tmp
  write_value GRAFANA_ADMIN_PASSWORD
  ( umask 077 && printf 'admin' > "${tmp}/admin-user" )
  apply_secret create secret generic grafana-admin \
    --from-file=admin-user="${tmp}/admin-user" \
    --from-file=admin-password="${tmp}/GRAFANA_ADMIN_PASSWORD"
  echo "grafana-admin : à jour."

  step "kube-prometheus-stack ${STACK_VERSION}"
  # Les CRD (dont ServiceMonitor) sont installés par le chart lui-même (premier install).
  $H upgrade --install kps "$STACK_CHART" --version "$STACK_VERSION" \
    -f "${MON_DIR}/kube-prometheus-stack.yaml" --wait --timeout 10m
  wait_exists pod prometheus-kps-prometheus-0
  $K wait --for=condition=Ready pod/prometheus-kps-prometheus-0 --timeout=300s
  $K get crd servicemonitors.monitoring.coreos.com >/dev/null

  step "Tableau de bord Grafana"
  # Le sidecar de Grafana charge toute ConfigMap portant le label grafana_dashboard=1.
  apply_generated create configmap collector-dashboards --from-file=collector-service.json="${MON_DIR}/dashboards/collector-service.json"
  $K label configmap collector-dashboards grafana_dashboard=1 --overwrite >/dev/null
  echo "ConfigMap collector-dashboards : à jour."

  # Services déjà déployés avant la pile : on ajoute leur ServiceMonitor sans rejouer la migration
  # (--no-hooks) ni toucher aux pods ni au nombre de réplicas (--reuse-values).
  # Risque de --reuse-values : il reprend les valeurs de la DERNIÈRE révision, même en échec (image
  # ou digest d'un déploiement raté). On refuse donc si la dernière révision n'est pas « deployed ».
  local svc status
  for svc in "${SERVICES[@]}"; do
    status="$(last_status "$svc")"
    if [[ -n "$status" && "$status" != deployed ]]; then
      echo "${svc} : dernière révision Helm au statut « ${status} » : ServiceMonitor non ajouté (relancer 'deploy.sh services <tag>' d'abord)." >&2
      exit 1
    fi
    if [[ -n "$status" ]] && ! $K get servicemonitor "$svc" >/dev/null 2>&1; then
      step "ServiceMonitor de ${svc}"
      $H upgrade "$svc" "$CHART_DIR" --reuse-values --set serviceMonitor.enabled=true --no-hooks --wait --timeout 3m
    fi
  done

  step "Contrôle HTTPS de Grafana"
  local code="" anon=""
  for _ in $(seq 1 60); do
    code=$(curl -s --max-time 10 -o /dev/null -w '%{http_code}' "https://grafana.127.0.0.1.sslip.io/api/health" || true)
    [[ "$code" == 200 ]] && break
    sleep 2
  done
  # Sans identifiants, l'API doit refuser (accès anonyme désactivé).
  anon=$(curl -s --max-time 10 -o /dev/null -w '%{http_code}' "https://grafana.127.0.0.1.sslip.io/api/search" || true)
  echo "https://grafana.127.0.0.1.sslip.io/api/health : HTTP ${code} ; /api/search sans identifiants : HTTP ${anon}"
  [[ "$code" == 200 && "$anon" == 401 ]] || exit 1
  $K get pods | grep -E 'kps|prometheus|grafana' || true
}

# --- Services ------------------------------------------------------------------------------

# Digest (sha256:...) de l'index multi-architecture d'une image GHCR. Code 1 si l'image n'existe
# pas, code 2 si la vérification est impossible (Docker arrêté, GHCR injoignable) : les deux cas
# ne doivent pas donner le même message.
image_digest() {
  local out
  if ! out="$(docker buildx imagetools inspect "$1" 2>&1)"; then
    if grep -qiE 'not found|manifest unknown' <<<"$out"; then
      return 1
    fi
    echo "Vérification de $1 impossible : $(tail -n 1 <<<"$out")" >&2
    return 2
  fi
  awk '/^Digest:/ {print $2; exit}' <<<"$out"
}

# Secrets propres aux services : URL de connexion à PostgreSQL et à RabbitMQ (elles contiennent le
# mot de passe). Même méthode que create_secrets : fichiers 600 dans le dossier temporaire,
# --from-file, application côté serveur ; rien en argument de commande, rien d'affiché.
create_service_secrets() {
  step "Secrets des services"
  ensure_tmp
  local key
  for key in CATALOG_DB_PASSWORD NOTIFICATION_DB_PASSWORD RABBITMQ_CATALOG_PASSWORD RABBITMQ_NOTIFICATION_PASSWORD; do
    write_value "$key"
  done
  # printf est une commande interne du shell : les mots de passe ne passent pas par un processus
  # externe visible dans `ps`.
  ( umask 077
    printf 'postgresql+psycopg://catalog:%s@postgres:5432/catalog_db' "$(cat "${tmp}/CATALOG_DB_PASSWORD")" > "${tmp}/catalog-database-url"
    printf 'amqp://catalog:%s@rabbitmq:5672/' "$(cat "${tmp}/RABBITMQ_CATALOG_PASSWORD")" > "${tmp}/catalog-rabbitmq-url"
    printf 'postgresql+psycopg://notification:%s@postgres:5432/notification_db' "$(cat "${tmp}/NOTIFICATION_DB_PASSWORD")" > "${tmp}/notification-database-url"
    printf 'amqp://notification:%s@rabbitmq:5672/' "$(cat "${tmp}/RABBITMQ_NOTIFICATION_PASSWORD")" > "${tmp}/notification-rabbitmq-url" )
  apply_secret create secret generic catalog-service-secrets \
    --from-file=DATABASE_URL="${tmp}/catalog-database-url" \
    --from-file=RABBITMQ_URL="${tmp}/catalog-rabbitmq-url"
  apply_secret create secret generic notification-service-secrets \
    --from-file=DATABASE_URL="${tmp}/notification-database-url" \
    --from-file=RABBITMQ_URL="${tmp}/notification-rabbitmq-url"
  echo "catalog-service-secrets, notification-service-secrets : à jour."
}

# Attend (au plus 2 min) que le Deployment $1 ait au moins $2 pods Ready.
wait_min_replicas() {
  local ready="" _
  for _ in $(seq 1 60); do
    ready="$($K get deployment "$1" -o jsonpath='{.status.readyReplicas}')"
    [[ "${ready:-0}" -ge "$2" ]] && return 0
    sleep 2
  done
  echo "${1} : ${ready:-0} pod(s) Ready sur ${2} attendus." >&2
  return 1
}

# Dernière révision Helm au statut « deployed » d'une release (vide si elle n'existe pas).
deployed_revision() {
  $H history "$1" -o json 2>/dev/null \
    | python3 -c 'import json,sys
rows=[r for r in json.load(sys.stdin) if r["status"]=="deployed"]
print(rows[-1]["revision"] if rows else "")' 2>/dev/null || true
}

# Statut de la dernière révision Helm d'une release (vide si elle n'existe pas).
last_status() {
  $H history "$1" -o json 2>/dev/null \
    | python3 -c 'import json,sys
rows=json.load(sys.stdin)
print(rows[-1]["status"] if rows else "")' 2>/dev/null || true
}

# Retour arrière : chaque release que ce lancement a commencé à mettre à jour (updated[i] = 1) et qui
# avait une révision déployée avant y revient. Les autres ne sont pas touchées.
# Le schéma de la base n'est pas rétabli (les migrations Alembic restent appliquées) : les
# migrations doivent rester compatibles avec la version précédente (limite documentée).
rollback_all() {
  local svc rev i=-1
  step "ÉCHEC : retour arrière"
  for svc in "${COMPONENTS[@]}"; do
    i=$((i + 1))
    rev="${previous[$i]:-}"
    if [[ "${updated[$i]:-0}" != 1 ]]; then
      echo "${svc} : non modifié par ce lancement, laissé tel quel"
    elif [[ -n "$rev" ]]; then
      echo "${svc} : retour à la révision ${rev}"
      $H rollback "$svc" "$rev" --wait --timeout 3m || echo "  (retour arrière de ${svc} en échec)" >&2
    else
      echo "${svc} : premier déploiement, pas de révision précédente (release laissée en l'état pour diagnostic)"
    fi
  done
}

# Valide le tag et vérifie sur GHCR que les images des trois composants existent. Ne modifie rien.
# Remplit le tableau global `digest` (un digest par composant, dans l'ordre de COMPONENTS).
check_images() {
  local tag="$1" svc i=0 rc
  [[ "$tag" =~ ^sha-[0-9a-f]{7,40}$ ]] || { echo "Tag attendu : sha-<commit> (ex. sha-bec38ed), reçu « ${tag} »." >&2; exit 2; }
  for tool in helm docker; do
    command -v "$tool" >/dev/null || { echo "Outil manquant : $tool" >&2; exit 1; }
  done
  check_prerequisites
  step "Vérification des images ${tag} sur GHCR"
  # Tableaux indexés parallèles à COMPONENTS (bash 3.2 de macOS : pas de tableaux associatifs).
  digest=()
  for svc in "${COMPONENTS[@]}"; do
    # `|| rc=$?` : sous `set -e`, l'échec de la commande ferait sortir le script avant le message.
    rc=0
    digest[i]="$(image_digest "${REGISTRY}/${svc}:${tag}")" || rc=$?
    if [[ $rc -eq 2 ]]; then
      echo "Rien n'a été modifié : relancer quand Docker et GHCR répondent." >&2
      exit 1
    fi
    if [[ -z "${digest[i]}" ]]; then
      echo "Image ${REGISTRY}/${svc}:${tag} introuvable sur GHCR : rien n'a été modifié." >&2
      exit 1
    fi
    echo "${svc}:${tag} -> ${digest[i]}"
    i=$((i + 1))
  done
}

services() {
  local tag="${1:-}" svc i=0
  # 1. Le tag doit exister sur GHCR pour les trois composants : avant tout changement du cluster.
  check_images "$tag"

  generate_env
  create_service_secrets

  # ServiceMonitor : créé seulement si le CRD de Prometheus Operator existe (étape `monitoring`),
  # et seulement pour les services FastAPI (nginx n'expose pas /metrics, limite acceptée).
  local has_crd=0 sm_args=()
  if $K get crd servicemonitors.monitoring.coreos.com >/dev/null 2>&1; then
    has_crd=1
  else
    echo "CRD ServiceMonitor absent : services déployés sans supervision (lancer 'deploy.sh monitoring')."
  fi

  # Values supplémentaires facultatives (voir l'en-tête). Le fichier doit exister.
  local extra_args=()
  if [[ -n "${DEPLOY_VALUES:-}" ]]; then
    [[ -f "$DEPLOY_VALUES" ]] || { echo "DEPLOY_VALUES : fichier introuvable : ${DEPLOY_VALUES}" >&2; exit 1; }
    extra_args=(-f "$DEPLOY_VALUES")
    echo "Values supplémentaires : $(basename "$DEPLOY_VALUES")"
  fi

  # 2. Révisions Helm actuelles, pour pouvoir revenir en arrière.
  previous=()   # globales : lues par rollback_all
  updated=()
  for svc in "${COMPONENTS[@]}"; do previous+=("$(deployed_revision "$svc")"); updated+=(0); done

  # 3. Installation : migration (hook pre-install/pre-upgrade), puis Deployment. --wait attend que
  #    les pods soient Ready ; l'image est épinglée par tag@digest.
  local failed=0
  i=0
  for svc in "${COMPONENTS[@]}"; do
    step "helm upgrade --install ${svc}"
    updated[i]=1
    sm_args=()
    if [[ $has_crd -eq 1 && "$svc" != frontend ]]; then sm_args=(--set serviceMonitor.enabled=true); fi
    $H upgrade --install "$svc" "$CHART_DIR" -f "${VALUES_DIR}/${svc}.yaml" ${extra_args[@]+"${extra_args[@]}"} \
      --set image.tag="$tag" --set image.digest="${digest[i]}" ${sm_args[@]+"${sm_args[@]}"} \
      --wait --timeout 5m || { failed=1; break; }
    $K rollout status "deployment/${svc}" --timeout=180s || { failed=1; break; }
    # Le chart ne fixe pas le nombre de réplicas (c'est l'HPA qui en décide) : à la première
    # installation le Deployment démarre à 1 pod et l'HPA monte à son minimum (2) en quelques
    # secondes. On attend ce minimum avant de tester.
    wait_min_replicas "$svc" 2 || { failed=1; break; }
    i=$((i + 1))
  done

  # 4. Contrôle de bout en bout par l'Ingress.
  if [[ $failed -eq 0 ]]; then
    step "Test de fumée"
    "${HERE}/smoke.sh" || failed=1
  fi

  if [[ $failed -ne 0 ]]; then
    rollback_all
    exit 1
  fi

  # 5. Digest réellement exécuté par les pods (imageID), à comparer à celui publié par la CI.
  step "Images en cours d'exécution (imageID)"
  for svc in "${COMPONENTS[@]}"; do
    $K get pods -l "app.kubernetes.io/name=${svc}" \
      -o jsonpath='{range .items[*]}{.metadata.name}{"  "}{.status.containerStatuses[0].imageID}{"\n"}{end}'
  done
  $K get deploy,hpa,pods
}

case "${1:-}" in
  infra) infra ;;
  realm) realm ;;
  services) services "${2:-}" ;;
  monitoring) monitoring ;;
  all) check_images "${2:-}"; infra; monitoring; services "${2:-}" ;;
  *) echo "Usage : $0 infra | realm | monitoring | services <tag> | all <tag>" >&2; exit 2 ;;
esac
