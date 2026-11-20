#!/usr/bin/env bash
# Lifecycle of the k3d cluster `collector`: creation, HTTPS check, deletion.
#
# Usage: deploy/local/cluster.sh create | verify | delete
#   create: checks the prerequisites, creates the cluster (1 server + 2 agents), generates the
#            mkcert certificate if it is missing, configures Traefik (default certificate,
#            HTTP -> HTTPS redirect) and creates the `collector` namespace. Safe to rerun.
#   verify: deploys a temporary resource (traefik/whoami), checks the 301 redirect and
#            HTTPS without `-k`, prints the certificate dates, then deletes the resource.
#   delete: deletes the cluster. The certificate (deploy/local/.certs/) is kept for reuse.
#
# The mkcert CA must already be installed (`mkcert -install`, done once, outside this script).
set -euo pipefail

# --- Pinned versions (tag@digest of the multi-architecture index) -----------------------
K3S_IMAGE="rancher/k3s:v1.35.8-k3s1@sha256:59fe491fd3b73204e499e40b325240d85c42c7189c3ae50150d37b78243f3b32"

CLUSTER="collector"
CTX="k3d-${CLUSTER}"
HOST_SUFFIX="127.0.0.1.sslip.io"
MIN_FREE_MB=10000   # the full deployment uses 6.4 GB (protocol 4) + kubelet margin (evictions below ~3.1 GB free)

HERE="$(cd "$(dirname "$0")" && pwd)"
K8S_DIR="$(cd "${HERE}/../k8s" && pwd)"
CERT_DIR="${HERE}/.certs"   # ignored by Git: contains the certificate's private key
K="kubectl --context ${CTX}"

step() { printf '\n=== %s ===\n' "$*"; }

# Reruns a command until it succeeds. $1 attempts, $2 pause, the rest: the command.
retry() {
  local tries="$1" pause="$2"
  shift 2
  for _ in $(seq 1 "$tries"); do
    "$@" && return 0
    sleep "$pause"
  done
  echo "Failed after ${tries} attempts: $*" >&2
  return 1
}

cluster_exists() { k3d cluster list --no-headers 2>/dev/null | awk '{print $1}' | grep -qx "$CLUSTER"; }

check_prerequisites() {
  step "Prerequisites"
  for tool in docker k3d kubectl mkcert curl openssl lsof; do
    command -v "$tool" >/dev/null || { echo "Missing tool: $tool (see deploy/local/check-tools.sh)" >&2; exit 1; }
  done
  docker info >/dev/null 2>&1 || { echo "Docker is not responding: start Docker Desktop." >&2; exit 1; }
  [[ -f "$(mkcert -CAROOT)/rootCA.pem" ]] || { echo "mkcert CA missing: run 'mkcert -install' once (outside this script)." >&2; exit 1; }
  echo "Tools present, Docker responds, mkcert CA present."
}

# Mac ports 80 and 443 free, and 10 GB free in the Docker VM: only before creation.
check_resources() {
  for port in 80 443; do
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "Mac port ${port} is already in use:" >&2
      lsof -nP -iTCP:"$port" -sTCP:LISTEN >&2 || true
      exit 1
    fi
  done
  echo "Mac ports 80 and 443: free."
  # The k3s image (needed anyway) is used to measure the free space of the Docker VM.
  local free_mb
  free_mb=$(docker run --rm --entrypoint df "$K3S_IMAGE" -m / | awk 'NR==2 {print $4}')
  echo "Free space in the Docker VM: ${free_mb} MB (minimum ${MIN_FREE_MB} MB)."
  if [[ "$free_mb" -lt "$MIN_FREE_MB" ]]; then
    echo "Not enough disk space." >&2
    exit 1
  fi
}

# Wildcard mkcert certificate, generated once and reused after a `delete`.
ensure_certificate() {
  step "mkcert certificate"
  mkdir -p "$CERT_DIR"
  chmod 700 "$CERT_DIR"
  if [[ -f "${CERT_DIR}/tls.crt" && -f "${CERT_DIR}/tls.key" ]]; then
    echo "Existing certificate kept."
  else
    mkcert -cert-file "${CERT_DIR}/tls.crt" -key-file "${CERT_DIR}/tls.key" "*.${HOST_SUFFIX}" "${HOST_SUFFIX}"
    chmod 600 "${CERT_DIR}/tls.key"
  fi
}

