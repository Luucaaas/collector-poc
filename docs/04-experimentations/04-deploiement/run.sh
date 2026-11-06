#!/usr/bin/env bash
# Protocole 4 : déploiement du POC sur le cluster k3d `collector`, de zéro, avec mesures.
#
# Usage : docs/04-experimentations/04-deploiement/run.sh [<tag>]      (défaut : sha-bec38ed)
#
# ATTENTION : supprime puis recrée le cluster `collector` (les données des pods sont perdues ; le
# certificat mkcert et deploy/local/.env sont conservés). Dure environ 11 minutes (dont 5 min d'attente du déploiement défaillant). Le cluster
# est laissé complet à la fin.
#
# Étapes : 1 versions et disque initial ; 2 cluster.sh delete, create, deploy.sh all (chronométrés) ;
# 3 mémoire, disque, placement ; 4 auto-réparation (suppression d'un pod sous boucle de requêtes) ;
# 5 retour arrière sur une version défaillante (limite de mémoire trop basse), service surveillé ;
# 6 traçabilité pod -> digest -> tag -> commit -> run de CI ; 7 événement de test de bout en bout.
# La sortie est écrite dans resultats/run-AAAAMMJJ-HHMM.log. Aucun mot de passe n'est affiché.
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
defect_started=0   # passe à 1 quand la version défaillante est lancée (étape 5)
# À la sortie : arrête la boucle, supprime les fichiers temporaires et, si le script échoue après le
# début de l'étape 5, redéploie la configuration nominale (sans DEPLOY_VALUES) pour ne pas laisser
# une version défaillante sur le cluster.
cleanup() {
  local rc=$?
  [[ -z "$loop_pid" ]] || kill "$loop_pid" 2>/dev/null || true
  if [[ $rc -ne 0 && $defect_started -eq 1 ]]; then
    echo "ÉCHEC du script (code ${rc}) après la version défaillante : redéploiement de la configuration nominale." >&2
    env -u DEPLOY_VALUES "${LOCAL}/deploy.sh" services "$TAG" || echo "Redéploiement nominal en échec : vérifier le cluster." >&2
  fi
  rm -rf "$work"
}
trap cleanup EXIT
fail() { echo "ASSERTION EN ÉCHEC : $*" >&2; exit 1; }

step() { printf '\n=== %s ===\n' "$*"; }
now() { python3 -c 'import time; print(f"{time.time():.3f}")'; }
elapsed() { python3 -c "print(f'{$2 - $1:.1f}')"; }
stamp() { date "+%d/%m/%Y %H:%M:%S"; }

# Espace disque de la machine virtuelle de Docker Desktop (celle où vivent les nœuds k3d), en Mo.
# Même méthode que cluster.sh : `df` dans l'image k3s (déjà présente, épinglée), aucune autre image.
K3S_IMAGE="$(sed -n 's/^K3S_IMAGE="\(.*\)"$/\1/p' "${LOCAL}/cluster.sh")"
vm_disk() { docker run --rm --entrypoint df "$K3S_IMAGE" -m / | awk 'NR==2 {printf "utilisé %s Mo, libre %s Mo (taille %s Mo)\n", $3, $4, $2}'; }

# Boucle de requêtes publiques en arrière-plan : une ligne « epoch code » toutes les 0,1 s environ.
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
  echo "Boucle de requêtes : ${total} requêtes en ${loop_duration} s, ${ok} réponses 200, ${loop_failed} en échec"
  awk '$2 != 200 {c[$2]++} END {for (k in c) printf "  code %s : %d\n", k, c[k]}' "$work/loop.txt"
}

ready() { $K get deployment "$1" -o jsonpath='{.status.readyReplicas}' 2>/dev/null; }

