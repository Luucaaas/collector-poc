#!/usr/bin/env bash
# Déploiement sur le cluster k3d `collector`.
#
# Usage : deploy/local/deploy.sh infra
#   infra : génère les mots de passe manquants dans deploy/local/.env, crée ou met à jour les
#           Secrets et ConfigMaps, applique les manifestes de deploy/infra (PostgreSQL, RabbitMQ,
#           Keycloak + Ingress `auth.`) et attend que tout soit prêt. Relançable sans effet de bord.
#
# (Les étapes des services et de l'observabilité s'ajouteront ici : P6-03 et P6-04.)
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

create_secrets() {
  step "Secrets et ConfigMaps"
  tmp="$(mktemp -d)"   # variable globale : le trap EXIT s'exécute après le retour de la fonction
  trap 'rm -rf "$tmp"' EXIT   # les fichiers rendus contiennent des mots de passe : toujours supprimés
  chmod 700 "$tmp"
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
  step "Contrôle HTTPS de Keycloak"
  # Le realm est importé avant que Keycloak soit prêt ; l'Ingress met quelques secondes à apparaître.
  for _ in $(seq 1 30); do
    code=$(curl -s -o /dev/null -w '%{http_code}' "https://auth.127.0.0.1.sslip.io/realms/collector/.well-known/openid-configuration" || true)
    [[ "$code" == 200 ]] && break
    sleep 2
  done
  echo "https://auth.127.0.0.1.sslip.io/realms/collector/.well-known/openid-configuration : HTTP ${code}"
  [[ "$code" == 200 ]] || exit 1
  $K get pods
}

case "${1:-}" in
  infra) infra ;;
  *) echo "Usage : $0 infra" >&2; exit 2 ;;
esac
