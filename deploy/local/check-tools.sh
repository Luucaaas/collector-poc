#!/usr/bin/env bash
# Vérifie la présence et la version des outils de développement du POC.
# Compatible avec le bash 3.2 de macOS.
#
# Usage :
#   deploy/local/check-tools.sh            # vérifie les outils
#   deploy/local/check-tools.sh --cluster  # vérifie les outils, puis crée un cluster
#                                          # k3d de test (1 server + 2 agents),
#                                          # attend les 3 nœuds Ready et le supprime
#
# Code de sortie : 0 si tout est présent, 1 s'il manque un outil
# ou si la validation du cluster échoue.

set -u

TEST_CLUSTER="collector-check"
RUN_CLUSTER=0
[ "${1:-}" = "--cluster" ] && RUN_CLUSTER=1

MISSING=0
WARNINGS=0

if [ -t 1 ]; then
  GREEN=$'\033[32m'; RED=$'\033[31m'; YELLOW=$'\033[33m'; RESET=$'\033[0m'
else
  GREEN=""; RED=""; YELLOW=""; RESET=""
fi

# Extrait le premier numéro de version (x.y ou x.y.z) d'une chaîne.
extract_version() {
  grep -Eo '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n 1
}

row() {
  # row <outil> <version> <statut> <couleur>
  printf '%-12s %-12s %s%s%s\n' "$1" "$2" "$4" "$3" "$RESET"
}

ok()      { row "$1" "$2" "OK" "$GREEN"; }
missing() { row "$1" "-" "MANQUANT" "$RED"; MISSING=$((MISSING + 1)); }
warn()    { row "$1" "$2" "ATTENTION : $3" "$YELLOW"; WARNINGS=$((WARNINGS + 1)); }

# check <outil> <commande qui affiche la version>
check() {
  local tool="$1" cmd="$2" version
  if ! command -v "$tool" >/dev/null 2>&1; then
    missing "$tool"
    return
  fi
  version=$(eval "$cmd" 2>/dev/null | extract_version)
  ok "$tool" "${version:-?}"
}

printf '%-12s %-12s %s\n' "OUTIL" "VERSION" "STATUT"
printf '%-12s %-12s %s\n' "-----" "-------" "------"

check brew    "brew --version"
check git     "git --version"
check kubectl "kubectl version --client"
check helm    "helm version --short"
check k3d     "k3d version"
check uv      "uv --version"
check node    "node --version"

# mkcert : l'autorité de certification locale doit aussi être installée.
if command -v mkcert >/dev/null 2>&1; then
  version=$(mkcert -version 2>/dev/null | extract_version)
  if [ -f "$(mkcert -CAROOT 2>/dev/null)/rootCA.pem" ]; then
    ok mkcert "${version:-?}"
  else
    warn mkcert "${version:-?}" "CA absente, lancer 'mkcert -install'"
  fi
else
  missing mkcert
fi

# Python 3.12 : installé et géré par uv.
if command -v uv >/dev/null 2>&1 && py=$(uv python find 3.12 2>/dev/null); then
  ok python3.12 "$("$py" --version 2>&1 | extract_version)"
else
  missing python3.12
fi

# Docker : le client doit être présent et le daemon (Docker Desktop) démarré.
if command -v docker >/dev/null 2>&1; then
  version=$(docker --version 2>/dev/null | extract_version)
  if docker info >/dev/null 2>&1; then
    ok docker "${version:-?}"
  else
    warn docker "${version:-?}" "daemon arrêté, ouvrir Docker Desktop"
  fi
else
  missing docker
fi

echo
if [ "$MISSING" -gt 0 ]; then
  echo "${RED}${MISSING} outil(s) manquant(s).${RESET}"
  exit 1
fi
if [ "$WARNINGS" -gt 0 ]; then
  echo "${YELLOW}Tous les outils sont présents, ${WARNINGS} point(s) d'attention.${RESET}"
else
  echo "${GREEN}Tous les outils sont présents.${RESET}"
fi

[ "$RUN_CLUSTER" -eq 1 ] || exit 0

# --- Validation de l'environnement : cluster k3d de test -------------------
echo
echo "Création du cluster de test '$TEST_CLUSTER' (1 server + 2 agents)..."
if ! k3d cluster create "$TEST_CLUSTER" --servers 1 --agents 2 --wait; then
  echo "${RED}Échec de la création du cluster.${RESET}"
  k3d cluster delete "$TEST_CLUSTER" >/dev/null 2>&1
  exit 1
fi

status=0
if kubectl --context "k3d-$TEST_CLUSTER" wait --for=condition=Ready nodes --all --timeout=120s; then
  kubectl --context "k3d-$TEST_CLUSTER" get nodes
  ready=$(kubectl --context "k3d-$TEST_CLUSTER" get nodes --no-headers | grep -c ' Ready ')
  if [ "$ready" -eq 3 ]; then
    echo "${GREEN}Les 3 nœuds sont Ready.${RESET}"
  else
    echo "${RED}${ready} nœud(s) Ready sur 3.${RESET}"
    status=1
  fi
else
  echo "${RED}Les nœuds ne sont pas Ready après 120 s.${RESET}"
  status=1
fi

echo "Suppression du cluster de test..."
k3d cluster delete "$TEST_CLUSTER"
exit "$status"
