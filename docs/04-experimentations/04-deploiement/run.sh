#!/usr/bin/env bash
# Protocol 4: deployment of the POC on the k3d cluster `collector`, from scratch, with measurements.
#
# Usage: docs/04-experimentations/04-deploiement/run.sh [<tag>]      (default: sha-bec38ed)
#
# WARNING: deletes then recreates the `collector` cluster (pod data is lost; the mkcert
# certificate and deploy/local/.env are kept). Takes about 11 minutes (including 5 min of waiting for the failing deployment). The cluster
# is left complete at the end.
#
# Steps: 1 versions and initial disk; 2 cluster.sh delete, create, deploy.sh all (timed);
# 3 memory, disk, placement; 4 self-healing (deleting a pod under a request loop);
# 5 rollback of a failing version (memory limit too low), service monitored;
# 6 traceability pod -> digest -> tag -> commit -> CI run; 7 end-to-end test event.
# The output is written to resultats/run-YYYYMMDD-HHMM.log. No password is displayed.
set -euo pipefail

TAG="${1:-sha-bec38ed}"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "${HERE}/../../.." && pwd)"
LOCAL="${REPO}/deploy/local"
K="kubectl --context k3d-collector -n collector"
H="helm --kube-context k3d-collector -n collector"
API="https://api.127.0.0.1.sslip.io/catalog/api/v1/categories"
mkdir -p "${HERE}/resultats"
LOG="${HERE}/resultats/run-$(date +%Y%m%d-%H%M).log"
exec > >(tee "$LOG") 2>&1

work="$(mktemp -d)"
loop_pid=""
defect_started=0   # set to 1 when the failing version is launched (step 5)
# On exit: stops the loop, removes the temporary files and, if the script fails after the
# start of step 5, redeploys the nominal configuration (without DEPLOY_VALUES) so as not to leave
# a failing version on the cluster.
cleanup() {
  local rc=$?
  [[ -z "$loop_pid" ]] || kill "$loop_pid" 2>/dev/null || true
  if [[ $rc -ne 0 && $defect_started -eq 1 ]]; then
    echo "Script FAILURE (code ${rc}) after the failing version: redeploying the nominal configuration." >&2
    env -u DEPLOY_VALUES "${LOCAL}/deploy.sh" services "$TAG" || echo "Nominal redeployment failed: check the cluster." >&2
  fi
  rm -rf "$work"
}
trap cleanup EXIT
fail() { echo "ASSERTION FAILED: $*" >&2; exit 1; }

step() { printf '\n=== %s ===\n' "$*"; }
now() { python3 -c 'import time; print(f"{time.time():.3f}")'; }
elapsed() { python3 -c "print(f'{$2 - $1:.1f}')"; }
stamp() { date "+%d/%m/%Y %H:%M:%S"; }

# Disk space of the Docker Desktop virtual machine (the one hosting the k3d nodes), in MB.
# Same method as cluster.sh: `df` in the k3s image (already present, pinned), no other image.
K3S_IMAGE="$(sed -n 's/^K3S_IMAGE="\(.*\)"$/\1/p' "${LOCAL}/cluster.sh")"
vm_disk() { docker run --rm --entrypoint df "$K3S_IMAGE" -m / | awk 'NR==2 {printf "used %s MB, free %s MB (size %s MB)\n", $3, $4, $2}'; }

# Background loop of public requests: one "epoch code" line about every 0.1 s.
start_loop() {
  : > "$work/loop.txt"
  loop_start="$(now)"
  ( while :; do
      code="$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' "$API" || true)"
      printf '%s %s\n' "$(date +%s)" "${code:-000}" >> "$work/loop.txt"
      sleep 0.1
    done ) &
  loop_pid=$!
}
stop_loop() {
  kill "$loop_pid" 2>/dev/null || true
  wait "$loop_pid" 2>/dev/null || true
  loop_pid=""
  local total ok
  loop_duration="$(elapsed "$loop_start" "$(now)")"
  total="$(wc -l < "$work/loop.txt" | tr -d ' ')"
  ok="$(awk '$2 == 200' "$work/loop.txt" | wc -l | tr -d ' ')"
  loop_failed=$((total - ok))
  echo "Request loop: ${total} requests in ${loop_duration} s, ${ok} 200 responses, ${loop_failed} failed"
  awk '$2 != 200 {c[$2]++} END {for (k in c) printf "  code %s: %d\n", k, c[k]}' "$work/loop.txt"
}

