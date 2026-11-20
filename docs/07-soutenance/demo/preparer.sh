#!/usr/bin/env bash
# Pre-demo check: is everything ready? Changes nothing (reads only).
#
#   docs/07-soutenance/demo/preparer.sh               full check (smoke.sh included, about 1 minute)
#   docs/07-soutenance/demo/preparer.sh --rapide      without smoke.sh (quick reminder, a few seconds)
#   docs/07-soutenance/demo/preparer.sh --veille [h]  also keeps the Mac from sleeping for
#                                                     h hours (2 by default), with `caffeinate`
#
# Output: "READY" (code 0), or the list of what is missing with the command that fixes it (code 1).
# Passwords are read from deploy/local/.env, given to curl through a pipe (never as an argument,
# never displayed).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${HERE}/../../.." && pwd)"
ENV_FILE="${ROOT}/deploy/local/.env"
CTX="k3d-collector"
K="kubectl --context ${CTX} -n collector"
API="https://api.127.0.0.1.sslip.io"
QUICK=0; KEEP_AWAKE=0; HOURS=2
while [[ $# -gt 0 ]]; do
  case "$1" in
    --rapide) QUICK=1 ;;
    --veille) KEEP_AWAKE=1; if [[ "${2:-}" =~ ^[0-9]+$ ]]; then HOURS="$2"; shift; fi ;;
    *) echo "Usage: $0 [--rapide] [--veille [heures]]" >&2; exit 2 ;;
  esac
  shift
done

missing_count=0; warn_count=0
ok() { printf 'OK      %s\n' "$1"; }
missing() { printf 'MISSING %s\n          -> %s\n' "$1" "$2"; missing_count=$((missing_count + 1)); }
warn() { printf 'WARNING %s\n          -> %s\n' "$1" "$2"; warn_count=$((warn_count + 1)); }
http() { curl -s --max-time 10 -o /dev/null -w '%{http_code}' "$1" 2>/dev/null || true; }

echo "=== Before the demo, $(date '+%d/%m/%Y %H:%M') ==="

# 1. Docker, ressources et disque
if docker info >/dev/null 2>&1; then
  cpu="$(docker info --format '{{.NCPU}}')"; mem="$(docker info --format '{{.MemTotal}}')"
  if [[ "$cpu" -ge 8 && "$mem" -ge 7500000000 ]]; then
    ok "Docker answers: ${cpu} CPU, $((mem / 1000000000)) GB of memory"
  else
    missing "Docker has only ${cpu} CPU and $((mem / 1000000000)) GB" "Docker Desktop > Settings > Resources: 10 CPU and 8 GB"
  fi
else
  missing "Docker does not answer" "open Docker Desktop and wait until it is ready"
fi
free_mb="$(df -m / | awk 'NR==2 {print $4}')"
if [[ "$free_mb" -ge 10000 ]]; then ok "Disk: $((free_mb / 1000)) GB free"
else missing "Disk: ${free_mb} MB free (less than 10,000)" "free up space (docker system prune must not touch other projects)"; fi

# 2. Cluster and nodes
if ready_nodes="$(kubectl --context "$CTX" get nodes --no-headers 2>/dev/null | grep -c ' Ready ')" && [[ "$ready_nodes" -eq 3 ]]; then
  ok "Cluster ${CTX}: 3 nodes Ready"
else
  missing "Cluster missing or nodes not ready (${ready_nodes:-0}/3)" "docker start \$(docker ps -aq --filter name=k3d-collector) ; otherwise deploy/local/cluster.sh create then deploy.sh all <tag>"
fi

# 3. Pods, HPA, deployed versions
if $K get pods >/dev/null 2>&1; then
  bad_pods="$($K get pods --no-headers | awk '$3 != "Running" && $3 != "Completed" {print $1 " (" $3 ")"}' | tr '\n' ' ')"
  [[ -z "$bad_pods" ]] && ok "No failing pod" || missing "Failing pods: ${bad_pods}" "kubectl -n collector describe pod <name> ; rerun deploy.sh services <tag>"
  not_ready="$($K get pods --no-headers | awk '$3 == "Running" {split($2, r, "/"); if (r[1] != r[2]) print $1}' | tr '\n' ' ')"
  [[ -z "$not_ready" ]] || missing "Pods not ready yet: ${not_ready}" "wait a minute and rerun this script"
  hpa_bad=""
  for name in catalog-service notification-service frontend; do
    state="$($K get hpa "$name" -o jsonpath='{.status.currentReplicas}/{.status.desiredReplicas}' 2>/dev/null || true)"
    [[ "$state" == "2/2" ]] || hpa_bad="${hpa_bad}${name}=${state:-absent} "
  done
  if [[ -z "$hpa_bad" ]]; then ok "HPA of the 3 components at 2 replicas"
  else missing "HPA not at 2 replicas: ${hpa_bad}" "wait for the return to 2 (5 to 10 minutes after a load): kubectl -n collector get hpa -w"; fi
  tag="$($K get deploy catalog-service -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null | sed 's/@.*//; s/.*://')"
  ok "Deployed version: ${tag}"
