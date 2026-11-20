#!/usr/bin/env bash
# Deployment to the k3d cluster `collector`.
#
# Usage: deploy/local/deploy.sh infra | realm | monitoring | services <tag> | all <tag>
#   infra: generates the missing passwords in deploy/local/.env, creates or updates the
#           Secrets and ConfigMaps, applies the deploy/infra manifests (PostgreSQL, RabbitMQ,
#           Keycloak + `auth.` Ingress) and waits until everything is ready. Safe to rerun.
#   realm: applies the Keycloak realm (deploy/keycloak/collector-realm.json) to an existing cluster.
#           `start --import-realm` skips a realm that already exists: the command stops Keycloak,
#           recreates its PostgreSQL database (everything it holds goes back to the JSON and the keycloak-admin Secret:
#           sessions, and any change made by hand in the console), restarts it and waits for
#           the OpenID configuration. Never run by `infra` or `all`. See deploy/README.md.
#   services <tag>: deploys catalog-service, notification-service and the front end (frontend) from
#           the images published by the CI (ghcr.io/luucaaas/<component>:<tag>, e.g. sha-bec38ed)
#           with the Helm chart deploy/helm/collector-service. Refuses a tag that is missing from GHCR for
#           any of the three before changing anything; waits for the pods, runs smoke.sh; on
#           failure, goes back to the previous revision (`helm rollback`) and exits with an error.
#   monitoring: installs the slimmed-down kube-prometheus-stack (Prometheus, operator, Grafana,
#           kube-state-metrics) in the `collector` namespace, loads the dashboard, exposes
#           Grafana over HTTPS (https://grafana.127.0.0.1.sslip.io). Admin password
#           generated in .env. Enables the ServiceMonitor of services already deployed. Safe to rerun.
#   all <tag>: `infra`, `monitoring` then `services <tag>` (so the ServiceMonitor CRD exists
#           before the services chart creates one).
#
# Optional variable: DEPLOY_VALUES=<Helm values file> is added (`-f`) after the values
# of each component (services and front end), for `services` and `all`. Used to deploy a deliberately
# failing configuration and demonstrate the rollback (e.g. a memory limit that is too low), without changing the script.
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
# FastAPI services (Secrets, ServiceMonitor) and components deployed by the chart (services + front end).
SERVICES=(catalog-service notification-service)
COMPONENTS=(catalog-service notification-service frontend)
# Observability stack: chart version pinned (experiment 3), values in deploy/infra/monitoring.
STACK_CHART="oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack"
STACK_VERSION="91.9.0"
MON_DIR="${INFRA_DIR}/monitoring"
digest=()   # image digests (filled in by check_images)
tmp=""   # temporary directory for the files holding passwords (created by ensure_tmp)

step() { printf '\n=== %s ===\n' "$*"; }

check_prerequisites() {
  for tool in kubectl python3 openssl curl; do
    command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
  done
  kubectl --context "$CTX" get namespace "$NS" >/dev/null 2>&1 \
    || { echo "Cluster ${CLUSTER} missing or without namespace ${NS}: run 'deploy/local/cluster.sh create'." >&2; exit 1; }
}