step "1. Environnement et disque initial ($(stamp))"
sw_vers | tr '\n' ' '; echo
echo "Docker : $(docker version --format '{{.Server.Version}}'), $(docker info --format '{{.NCPU}} CPU, {{.MemTotal}} octets de mémoire')"
echo "k3d $(k3d version | head -n 1 | awk '{print $3}') ; $(kubectl version --client | head -n 1) ; helm $(helm version --short) ; mkcert $(mkcert -version)"
echo "Disque du Mac avant : $(df -h / | awk 'NR==2 {print $4 " libres"}')"

step "2. Déploiement depuis rien, tag ${TAG}"
t0="$(now)"
"${LOCAL}/cluster.sh" delete
t1="$(now)"
echo "RESULTAT cluster.sh delete : $(elapsed "$t0" "$t1") s"
echo "RESULTAT disque de la VM Docker sans cluster : $(vm_disk)"
docker system df
"${LOCAL}/cluster.sh" create
t2="$(now)"
echo "RESULTAT cluster.sh create : $(elapsed "$t1" "$t2") s"
"${LOCAL}/deploy.sh" all "$TAG"
t3="$(now)"
echo "RESULTAT deploy.sh all ${TAG} (infra, monitoring, services, smoke.sh) : $(elapsed "$t2" "$t3") s"
echo "RESULTAT total create + deploy : $(elapsed "$t1" "$t3") s"
"${LOCAL}/smoke.sh"

step "3. Mesures au repos ($(stamp))"
echo "Attente de 90 s pour que metrics-server et l'HPA se stabilisent..."
sleep 90
echo "RESULTAT disque de la VM Docker avec le déploiement complet : $(vm_disk)"
docker system df
echo "--- kubectl top nodes"
kubectl --context k3d-collector top nodes
echo "--- kubectl top pods -A"
kubectl --context k3d-collector top pods -A
kubectl --context k3d-collector top pods -A --no-headers | awk '
  {gsub("Mi","",$4); total += $4; if ($1 == "collector") app += $4}
  END {printf "RESULTAT mémoire des pods : namespace collector %d Mi, tous namespaces %d Mi\n", app, total}'
echo "--- kubectl get pods -A -o wide (placement)"
kubectl --context k3d-collector get pods -A -o wide
echo "--- images en cours d'exécution"
kubectl --context k3d-collector get pods -A -o jsonpath='{range .items[*]}{range .spec.containers[*]}{.image}{"\n"}{end}{end}' | sort -u

step "4. Auto-réparation : suppression d'un pod de catalog-service sous requêtes ($(stamp))"
start_loop
sleep 5
victim="$($K get pods -l app.kubernetes.io/name=catalog-service -o jsonpath='{.items[0].metadata.name}')"
echo "Pod supprimé : ${victim} ; prêts avant : $(ready catalog-service)"
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
[[ -n "$recovered" ]] || { echo "ECHEC : 2 réplicas Ready non retrouvés en 120 s" >&2; exit 1; }
echo "RESULTAT ancien pod disparu après $(elapsed "$t0" "$gone") s ; 2 réplicas Ready (et 2 pods) après $(elapsed "$t0" "$recovered") s"
sleep 5
stop_loop
[[ "$loop_failed" -eq 0 ]] || fail "${loop_failed} requête(s) en échec pendant l'auto-réparation (attendu : 0)"
$K get pods -l app.kubernetes.io/name=catalog-service -o wide

step "5. Retour arrière sur une version défaillante ($(stamp))"
echo "Révisions avant :"; $H history catalog-service
# Version défaillante réaliste : limite de mémoire de 24 Mi (le service en utilise environ 77 Mi) ->
# les pods sont tués par le noyau (OOMKilled) avant d'être prêts ; `rollout status` ne réussit jamais.
cat > "$work/defaillant.yaml" <<'YAML'
resources:
  requests: {cpu: 50m, memory: 16Mi}
  limits: {cpu: 200m, memory: 24Mi}