fi

# 4. Name resolution by the Mac (the one Chrome and Safari use, not curl's).
# A DNS64 network (iPhone tethering, some Wi-Fi) also answers a gateway IPv6 address
# (64:ff9b::7f00:1) that the browser tries first: connection reset
# (ERR_CONNECTION_RESET) while curl and smoke.sh pass. Without Internet, sslip.io does not answer.
# Remedy: declare the 4 hosts in /etc/hosts (127.0.0.1 and ::1, the cluster listens on both).
HOSTS_LIST="app.127.0.0.1.sslip.io api.127.0.0.1.sslip.io auth.127.0.0.1.sslip.io grafana.127.0.0.1.sslip.io"
HOSTS_FIX="sudo sh -c 'printf \"127.0.0.1 ${HOSTS_LIST}\\n::1 ${HOSTS_LIST}\\n\" >> /etc/hosts' (by you, password requested)"
HOSTS_FILE="${HOSTS_FILE:-/etc/hosts}"
# declared_in_hosts <ip> <name>: true if an uncommented line associates this name with this address.
declared_in_hosts() {
  awk -v ip="$1" -v name="$2" '{ sub(/#.*/, "") } $1 == ip { for (i = 2; i <= NF; i++) if ($i == name) t = 1 }
    END { exit !t }' "$HOSTS_FILE" 2>/dev/null
}
declared=0; unreachable_names=""
for h in $HOSTS_LIST; do
  declared_in_hosts 127.0.0.1 "$h" && declared_in_hosts ::1 "$h" && declared=$((declared + 1))
  addresses="$(dscacheutil -q host -a name "$h" 2>/dev/null | awk '/^ip(v6)?_address:/ {print $2}' | sort -u | tr '\n' ' ')"
  others="$(tr ' ' '\n' <<< "$addresses" | grep -vE '^(127\.0\.0\.1|::1)?$' | tr '\n' ' ' || true)"
  if [[ -z "${addresses// /}" ]]; then unreachable_names="${unreachable_names}${h} (unresolved) "
  elif [[ -n "${others// /}" ]]; then unreachable_names="${unreachable_names}${h} (also ${others% }) "; fi
done
if [[ -n "$unreachable_names" ]]; then
  missing "The browser will not reach the cluster: ${unreachable_names}" "$HOSTS_FIX"
elif [[ $declared -eq 4 ]]; then
  ok "The 4 hosts are declared in /etc/hosts: the demo depends neither on the network nor on the Internet"
else
  warn "Hosts resolved by sslip.io: needs Internet and a network without DNS64" "$HOSTS_FIX"
fi

# 5. Smoke test, Grafana, Keycloak, application
if [[ $QUICK -eq 1 ]]; then
  warn "smoke.sh skipped (--rapide)" "run deploy/local/smoke.sh"
else
  if output="$("${ROOT}/deploy/local/smoke.sh" 2>&1)"; then
    ok "smoke.sh: $(grep -c '^OK' <<< "$output") checks green"
  else
    missing "smoke.sh fails ($(grep -c '^FAIL' <<< "$output") check(s))" "deploy/local/smoke.sh for the details"
  fi
fi
[[ "$(http https://auth.127.0.0.1.sslip.io/realms/collector/.well-known/openid-configuration)" == 200 ]] \
  && ok "Keycloak reachable (https://auth.127.0.0.1.sslip.io)" \
  || missing "Keycloak does not answer" "kubectl -n collector get pods -l app=keycloak ; wait until it is ready"
[[ "$(http https://app.127.0.0.1.sslip.io/)" == 200 ]] \
  && ok "Application reachable (https://app.127.0.0.1.sslip.io), certificate recognized" \
  || missing "The application does not answer (or certificate not recognized)" "mkcert -install (to be done by you, password requested) ; deploy/local/smoke.sh"
[[ "$(http https://grafana.127.0.0.1.sslip.io/login)" == 200 ]] \
  && ok "Grafana reachable (https://grafana.127.0.0.1.sslip.io)" \
  || missing "Grafana does not answer" "deploy/local/deploy.sh monitoring"