# Adds to .env each variable of the template that is missing there (or empty), with a random
# password. base64 of 18 bytes = 24 characters; '+' and '/' replaced so it stays usable
# in a URL. Nothing is printed except the names of the variables created.
generate_env() {
  step "Passwords (deploy/local/.env)"
  if [[ ! -f "$ENV_FILE" ]]; then
    ( umask 077 && : > "$ENV_FILE" )
  fi
  chmod 600 "$ENV_FILE"
  local created=() line key
  while IFS= read -r line; do
    [[ "$line" == *=change-me ]] || continue
    key="${line%%=*}"
    if ! grep -q "^${key}=." "$ENV_FILE"; then
      # Key present but empty ("KEY="): remove the line so it is not duplicated.
      if grep -q "^${key}=$" "$ENV_FILE"; then
        ( umask 077 && grep -v "^${key}=$" "$ENV_FILE" > "${ENV_FILE}.tmp" || true )
        mv "${ENV_FILE}.tmp" "$ENV_FILE"
      fi
      printf '%s=%s\n' "$key" "$(openssl rand -base64 18 | tr '+/' '-_')" >> "$ENV_FILE"
      created+=("$key")
    fi
  done < "${HERE}/.env.example"
  if [[ ${#created[@]} -gt 0 ]]; then
    echo "Generated: ${created[*]}"
  else
    echo "All present: passwords unchanged."
  fi
}

# Writes the value of a .env variable to a file in the temporary directory (600). Passwords thus
# reach kubectl through a file (--from-file), never as a command argument, where `ps`
# would show them. Called directly (not inside "$(...)"): its `exit 1` does stop the script if
# the value is missing or empty, so a Secret is never created with an empty password.
write_value() {
  local key="$1" value
  value="$(grep "^${key}=" "$ENV_FILE" | head -n 1 | cut -d= -f2- || true)"
  if [[ -z "$value" ]]; then
    echo "Variable ${key} missing or empty in ${ENV_FILE}." >&2
    exit 1
  fi
  ( umask 077 && printf '%s' "$value" > "${tmp}/${key}" )
}

# Applies a dry-run generated object: `create ... --dry-run=client -o yaml | apply` makes the command
# rerunnable (created the first time, updated afterwards).
apply_generated() { $K "$@" --dry-run=client -o yaml | $K apply -f - >/dev/null; }

# For Secrets: client-side `apply` would copy their data (base64 passwords) into the
# last-applied-configuration annotation. Server-side apply does not write it; we also
# remove the annotation from a Secret created by a previous version of the script.
apply_secret() {
  local name="$4"   # arguments: create secret generic <name> ...
  $K "$@" --dry-run=client -o yaml | $K apply --server-side --force-conflicts -f - >/dev/null
  $K annotate secret "$name" kubectl.kubernetes.io/last-applied-configuration- >/dev/null
}

# Creates (once per run) the 700 temporary directory for the files holding passwords. Global
# variable: the EXIT trap runs after the functions return; the files
# are always deleted when the script exits.
ensure_tmp() {
  [[ -z "$tmp" ]] || return 0
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  chmod 700 "$tmp"
}

create_secrets() {
  step "Secrets and ConfigMaps"
  ensure_tmp
  # Keycloak realm (without test client) and RabbitMQ definitions: rendered by the compose stack script.
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
  echo "postgres-credentials, postgres-init, rabbitmq-config, rabbitmq-definitions, keycloak-admin, keycloak-realm: up to date."
}

infra() {
  check_prerequisites
  generate_env
  create_secrets
  step "Infrastructure manifests"
  $K apply -f "${INFRA_DIR}/postgres.yaml" -f "${INFRA_DIR}/rabbitmq.yaml"
  # PostgreSQL first: Keycloak needs its `keycloak` database.
  $K rollout status statefulset/postgres --timeout=300s
  $K apply -f "${INFRA_DIR}/keycloak.yaml"
  $K rollout status statefulset/rabbitmq --timeout=300s
  $K rollout status deployment/keycloak --timeout=600s
  wait_openid
  $K get pods
}

# Waits (at most 60 s) for the realm OpenID configuration through the HTTPS Ingress; exits with an error otherwise.
wait_openid() {
  local code="" _
  step "Keycloak HTTPS check"
  # The realm is imported before Keycloak is ready; the Ingress takes a few seconds to appear.
  for _ in $(seq 1 30); do
    code=$(curl -s --max-time 10 -o /dev/null -w '%{http_code}' "https://auth.127.0.0.1.sslip.io/realms/collector/.well-known/openid-configuration" || true)
    [[ "$code" == 200 ]] && break
    sleep 2
  done
  echo "https://auth.127.0.0.1.sslip.io/realms/collector/.well-known/openid-configuration : HTTP ${code}"
  [[ "$code" == 200 ]] || exit 1
}

# Applies the realm JSON to an existing cluster. Keycloak (`start --import-realm`) skips the import
# of a realm already in the database, and the `import` command requires a stopped server: so we start
# again from an empty `keycloak` database, which the next start fills from the JSON (source of truth).
# The whole database is recreated: `collector` realm (accounts, roles, clients) taken from the JSON, `master`
# realm and admin account recreated from the keycloak-admin Secret. Lost: sessions
# and any change made by hand in the admin console.
# Explicit command: never called by `infra` or `all`. Safe to rerun.
realm() {
  check_prerequisites
  generate_env
  ensure_tmp
  step "keycloak-realm Secret"
  python3 "${COMPOSE_DIR}/render.py" "$ENV_FILE" "$tmp" --cluster
  apply_secret create secret generic keycloak-realm \
    --from-file=collector-realm.json="${tmp}/collector-realm.json"
  step "Stopping Keycloak"
  $K scale deployment/keycloak --replicas=0
  # If a later step fails, Keycloak must not stay stopped: it is restarted on exit
  # (the database may then be missing or empty: rerun `deploy.sh realm`).
  trap 'rm -rf "$tmp"; echo "deploy.sh realm interrupted: Keycloak restarted; rerun deploy.sh realm." >&2; $K scale deployment/keycloak --replicas=1 >/dev/null 2>&1 || true' EXIT
  $K wait --for=delete pod -l app=keycloak --timeout=120s
  step "keycloak database recreated"
  # Superuser through the pod's local socket (no password as an argument). One -c per statement:
  # DROP/CREATE DATABASE do not tolerate a transaction block. Access is removed from PUBLIC as
  # in postgres-init/10-roles.sh.
  $K exec postgres-0 -- psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
    -c 'DROP DATABASE IF EXISTS keycloak WITH (FORCE)' \
    -c 'CREATE DATABASE keycloak OWNER keycloak' \
    -c 'REVOKE ALL ON DATABASE keycloak FROM PUBLIC'
  step "Restarting Keycloak"
  $K scale deployment/keycloak --replicas=1
  trap 'rm -rf "$tmp"' EXIT
  $K rollout status deployment/keycloak --timeout=600s
  wait_openid
  local scopes
  scopes="$(curl -s --max-time 10 "https://auth.127.0.0.1.sslip.io/realms/collector/.well-known/openid-configuration" \
    | python3 -c 'import json,sys; print(" ".join(json.load(sys.stdin)["scopes_supported"]))')"
  echo "scopes_supported : ${scopes}"
}

# --- Observability -------------------------------------------------------------------------

# Waits (at most 5 min) for a resource to exist: the Prometheus pod is created by the operator
# after the chart is installed, it does not exist yet when `helm --wait` returns.
wait_exists() {
  local _
  for _ in $(seq 1 150); do
    $K get "$@" >/dev/null 2>&1 && return 0
    sleep 2
  done
  echo "Resource not found: $*" >&2
  return 1
}

monitoring() {
  for tool in helm; do
    command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
  done
  check_prerequisites
  generate_env

  step "Grafana password Secret"
  ensure_tmp
  write_value GRAFANA_ADMIN_PASSWORD
  ( umask 077 && printf 'admin' > "${tmp}/admin-user" )
  apply_secret create secret generic grafana-admin \
    --from-file=admin-user="${tmp}/admin-user" \
    --from-file=admin-password="${tmp}/GRAFANA_ADMIN_PASSWORD"
  echo "grafana-admin: up to date."

  step "kube-prometheus-stack ${STACK_VERSION}"
  # The CRDs (including ServiceMonitor) are installed by the chart itself (first install).
  $H upgrade --install kps "$STACK_CHART" --version "$STACK_VERSION" \
    -f "${MON_DIR}/kube-prometheus-stack.yaml" --wait --timeout 10m
  wait_exists pod prometheus-kps-prometheus-0
  $K wait --for=condition=Ready pod/prometheus-kps-prometheus-0 --timeout=300s
  $K get crd servicemonitors.monitoring.coreos.com >/dev/null

  step "Grafana dashboard"
  # The Grafana sidecar loads any ConfigMap carrying the label grafana_dashboard=1.
  apply_generated create configmap collector-dashboards --from-file=collector-service.json="${MON_DIR}/dashboards/collector-service.json"
  $K label configmap collector-dashboards grafana_dashboard=1 --overwrite >/dev/null
  echo "ConfigMap collector-dashboards: up to date."

  # Services deployed before the stack: we add their ServiceMonitor without replaying the migration
  # (--no-hooks) and without touching the pods or the replica count (--reuse-values).
  # Risk of --reuse-values: it takes the values of the LAST revision, even a failed one (image
  # or digest of a failed deployment). So we refuse if the last revision is not "deployed".
  local svc status
  for svc in "${SERVICES[@]}"; do
    status="$(last_status "$svc")"
    if [[ -n "$status" && "$status" != deployed ]]; then
      echo "${svc}: last Helm revision has status \"${status}\": ServiceMonitor not added (rerun 'deploy.sh services <tag>' first)." >&2
      exit 1
    fi
    if [[ -n "$status" ]] && ! $K get servicemonitor "$svc" >/dev/null 2>&1; then
      step "ServiceMonitor of ${svc}"
      $H upgrade "$svc" "$CHART_DIR" --reuse-values --set serviceMonitor.enabled=true --no-hooks --wait --timeout 3m
    fi
  done

  step "Grafana HTTPS check"
  local code="" anon=""
  for _ in $(seq 1 60); do
    code=$(curl -s --max-time 10 -o /dev/null -w '%{http_code}' "https://grafana.127.0.0.1.sslip.io/api/health" || true)
    [[ "$code" == 200 ]] && break
    sleep 2
  done
  # Without credentials, the API must refuse (anonymous access disabled).
  anon=$(curl -s --max-time 10 -o /dev/null -w '%{http_code}' "https://grafana.127.0.0.1.sslip.io/api/search" || true)
  echo "https://grafana.127.0.0.1.sslip.io/api/health: HTTP ${code}; /api/search without credentials: HTTP ${anon}"
  [[ "$code" == 200 && "$anon" == 401 ]] || exit 1
  $K get pods | grep -E 'kps|prometheus|grafana' || true
}

# --- Services ------------------------------------------------------------------------------

# Digest (sha256:...) of the multi-architecture index of a GHCR image. Code 1 if the image does not
# exist, code 2 if the check is impossible (Docker stopped, GHCR unreachable): both cases
# must not give the same message.
image_digest() {
  local out
  if ! out="$(docker buildx imagetools inspect "$1" 2>&1)"; then
    if grep -qiE 'not found|manifest unknown' <<<"$out"; then
      return 1
    fi
    echo "Cannot check $1: $(tail -n 1 <<<"$out")" >&2
    return 2
  fi
  awk '/^Digest:/ {print $2; exit}' <<<"$out"
}

# Secrets specific to the services: PostgreSQL and RabbitMQ connection URLs (they contain the
# password). Same method as create_secrets: 600 files in the temporary directory,
# --from-file, server-side apply; nothing as a command argument, nothing printed.
create_service_secrets() {
  step "Service Secrets"
  ensure_tmp
  local key
  for key in CATALOG_DB_PASSWORD NOTIFICATION_DB_PASSWORD RABBITMQ_CATALOG_PASSWORD RABBITMQ_NOTIFICATION_PASSWORD; do
    write_value "$key"
  done
  # printf is a shell builtin: the passwords do not go through an external process visible
  # in `ps`.
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
  echo "catalog-service-secrets, notification-service-secrets: up to date."
}

# Waits (at most 2 min) until Deployment $1 has at least $2 Ready pods.
wait_min_replicas() {
  local ready="" _
  for _ in $(seq 1 60); do
    ready="$($K get deployment "$1" -o jsonpath='{.status.readyReplicas}')"
    [[ "${ready:-0}" -ge "$2" ]] && return 0
    sleep 2
  done
  echo "${1}: ${ready:-0} Ready pod(s) out of ${2} expected." >&2
  return 1
}

# Last Helm revision with status "deployed" of a release (empty if it does not exist).
deployed_revision() {
  $H history "$1" -o json 2>/dev/null \
    | python3 -c 'import json,sys
rows=[r for r in json.load(sys.stdin) if r["status"]=="deployed"]
print(rows[-1]["revision"] if rows else "")' 2>/dev/null || true
}

# Status of the last Helm revision of a release (empty if it does not exist).
last_status() {
  $H history "$1" -o json 2>/dev/null \
    | python3 -c 'import json,sys
rows=json.load(sys.stdin)
print(rows[-1]["status"] if rows else "")' 2>/dev/null || true
}

# Rollback: each release that this run started updating (updated[i] = 1) and that
# had a deployed revision beforehand goes back to it. The others are not touched.
# The database schema is not restored (the Alembic migrations stay applied): migrations
# must stay compatible with the previous version (documented limit).
rollback_all() {
  local svc rev i=-1
  step "FAILURE: rolling back"
  for svc in "${COMPONENTS[@]}"; do
    i=$((i + 1))
    rev="${previous[$i]:-}"
    if [[ "${updated[$i]:-0}" != 1 ]]; then
      echo "${svc}: not modified by this run, left as is"
    elif [[ -n "$rev" ]]; then
      echo "${svc}: back to revision ${rev}"
      $H rollback "$svc" "$rev" --wait --timeout 3m || echo "  (rollback of ${svc} failed)" >&2
    else
      echo "${svc}: first deployment, no previous revision (release left as is for diagnosis)"
    fi
  done
}

# Validates the tag and checks on GHCR that the images of the three components exist. Changes nothing.
# Fills the global `digest` array (one digest per component, in the order of COMPONENTS).
check_images() {
  local tag="$1" svc i=0 rc
  [[ "$tag" =~ ^sha-[0-9a-f]{7,40}$ ]] || { echo "Expected tag: sha-<commit> (e.g. sha-bec38ed), got \"${tag}\"." >&2; exit 2; }
  for tool in helm docker; do
    command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
  done
  check_prerequisites
  step "Checking images ${tag} on GHCR"
  # Indexed arrays parallel to COMPONENTS (macOS bash 3.2: no associative arrays).
  digest=()
  for svc in "${COMPONENTS[@]}"; do
    # `|| rc=$?`: under `set -e`, the command failing would exit the script before the message.
    rc=0
    digest[i]="$(image_digest "${REGISTRY}/${svc}:${tag}")" || rc=$?
    if [[ $rc -eq 2 ]]; then
      echo "Nothing was changed: rerun when Docker and GHCR respond." >&2
      exit 1
    fi
    if [[ -z "${digest[i]}" ]]; then
      echo "Image ${REGISTRY}/${svc}:${tag} not found on GHCR: nothing was changed." >&2
      exit 1
    fi
    echo "${svc}:${tag} -> ${digest[i]}"
    i=$((i + 1))
  done
}

services() {
  local tag="${1:-}" svc i=0
  # 1. The tag must exist on GHCR for the three components: before any change to the cluster.
  check_images "$tag"

  generate_env
  create_service_secrets

  # ServiceMonitor: created only if the Prometheus Operator CRD exists (`monitoring` step),
  # and only for the FastAPI services (nginx does not expose /metrics, accepted limit).
  local has_crd=0 sm_args=()
  if $K get crd servicemonitors.monitoring.coreos.com >/dev/null 2>&1; then
    has_crd=1
  else
    echo "ServiceMonitor CRD missing: services deployed without monitoring (run 'deploy.sh monitoring')."
  fi

  # Optional extra values (see the header). The file must exist.
  local extra_args=()
  if [[ -n "${DEPLOY_VALUES:-}" ]]; then
    [[ -f "$DEPLOY_VALUES" ]] || { echo "DEPLOY_VALUES: file not found: ${DEPLOY_VALUES}" >&2; exit 1; }
    extra_args=(-f "$DEPLOY_VALUES")
    echo "Extra values: $(basename "$DEPLOY_VALUES")"
  fi

  # 2. Current Helm revisions, so we can roll back.
  previous=()   # globals: read by rollback_all
  updated=()
  for svc in "${COMPONENTS[@]}"; do previous+=("$(deployed_revision "$svc")"); updated+=(0); done

  # 3. Installation: migration (pre-install/pre-upgrade hook), then Deployment. --wait waits until
  #    the pods are Ready; the image is pinned by tag@digest.
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
    # The chart does not set the replica count (the HPA decides): on the first
    # install the Deployment starts at 1 pod and the HPA raises it to its minimum (2) within a few
    # seconds. We wait for that minimum before testing.
    wait_min_replicas "$svc" 2 || { failed=1; break; }
    i=$((i + 1))
  done

  # 4. End-to-end check through the Ingress.
  if [[ $failed -eq 0 ]]; then
    step "Smoke test"
    "${HERE}/smoke.sh" || failed=1
  fi

  if [[ $failed -ne 0 ]]; then
    rollback_all
    exit 1
  fi

  # 5. Digest actually run by the pods (imageID), to compare with the one published by the CI.
  step "Running images (imageID)"
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
  *) echo "Usage: $0 infra | realm | monitoring | services <tag> | all <tag>" >&2; exit 2 ;;
esac
