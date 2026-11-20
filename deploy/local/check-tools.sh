#!/usr/bin/env bash
# Checks that the POC's development tools are present and shows their version.
# Compatible with the macOS bash 3.2.
#
# Usage:
#   deploy/local/check-tools.sh            # checks the tools
#   deploy/local/check-tools.sh --cluster  # checks the tools, then creates a test
#                                          # k3d cluster (1 server + 2 agents),
#                                          # waits for the 3 Ready nodes and deletes it
#
# Exit code: 0 if everything is present, 1 if a tool is missing
# or if the cluster validation fails.

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

# Extracts the first version number (x.y or x.y.z) from a string.
extract_version() {
  grep -Eo '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n 1
}

row() {
  # row <tool> <version> <status> <color>
  printf '%-12s %-12s %s%s%s\n' "$1" "$2" "$4" "$3" "$RESET"
}

ok()      { row "$1" "$2" "OK" "$GREEN"; }
missing() { row "$1" "-" "MISSING" "$RED"; MISSING=$((MISSING + 1)); }
warn()    { row "$1" "$2" "WARNING: $3" "$YELLOW"; WARNINGS=$((WARNINGS + 1)); }

# check <tool> <command that prints the version>
check() {
  local tool="$1" cmd="$2" version
  if ! command -v "$tool" >/dev/null 2>&1; then
    missing "$tool"
    return
  fi
  version=$(eval "$cmd" 2>/dev/null | extract_version)
  ok "$tool" "${version:-?}"
}

printf '%-12s %-12s %s\n' "TOOL" "VERSION" "STATUS"
printf '%-12s %-12s %s\n' "----" "-------" "------"

check brew    "brew --version"
check git     "git --version"
check kubectl "kubectl version --client"
check helm    "helm version --short"
check k3d     "k3d version"
check uv      "uv --version"
check node    "node --version"

# mkcert: the local certificate authority must also be installed.
if command -v mkcert >/dev/null 2>&1; then
  version=$(mkcert -version 2>/dev/null | extract_version)
  if [ -f "$(mkcert -CAROOT 2>/dev/null)/rootCA.pem" ]; then
    ok mkcert "${version:-?}"
  else
    warn mkcert "${version:-?}" "CA missing, run 'mkcert -install'"
  fi
else
  missing mkcert
fi

# Python 3.12: installed and managed by uv.
if command -v uv >/dev/null 2>&1 && py=$(uv python find 3.12 2>/dev/null); then
  ok python3.12 "$("$py" --version 2>&1 | extract_version)"
else
  missing python3.12
fi

# Docker: the client must be present and the daemon (Docker Desktop) started.
if command -v docker >/dev/null 2>&1; then
  version=$(docker --version 2>/dev/null | extract_version)
  if docker info >/dev/null 2>&1; then
    ok docker "${version:-?}"
  else
    warn docker "${version:-?}" "daemon stopped, open Docker Desktop"
  fi
else
  missing docker
fi

echo
if [ "$MISSING" -gt 0 ]; then
  echo "${RED}${MISSING} tool(s) missing.${RESET}"
  exit 1
fi
if [ "$WARNINGS" -gt 0 ]; then
  echo "${YELLOW}All tools are present, ${WARNINGS} warning(s).${RESET}"
else
  echo "${GREEN}All tools are present.${RESET}"
fi

[ "$RUN_CLUSTER" -eq 1 ] || exit 0

# --- Environment validation: test k3d cluster -------------------------------
echo
echo "Creating the test cluster '$TEST_CLUSTER' (1 server + 2 agents)..."
if ! k3d cluster create "$TEST_CLUSTER" --servers 1 --agents 2 --wait; then
  echo "${RED}Cluster creation failed.${RESET}"
  k3d cluster delete "$TEST_CLUSTER" >/dev/null 2>&1
  exit 1
fi

status=0
if kubectl --context "k3d-$TEST_CLUSTER" wait --for=condition=Ready nodes --all --timeout=120s; then
  kubectl --context "k3d-$TEST_CLUSTER" get nodes
  ready=$(kubectl --context "k3d-$TEST_CLUSTER" get nodes --no-headers | grep -c ' Ready ')
  if [ "$ready" -eq 3 ]; then
    echo "${GREEN}All 3 nodes are Ready.${RESET}"
  else
    echo "${RED}${ready} node(s) Ready out of 3.${RESET}"
    status=1
  fi
else
  echo "${RED}The nodes are not Ready after 120 s.${RESET}"
  status=1
fi

echo "Deleting the test cluster..."
k3d cluster delete "$TEST_CLUSTER"
exit "$status"