# 6. Passwords: present, and the Grafana one accepted (without displaying it)
if [[ -f "$ENV_FILE" ]]; then
  absent_keys=""
  for key in ADMIN_PASSWORD ALICE_PASSWORD BOB_PASSWORD CHLOE_PASSWORD GRAFANA_ADMIN_PASSWORD; do
    grep -qE "^${key}=.+" "$ENV_FILE" || absent_keys="${absent_keys}${key} "
  done
  [[ -z "$absent_keys" ]] && ok "Demo passwords present in deploy/local/.env" \
    || missing "Passwords missing: ${absent_keys}" "deploy/local/deploy.sh infra (generates them)"
  gpw="$(grep -m1 -E '^GRAFANA_ADMIN_PASSWORD=' "$ENV_FILE" | cut -d= -f2- || true)"
  if [[ -n "$gpw" ]]; then
    code="$(printf 'user = "admin:%s"\n' "$gpw" | curl -s --max-time 10 -o /dev/null -w '%{http_code}' -K - https://grafana.127.0.0.1.sslip.io/api/org 2>/dev/null || true)"
    [[ "$code" == 200 ]] && ok "Grafana password accepted (mot-de-passe.sh grafana copies it)" \
      || missing "Grafana rejects the .env password (HTTP ${code})" "deploy/local/deploy.sh monitoring (realigns the password)"
  fi
else
  missing "deploy/local/.env not found" "deploy/local/deploy.sh infra"
fi

# 7. Tools: Locust (uv), Playwright Chromium, mkcert authority
if [[ -x "${ROOT}/tests/load/.venv/bin/locust" ]]; then ok "uv environment of tests/load: Locust present"
else missing "Locust missing" "cd tests/load && uv sync"; fi
if [[ -x "${ROOT}/frontend/node_modules/.bin/playwright" ]] && ls -d "${HOME}"/Library/Caches/ms-playwright/chromium-* >/dev/null 2>&1; then
  ok "Playwright and its Chromium present"
else missing "Playwright or Chromium missing" "cd frontend && npm ci && npx playwright install chromium"; fi
[[ -f "$(mkcert -CAROOT 2>/dev/null)/rootCA.pem" ]] && ok "mkcert authority present" || missing "mkcert authority missing" "mkcert -install (by you)"

# 8. Clean catalogue: only the demo set
categories="$(curl -s --max-time 10 "${API}/catalog/api/v1/categories" 2>/dev/null | python3 -c '
import json, sys
try:
    print("|".join(sorted(c["name"] for c in json.load(sys.stdin)["items"])))
except Exception:
    print("?")' || true)"
expected="Cartes à collectionner|Figurines|Jeux vidéo rétro|Monnaies et timbres|Vinyles"
if [[ "$categories" == "$expected" ]]; then
  total="$(curl -s --max-time 10 "${API}/catalog/api/v1/articles?limit=1" | python3 -c 'import json,sys; print(json.load(sys.stdin)["total"])' 2>/dev/null || echo 0)"
  [[ "$total" -ge 11 ]] && ok "Clean catalogue: 5 demo categories, ${total} articles" \
    || missing "Incomplete catalogue (${total} articles)" "docs/07-soutenance/demo/donnees-demo.sh"
elif [[ "$categories" == "" ]]; then
  missing "Empty catalogue" "docs/07-soutenance/demo/donnees-demo.sh"
else
  missing "The catalogue contains something other than the demo set" "rebuild a fresh cluster then donnees-demo.sh (script-demo.md, \"La veille\")"
fi

# 9. Last CI run on main
if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
  for wf in backend frontend; do
    line="$(gh run list --workflow "${wf}.yml" --branch main --limit 1 --json status,conclusion,headSha --jq '.[0] | "\(.status) \(.conclusion) \(.headSha[0:7])"' 2>/dev/null || true)"
    case "$line" in
      "completed success "*) ok "CI ${wf} on main: green (commit ${line##* })" ;;
      "completed "*) missing "CI ${wf} on main: ${line}" "gh run list --workflow ${wf}.yml --branch main ; run 'gh run view --log-failed'" ;;
      "") warn "CI ${wf}: state unreadable" "gh auth status" ;;
      *) warn "CI ${wf} on main: in progress (${line})" "wait for the run to finish before starting the demo" ;;
    esac
  done
else
  warn "gh missing or not logged in: CI state not checked" "gh auth login (by you)"
fi

# 10. Sleep prevention
if [[ $KEEP_AWAKE -eq 1 ]]; then
  caffeinate -dis -t $((HOURS * 3600)) >/dev/null 2>&1 &
  echo "Sleep prevented for ${HOURS} h (caffeinate, process $!). To stop it: kill $!"
  disown $!
fi

echo
if [[ $missing_count -eq 0 ]]; then
  [[ $warn_count -eq 0 ]] && echo "READY: everything is green." || echo "READY, with ${warn_count} point(s) of attention above."
else
  echo "NOT READY: ${missing_count} point(s) to fix (command shown under each MISSING)."
  exit 1
fi