ready() { $K get deployment "$1" -o jsonpath='{.status.readyReplicas}' 2>/dev/null; }

step "1. Environment and initial disk ($(stamp))"
sw_vers | tr '\n' ' '; echo
echo "Docker: $(docker version --format '{{.Server.Version}}'), $(docker info --format '{{.NCPU}} CPU, {{.MemTotal}} bytes of memory')"
echo "k3d $(k3d version | head -n 1 | awk '{print $3}') ; $(kubectl version --client | head -n 1) ; helm $(helm version --short) ; mkcert $(mkcert -version)"
echo "Mac disk before: $(df -h / | awk 'NR==2 {print $4 " free"}')"

step "2. Deployment from scratch, tag ${TAG}"
t0="$(now)"
"${LOCAL}/cluster.sh" delete
t1="$(now)"
echo "RESULT cluster.sh delete: $(elapsed "$t0" "$t1") s"
echo "RESULT Docker VM disk without cluster: $(vm_disk)"
docker system df
"${LOCAL}/cluster.sh" create
t2="$(now)"
echo "RESULT cluster.sh create: $(elapsed "$t1" "$t2") s"
"${LOCAL}/deploy.sh" all "$TAG"
t3="$(now)"
echo "RESULT deploy.sh all ${TAG} (infra, monitoring, services, smoke.sh): $(elapsed "$t2" "$t3") s"
echo "RESULT total create + deploy: $(elapsed "$t1" "$t3") s"
"${LOCAL}/smoke.sh"

step "3. Idle measurements ($(stamp))"
echo "Waiting 90 s for metrics-server and the HPA to settle..."
sleep 90
echo "RESULT Docker VM disk with the full deployment: $(vm_disk)"
docker system df
echo "--- kubectl top nodes"
kubectl --context k3d-collector top nodes
echo "--- kubectl top pods -A"
kubectl --context k3d-collector top pods -A
kubectl --context k3d-collector top pods -A --no-headers | awk '
  {gsub("Mi","",$4); total += $4; if ($1 == "collector") app += $4}
  END {printf "RESULT pod memory: namespace collector %d Mi, all namespaces %d Mi\n", app, total}'
echo "--- kubectl get pods -A -o wide (placement)"
kubectl --context k3d-collector get pods -A -o wide
echo "--- images running"
kubectl --context k3d-collector get pods -A -o jsonpath='{range .items[*]}{range .spec.containers[*]}{.image}{"\n"}{end}{end}' | sort -u

step "4. Self-healing: deleting a catalog-service pod under requests ($(stamp))"
start_loop
sleep 5
victim="$($K get pods -l app.kubernetes.io/name=catalog-service -o jsonpath='{.items[0].metadata.name}')"
echo "Pod deleted: ${victim}; ready before: $(ready catalog-service)"
t0="$(now)"
$K delete pod "$victim" --wait=false >/dev/null
gone=""; recovered=""
for _ in $(seq 1 240); do
  if [[ -z "$gone" ]] && ! $K get pod "$victim" >/dev/null 2>&1; then gone="$(now)"; fi
  if [[ -n "$gone" && "$(ready catalog-service)" == 2 ]] \
     && [[ "$($K get pods -l app.kubernetes.io/name=catalog-service --no-headers | wc -l | tr -d ' ')" == 2 ]]; then
    recovered="$(now)"; break
  fi
  sleep 0.5
done
[[ -n "$recovered" ]] || { echo "FAILURE: 2 Ready replicas not recovered within 120 s" >&2; exit 1; }
echo "RESULT old pod gone after $(elapsed "$t0" "$gone") s; 2 Ready replicas (and 2 pods) after $(elapsed "$t0" "$recovered") s"
sleep 5
stop_loop
[[ "$loop_failed" -eq 0 ]] || fail "${loop_failed} failed request(s) during self-healing (expected: 0)"
$K get pods -l app.kubernetes.io/name=catalog-service -o wide

