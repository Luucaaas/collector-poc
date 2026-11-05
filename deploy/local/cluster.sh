#!/usr/bin/env bash
# Cycle de vie du cluster k3d `collector` : création, vérification HTTPS, suppression.
#
# Usage : deploy/local/cluster.sh create | verify | delete
#   create : vérifie les pré-requis, crée le cluster (1 server + 2 agents), génère le certificat
#            mkcert s'il manque, configure Traefik (certificat par défaut, redirection
#            HTTP -> HTTPS) et crée le namespace `collector`. Relançable sans effet de bord.
#   verify : déploie une ressource temporaire (traefik/whoami), contrôle la redirection 301 et le
#            HTTPS sans `-k`, affiche les dates du certificat, puis supprime la ressource.
#   delete : supprime le cluster. Le certificat (deploy/local/.certs/) est conservé pour réutilisation.
#
# La CA mkcert doit déjà être installée (`mkcert -install`, à faire une fois, hors de ce script).
set -euo pipefail

# --- Versions épinglées (tag@digest de l'index multi-architecture) ----------------------
K3S_IMAGE="rancher/k3s:v1.35.8-k3s1@sha256:59fe491fd3b73204e499e40b325240d85c42c7189c3ae50150d37b78243f3b32"

CLUSTER="collector"
CTX="k3d-${CLUSTER}"
HOST_SUFFIX="127.0.0.1.sslip.io"
MIN_FREE_MB=7000   # seuil retenu en phase 3 (README des expérimentations)

HERE="$(cd "$(dirname "$0")" && pwd)"
K8S_DIR="$(cd "${HERE}/../k8s" && pwd)"
CERT_DIR="${HERE}/.certs"   # ignoré par Git : contient la clé privée du certificat
K="kubectl --context ${CTX}"

step() { printf '\n=== %s ===\n' "$*"; }

# Relance une commande jusqu'à ce qu'elle réussisse. $1 essais, $2 pause, le reste : commande.
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

cluster_exists() { k3d cluster list --no-headers 2>/dev/null | awk '{print $1}' | grep -qx "$CLUSTER"; }

check_prerequisites() {
  step "Pré-requis"
  for tool in docker k3d kubectl mkcert curl openssl lsof; do
    command -v "$tool" >/dev/null || { echo "Outil manquant : $tool (voir deploy/local/check-tools.sh)" >&2; exit 1; }
  done
  docker info >/dev/null 2>&1 || { echo "Docker ne répond pas : démarrer Docker Desktop." >&2; exit 1; }
  [[ -f "$(mkcert -CAROOT)/rootCA.pem" ]] || { echo "CA mkcert absente : lancer 'mkcert -install' une fois (hors de ce script)." >&2; exit 1; }
  echo "Outils présents, Docker répond, CA mkcert présente."
}

# Ports 80 et 443 du Mac libres, et 7 Go libres dans la VM Docker : seulement avant la création.
check_resources() {
  for port in 80 443; do
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "Le port ${port} du Mac est déjà utilisé :" >&2
      lsof -nP -iTCP:"$port" -sTCP:LISTEN >&2 || true
      exit 1
    fi
  done
  echo "Ports 80 et 443 du Mac : libres."
  # L'image k3s (nécessaire de toute façon) sert à mesurer l'espace libre de la VM Docker.
  local free_mb
  free_mb=$(docker run --rm --entrypoint df "$K3S_IMAGE" -m / | awk 'NR==2 {print $4}')
  echo "Espace libre de la VM Docker : ${free_mb} Mo (minimum ${MIN_FREE_MB} Mo)."
  if [[ "$free_mb" -lt "$MIN_FREE_MB" ]]; then
    echo "Espace disque insuffisant." >&2
    exit 1
  fi
}

# Certificat générique mkcert, généré une seule fois et réutilisé après un `delete`.
ensure_certificate() {
  step "Certificat mkcert"
  mkdir -p "$CERT_DIR"
  chmod 700 "$CERT_DIR"
  if [[ -f "${CERT_DIR}/tls.crt" && -f "${CERT_DIR}/tls.key" ]]; then
    echo "Certificat existant conservé."
  else
    mkcert -cert-file "${CERT_DIR}/tls.crt" -key-file "${CERT_DIR}/tls.key" "*.${HOST_SUFFIX}" "${HOST_SUFFIX}"
    chmod 600 "${CERT_DIR}/tls.key"
  fi
}