create() {
  check_prerequisites
  step "Cluster k3d"
  if cluster_exists; then
    echo "Cluster ${CLUSTER} already exists: not recreated."
    k3d cluster start "$CLUSTER" >/dev/null 2>&1 || true   # no effect if it is already running
  else
    check_resources
    # Mac ports 80 and 443 to the load balancer (serverlb), which passes them to Traefik.
    k3d cluster create "$CLUSTER" --servers 1 --agents 2 --image "$K3S_IMAGE" \
      -p "80:80@loadbalancer" -p "443:443@loadbalancer" --wait --timeout 600s
  fi
  $K wait --for=condition=Ready nodes --all --timeout=180s
  $K get nodes

  ensure_certificate

  step "Namespace and default Traefik certificate"
  $K apply -f "${K8S_DIR}/namespace.yaml"
  # The TLS Secret is in kube-system, where Traefik reads its TLSStore. `apply` of a Secret
  # generated dry-run makes it rerunnable.
  $K -n kube-system create secret tls mkcert-wildcard \
    --cert "${CERT_DIR}/tls.crt" --key "${CERT_DIR}/tls.key" --dry-run=client -o yaml | $K apply -f - >/dev/null
  # Traefik's CRDs only exist once its chart has been installed by k3s.
  retry 90 2 $K get crd tlsstores.traefik.io >/dev/null 2>&1
  $K apply -f "${K8S_DIR}/traefik-config.yaml"
  # The redirect only shows up in Traefik's arguments after the chart is reinstalled.
  retry 120 2 bash -c "$K -n kube-system get deploy traefik -o jsonpath='{.spec.template.spec.containers[0].args}' | grep -q redirections"
  $K -n kube-system rollout status deployment/traefik --timeout=300s
  echo "Cluster ${CLUSTER} ready: 3 nodes, Traefik on HTTPS with redirect."
}

verify() {
  check_prerequisites
  cluster_exists || { echo "Cluster ${CLUSTER} does not exist: run 'create'." >&2; exit 1; }
  local host="whoami.${HOST_SUFFIX}"
  trap '$K delete -f "${K8S_DIR}/whoami-verif.yaml" --ignore-not-found >/dev/null 2>&1 || true' EXIT
  step "Temporary resource (traefik/whoami)"
  $K apply -f "${K8S_DIR}/whoami-verif.yaml"
  $K -n collector rollout status deployment/whoami-verif --timeout=180s
  retry 60 2 bash -c "curl -s -o /dev/null -w '%{http_code}' https://${host}/ | grep -q 200"
  step "HTTP -> HTTPS redirect"
  # Traefik answers 301 to a GET and 308 to the other methods (HEAD of `curl -I`, POST): the 308
  # keeps the request method.
  echo "GET  : $(curl -s -o /dev/null -w 'code %{http_code}, Location %{redirect_url}' "http://${host}/")"
  echo "HEAD : $(curl -s -o /dev/null -I -w 'code %{http_code}' "http://${host}/")"
  echo "POST : $(curl -s -o /dev/null -X POST -w 'code %{http_code}' "http://${host}/")"
  step "HTTPS without -k"
  # -w rather than "| head": with pipefail, a SIGPIPE on curl would make the script fail.
  echo "HTTPS : $(curl -s -o /dev/null -w 'code %{http_code}, HTTP/%{http_version}' "https://${host}/")"
  step "Certificate presented"
  # Only the dates and host names are printed: mkcert's raw subject contains the user's
  # name and that of their machine.
  openssl s_client -connect "${host}:443" -servername "$host" </dev/null 2>/dev/null \
    | openssl x509 -noout -startdate -enddate -ext subjectAltName | grep -E '^not|DNS:' | sed 's/^ */  /'
  step "Deleting the temporary resource"
}

delete() {
  step "Deleting cluster ${CLUSTER}"
  if cluster_exists; then
    k3d cluster delete "$CLUSTER"
  else
    echo "Cluster ${CLUSTER} does not exist."
  fi
  echo "Certificate kept in deploy/local/.certs/ (reused by the next create)."
}

case "${1:-}" in
  create) create ;;
  verify) verify ;;
  delete) delete ;;
  *) echo "Usage: $0 create | verify | delete" >&2; exit 2 ;;
esac