step "5. Rollback of a failing version ($(stamp))"
echo "Revisions before:"; $H history catalog-service
# Realistic failing version: memory limit of 24 Mi (the service uses about 77 Mi) ->
# the pods are killed by the kernel (OOMKilled) before being ready; `rollout status` never succeeds.
cat > "$work/failing.yaml" <<'YAML'
resources:
  requests: {cpu: 50m, memory: 16Mi}
  limits: {cpu: 200m, memory: 24Mi}
YAML
defect_started=1
start_loop
sleep 3
# Snapshot of the pods 90 s after the start of the failing deployment: state, restarts, cause of the last termination.
( sleep 90
  { echo "--- catalog-service pods, 90 s after the start"
    $K get pods -l app.kubernetes.io/name=catalog-service -o wide
    $K get pods -l app.kubernetes.io/name=catalog-service -o jsonpath='{range .items[*]}{.metadata.name}{"  ready="}{.status.containerStatuses[0].ready}{"  restarts="}{.status.containerStatuses[0].restartCount}{"  last termination="}{.status.containerStatuses[0].lastState.terminated.reason}{"\n"}{end}'
  } > "$work/failing-pods.txt" 2>&1 ) &
snap_pid=$!
t0="$(now)"
rc=0
DEPLOY_VALUES="$work/failing.yaml" "${LOCAL}/deploy.sh" services "$TAG" > "$work/deploy-failing.txt" 2>&1 || rc=$?
# The temporary file path is not written to the versioned log.
sed -i '' "s#${work}#<temporary folder>#g" "$work/deploy-failing.txt"
t1="$(now)"
# The useful lines of the output (the rest is in the Helm log).
grep -E "^===|Extra values|Error|error|timed out|Waiting|rolling back|back to revision|Rollback|not modified|rollback" "$work/deploy-failing.txt" | tail -n 40 || true
echo "RESULT deploy.sh services with the failing version: exit code ${rc} (expected: 1) after $(elapsed "$t0" "$t1") s"
sleep 5
stop_loop
wait "$snap_pid" 2>/dev/null || true
[[ "$rc" -eq 1 ]] || fail "deploy.sh with the failing version returned code ${rc} (expected: 1)"
[[ "$loop_failed" -eq 0 ]] || fail "${loop_failed} failed request(s) during the rollback (expected: 0)"
defect_started=0   # the rollback succeeded: the nominal configuration is in place
cat "$work/failing-pods.txt"
echo "Revisions after:"; $H history catalog-service
echo "Pods after:"; $K get pods -l app.kubernetes.io/name=catalog-service
echo "Memory limit in effect: $($K get deployment catalog-service -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}')"
"${LOCAL}/smoke.sh"

step "6. Traceability ($(stamp))"
pod="$($K get pods -l app.kubernetes.io/name=catalog-service -o jsonpath='{.items[0].metadata.name}')"
image="$($K get pod "$pod" -o jsonpath='{.spec.containers[0].image}')"
image_id="$($K get pod "$pod" -o jsonpath='{.status.containerStatuses[0].imageID}')"
tag="${image#*:}"; tag="${tag%%@*}"
sha7="${tag#sha-}"
echo "pod       : ${pod}"
echo "image     : ${image}"
echo "imageID   : ${image_id}"
echo "tag       : ${tag}"
echo "digest of the tag on GHCR: $(docker buildx imagetools inspect "ghcr.io/luucaaas/catalog-service:${tag}" | awk '/^Digest:/ {print $2; exit}')"
full="$(git -C "$REPO" rev-parse "$sha7")"
echo "commit    : ${full} - $(git -C "$REPO" log -1 --format=%s "$full")"
if command -v gh >/dev/null; then
  echo "CI run: $(gh run list --commit "$full" --json databaseId,workflowName,conclusion,url -q '.[] | "\(.workflowName) \(.conclusion) \(.url)"')"
fi
echo "OCI revision label: $(docker buildx imagetools inspect "ghcr.io/luucaaas/catalog-service:${tag}" --format '{{json .Image}}' 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("linux/arm64", d).get("config", {}).get("Labels", {}).get("org.opencontainers.image.revision", "not read"))' 2>/dev/null || echo "not read")"

step "7. End-to-end test event ($(stamp))"
"${LOCAL}/publish-test-event.sh"

step "Final state ($(stamp))"
$K get deploy,hpa,pods
echo "Cluster left complete."