create() {
  check_prerequisites
  step "Cluster k3d"
  if cluster_exists; then
    echo "Le cluster ${CLUSTER} existe déjà : non recréé."
    k3d cluster start "$CLUSTER" >/dev/null 2>&1 || true   # sans effet s'il tourne déjà
  else
    check_resources
    # Ports 80 et 443 du Mac vers le répartiteur de charge (serverlb), qui les passe à Traefik.
    k3d cluster create "$CLUSTER" --servers 1 --agents 2 --image "$K3S_IMAGE" \
      -p "80:80@loadbalancer" -p "443:443@loadbalancer" --wait --timeout 600s
  fi
  $K wait --for=condition=Ready nodes --all --timeout=180s
  $K get nodes

  ensure_certificate

  step "Namespace et certificat par défaut de Traefik"
  $K apply -f "${K8S_DIR}/namespace.yaml"
  # Le Secret TLS est dans kube-system, là où Traefik lit son TLSStore. `apply` d'un Secret
  # généré à sec le rend relançable.
  $K -n kube-system create secret tls mkcert-wildcard \
    --cert "${CERT_DIR}/tls.crt" --key "${CERT_DIR}/tls.key" --dry-run=client -o yaml | $K apply -f - >/dev/null
  # Les CRD de Traefik n'existent qu'une fois son chart installé par k3s.
  retry 90 2 $K get crd tlsstores.traefik.io >/dev/null 2>&1
  $K apply -f "${K8S_DIR}/traefik-config.yaml"
  # La redirection n'apparaît dans les arguments de Traefik qu'après réinstallation du chart.
  retry 120 2 bash -c "$K -n kube-system get deploy traefik -o jsonpath='{.spec.template.spec.containers[0].args}' | grep -q redirections"
  $K -n kube-system rollout status deployment/traefik --timeout=300s
  echo "Cluster ${CLUSTER} prêt : 3 nœuds, Traefik en HTTPS avec redirection."
}

verify() {
  check_prerequisites
  cluster_exists || { echo "Le cluster ${CLUSTER} n'existe pas : lancer 'create'." >&2; exit 1; }
  local host="whoami.${HOST_SUFFIX}"
  trap '$K delete -f "${K8S_DIR}/whoami-verif.yaml" --ignore-not-found >/dev/null 2>&1 || true' EXIT
  step "Ressource temporaire (traefik/whoami)"
  $K apply -f "${K8S_DIR}/whoami-verif.yaml"
  $K -n collector rollout status deployment/whoami-verif --timeout=180s
  retry 60 2 bash -c "curl -s -o /dev/null -w '%{http_code}' https://${host}/ | grep -q 200"
  step "Redirection HTTP -> HTTPS"
  # Traefik répond 301 à un GET et 308 aux autres méthodes (HEAD de `curl -I`, POST) : le 308
  # conserve la méthode de la requête.
  echo "GET  : $(curl -s -o /dev/null -w 'code %{http_code}, Location %{redirect_url}' "http://${host}/")"
  echo "HEAD : $(curl -s -o /dev/null -I -w 'code %{http_code}' "http://${host}/")"
  echo "POST : $(curl -s -o /dev/null -X POST -w 'code %{http_code}' "http://${host}/")"
  step "HTTPS sans -k"
  # -w plutôt que « | head » : avec pipefail, un SIGPIPE de curl ferait échouer le script.
  echo "HTTPS : $(curl -s -o /dev/null -w 'code %{http_code}, HTTP/%{http_version}' "https://${host}/")"
  step "Certificat présenté"
  # Seules les dates et les noms d'hôte sont affichés : le sujet brut de mkcert contient le
  # nom de l'utilisateur et celui de sa machine.
  openssl s_client -connect "${host}:443" -servername "$host" </dev/null 2>/dev/null \
    | openssl x509 -noout -startdate -enddate -ext subjectAltName | grep -E '^not|DNS:' | sed 's/^ */  /'
  step "Suppression de la ressource temporaire"
}

delete() {
  step "Suppression du cluster ${CLUSTER}"
  if cluster_exists; then
    k3d cluster delete "$CLUSTER"
  else
    echo "Le cluster ${CLUSTER} n'existe pas."
  fi
  echo "Certificat conservé dans deploy/local/.certs/ (réutilisé par le prochain create)."
}

case "${1:-}" in
  create) create ;;
  verify) verify ;;
  delete) delete ;;
  *) echo "Usage : $0 create | verify | delete" >&2; exit 2 ;;
esac