YAML
defect_started=1
start_loop
sleep 3
# Instantané des pods 90 s après le début du déploiement défaillant : état, redémarrages, cause du dernier arrêt.
( sleep 90
  { echo "--- pods de catalog-service, 90 s après le début"
    $K get pods -l app.kubernetes.io/name=catalog-service -o wide
    $K get pods -l app.kubernetes.io/name=catalog-service -o jsonpath='{range .items[*]}{.metadata.name}{"  prêt="}{.status.containerStatuses[0].ready}{"  redémarrages="}{.status.containerStatuses[0].restartCount}{"  dernier arrêt="}{.status.containerStatuses[0].lastState.terminated.reason}{"\n"}{end}'
  } > "$work/pods-defaillants.txt" 2>&1 ) &
snap_pid=$!
t0="$(now)"
rc=0
DEPLOY_VALUES="$work/defaillant.yaml" "${LOCAL}/deploy.sh" services "$TAG" > "$work/deploy-defaillant.txt" 2>&1 || rc=$?
# Le chemin du fichier temporaire n'est pas écrit dans le journal versionné.
sed -i '' "s#${work}#<dossier temporaire>#g" "$work/deploy-defaillant.txt"
t1="$(now)"
# Les lignes utiles de la sortie (le reste est dans le journal de Helm).
grep -E "^===|Values supp|Error|error|timed out|Waiting|retour|Rollback|non modifié|rollback" "$work/deploy-defaillant.txt" | tail -n 40 || true
echo "RESULTAT deploy.sh services avec la version défaillante : code de sortie ${rc} (attendu : 1) après $(elapsed "$t0" "$t1") s"
sleep 5
stop_loop
wait "$snap_pid" 2>/dev/null || true
[[ "$rc" -eq 1 ]] || fail "deploy.sh avec la version défaillante a rendu le code ${rc} (attendu : 1)"
[[ "$loop_failed" -eq 0 ]] || fail "${loop_failed} requête(s) en échec pendant le retour arrière (attendu : 0)"
defect_started=0   # le retour arrière a réussi : la configuration nominale est en place
cat "$work/pods-defaillants.txt"
echo "Révisions après :"; $H history catalog-service
echo "Pods après :"; $K get pods -l app.kubernetes.io/name=catalog-service
echo "Limite mémoire en vigueur : $($K get deployment catalog-service -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}')"
"${LOCAL}/smoke.sh"

step "6. Traçabilité ($(stamp))"
pod="$($K get pods -l app.kubernetes.io/name=catalog-service -o jsonpath='{.items[0].metadata.name}')"
image="$($K get pod "$pod" -o jsonpath='{.spec.containers[0].image}')"
image_id="$($K get pod "$pod" -o jsonpath='{.status.containerStatuses[0].imageID}')"
tag="${image#*:}"; tag="${tag%%@*}"
sha7="${tag#sha-}"
echo "pod       : ${pod}"
echo "image     : ${image}"
echo "imageID   : ${image_id}"
echo "tag       : ${tag}"
echo "digest du tag sur GHCR : $(docker buildx imagetools inspect "ghcr.io/luucaaas/catalog-service:${tag}" | awk '/^Digest:/ {print $2; exit}')"
full="$(git -C "$REPO" rev-parse "$sha7")"
echo "commit    : ${full} — $(git -C "$REPO" log -1 --format=%s "$full")"
if command -v gh >/dev/null; then
  echo "run de CI : $(gh run list --commit "$full" --json databaseId,workflowName,conclusion,url -q '.[] | "\(.workflowName) \(.conclusion) \(.url)"')"
fi
echo "label OCI revision : $(docker buildx imagetools inspect "ghcr.io/luucaaas/catalog-service:${tag}" --format '{{json .Image}}' 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("linux/arm64", d).get("config", {}).get("Labels", {}).get("org.opencontainers.image.revision", "non relevé"))' 2>/dev/null || echo "non relevé")"

step "7. Événement de test de bout en bout ($(stamp))"
"${LOCAL}/publish-test-event.sh"

step "État final ($(stamp))"
$K get deploy,hpa,pods
echo "Cluster laissé complet."
