#!/usr/bin/env bash
# Expérimentation 3 : observabilité avec kube-prometheus-stack sur k3d (voir protocole.md).
# Crée le cluster, installe la pile allégée, déploie une application FastAPI instrumentée,
# envoie une charge connue (vérité terrain), compare les mesures de Prometheus aux valeurs
# injectées, vérifie Grafana, relève la mémoire de la pile, puis supprime le cluster.
# Usage : ./run.sh [--keep]   (--keep conserve le cluster à la fin)
# La sortie complète est aussi écrite dans resultats/run-AAAAMMJJ-HHMM.log.
set -euo pipefail

# --- Versions figées -------------------------------------------------------------------
K3S_IMAGE="rancher/k3s:v1.35.8-k3s1"
STACK_CHART="oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack"
STACK_VERSION="91.9.0"   # publié le 02/10/2026 ; Prometheus 3.15.0, Grafana 13.2.3, opérateur 0.94.1
ALPINE_IMAGE="alpine:3.24.3"   # image utilitaire : mesure de l'espace disque de la VM Docker
APP_IMAGE="exp-observabilite-app:local"   # FastAPI 0.142.2, instrumentator 8.1.0, structlog 26.1.0,
                                          # httpx 0.28.1, uvicorn 0.52.4 (voir app/uv.lock)

# --- Paramètres ------------------------------------------------------------------------
CLUSTER="collector-exp3"
NS_APP="exp"
NS_MON="monitoring"
TOTAL=3000     # requêtes de la charge
RATE=20        # requêtes par seconde (durée : TOTAL / RATE = 150 s)
KEEP=false
[[ "${1:-}" == "--keep" ]] && KEEP=true

cd "$(dirname "$0")"
MIN_FREE_MB=7000   # l'exécution consomme environ 3,6 Go et le kubelet évince sous environ 3,1 Go libres

# Journalise toute la sortie (sans codes de couleur) dans resultats/ : le script se relance
# lui-même à travers `tee`.
if [[ -z "${EXP_LOGGING:-}" ]]; then
  export EXP_LOGGING=1
  mkdir -p resultats
  LOG="resultats/run-$(date +%Y%m%d-%H%M).log"
  echo "Journal complet : ${LOG}"
  ./run.sh "$@" 2>&1 | perl -pe 'BEGIN{$|=1} s/\e\[[0-9;]*m//g' | tee "$LOG"
  exit "${PIPESTATUS[0]}"
fi
K="kubectl --context k3d-${CLUSTER}"
WORK=$(mktemp -d)
PF_PIDS=()
PROM_URL="http://127.0.0.1:19090"
GRAFANA_URL="http://127.0.0.1:13000"
APP_URL="http://127.0.0.1:18000"

step() { printf '\n=== %s ===\n' "$*"; }
disk() { echo "Espace disque libre de la VM Docker ($1) : $(docker run --rm "$ALPINE_IMAGE" df -h / | awk 'NR==2 {print $4 " sur " $2 " (" $5 " utilisé)"}')"; }
now() { python3 -c 'import time; print(f"{time.time():.3f}")'; }

cleanup() {
  local rc=$?   # code de sortie du script, relevé avant toute autre commande
  for pid in "${PF_PIDS[@]:-}"; do [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true; done
  rm -rf "$WORK"
  if [[ "$KEEP" == true ]]; then
    echo "Cluster conservé (--keep) : k3d cluster delete ${CLUSTER} pour le supprimer."
  else
    step "Suppression du cluster"
    k3d cluster delete "$CLUSTER" || true
    disk "après suppression du cluster"
    echo "--- k3d cluster list (après suppression) ---"
    k3d cluster list || true
  fi
  echo "Code de sortie de run.sh : ${rc}"
}
trap cleanup EXIT

# Ouvre (ou rouvre si elle est tombée) une redirection de port. $1 espace de noms, $2 service,
# $3 port local, $4 port du service, $5 chemin de test.
forward() {
  if curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$3$5"; then return 0; fi
  $K -n "$1" port-forward "svc/$2" "$3:$4" >/dev/null 2>&1 &
  PF_PIDS+=("$!")
  disown "$!"
  for _ in $(seq 1 60); do
    curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$3$5" && return 0
    sleep 0.5
  done
  echo "Redirection de port vers $2 impossible" >&2
  return 1
}

# Relève mémoire et CPU de chaque pod (metrics-server de k3s). $1 libellé.
top_all() {
  echo "--- Mémoire et CPU des pods ($1) ---"
  local out=""
  for _ in $(seq 1 60); do
    out=$($K top pods -n "$NS_MON" --no-headers 2>/dev/null || true)
    [[ -n "$out" ]] && break
    sleep 2
  done
  echo "Espace de noms ${NS_MON} :"
  echo "$out"
  echo "Espace de noms ${NS_APP} :"
  $K top pods -n "$NS_APP" --no-headers 2>/dev/null || true
  echo "$out" | python3 -c '
import sys
mem = cpu = 0.0
for line in sys.stdin:
    p = line.split()
    if len(p) < 3:
        continue
    cpu += float(p[1].rstrip("m"))
    value = float(p[2][:-2])
    unit = p[2][-2:]
    mem += value * {"Ki": 1 / 1024, "Mi": 1, "Gi": 1024}[unit]
print(f"TOTAL pile ({sys.argv[1]}) : {mem:.0f} Mi, {cpu:.0f} m CPU")' "$1"
}

# --- 0. Pré-requis et environnement ---------------------------------------------------------
step "0. Pré-requis et environnement"
for tool in docker k3d kubectl helm uv python3 perl curl; do
  command -v "$tool" >/dev/null || { echo "Outil manquant : $tool" >&2; exit 1; }
done
docker info >/dev/null
date "+Date de l'exécution : %d/%m/%Y %H:%M"
echo "macOS $(sw_vers -productVersion) $(uname -m) ; Python hôte $(python3 --version | cut -d' ' -f2) ; $(uv --version | cut -d' ' -f1-2)"
echo "Docker moteur $(docker version --format '{{.Server.Version}}') ; $(docker info --format '{{.NCPU}} CPU, {{.MemTotal}} octets de mémoire')"
k3d version | head -1
kubectl version --client | head -1
echo "Helm $(helm version --short)"
echo "Chart ${STACK_CHART} version ${STACK_VERSION}"
FREE_MB=$(docker run --rm "$ALPINE_IMAGE" df -m / | awk 'NR==2 {print $4}')
disk "avant"
if [[ "$FREE_MB" -lt "$MIN_FREE_MB" ]]; then
  echo "Espace disque insuffisant : ${FREE_MB} Mo libres, ${MIN_FREE_MB} Mo requis" >&2
  exit 1
fi

step "1. Cluster k3d (1 server, 2 agents)"
k3d cluster delete "$CLUSTER" >/dev/null 2>&1 || true
k3d cluster create "$CLUSTER" --servers 1 --agents 2 --image "$K3S_IMAGE" \
  --k3s-arg "--disable=traefik@server:0" --wait --timeout 600s
$K get nodes -o wide

step "2. Image de l'application"
docker build -q -t "$APP_IMAGE" app
k3d image import "$APP_IMAGE" -c "$CLUSTER"

step "3. kube-prometheus-stack ${STACK_VERSION} (valeurs allégées)"
helm --kube-context "k3d-${CLUSTER}" upgrade --install kps "$STACK_CHART" --version "$STACK_VERSION" \
  --namespace "$NS_MON" --create-namespace -f values/kube-prometheus-stack.yaml --wait --timeout 10m
for _ in $(seq 1 90); do
  $K -n "$NS_MON" get pod prometheus-kps-prometheus-0 >/dev/null 2>&1 && break
  sleep 2
done
$K -n "$NS_MON" wait --for=condition=Ready pod/prometheus-kps-prometheus-0 --timeout=300s
$K -n "$NS_MON" get pods -o wide
echo "--- Images de la pile ---"
$K -n "$NS_MON" get pods -o jsonpath='{range .items[*].spec.containers[*]}{.image}{"\n"}{end}' | sort -u
disk "après téléchargement de la pile"

step "4. Application de test, ServiceMonitor et tableau de bord"
$K apply -f manifests/app.yaml
$K -n "$NS_APP" rollout status deployment/exp-app --timeout=180s
$K apply -f manifests/servicemonitor.yaml
# Le tableau de bord versionné est publié dans une ConfigMap que le sidecar de Grafana charge.
$K -n "$NS_MON" create configmap exp-dashboard --from-file=dashboards/collector-service.json \
  --dry-run=client -o yaml | $K apply -f -
$K -n "$NS_MON" label configmap exp-dashboard grafana_dashboard=1 --overwrite

step "5. Collecte : attente de la cible Prometheus"
forward "$NS_MON" kps-prometheus 19090 9090 /-/ready
UP=""
for _ in $(seq 1 120); do
  UP=$(curl -s --max-time 5 --get "${PROM_URL}/api/v1/query" --data-urlencode 'query=up{job="exp-app"}' |
    python3 -c 'import json,sys; r=json.load(sys.stdin)["data"]["result"]; print(r[0]["value"][1] if r else "")' || true)
  [[ "$UP" == "1" ]] && break
  sleep 2
done
echo "up{job=\"exp-app\"} = ${UP:-absente}"
[[ "$UP" == "1" ]] || { echo "La cible exp-app n'est pas collectée" >&2; exit 1; }
sleep 30   # laisse metrics-server relever la pile au repos
top_all "au repos, avant la charge"

# --- Mesure 4 : délai de collecte -------------------------------------------------------------
step "Mesure 4 : délai entre une requête et sa visibilité dans Prometheus (5 essais)"
forward "$NS_APP" exp-app 18000 8000 /health/live
PROM_URL="$PROM_URL" APP_URL="$APP_URL" python3 - <<'PY'
import json
import os
import time
import urllib.parse
import urllib.request

prom, app = os.environ["PROM_URL"], os.environ["APP_URL"]
query = 'sum(http_requests_total{job="exp-app",handler="/items"})'


def value() -> float:
    url = f"{prom}/api/v1/query?" + urllib.parse.urlencode({"query": query})
    result = json.load(urllib.request.urlopen(url, timeout=10))["data"]["result"]
    return float(result[0]["value"][1]) if result else 0.0


baseline = value()
pauses = [3.1, 7.7, 1.9, 11.3, 0.0]
delays = []
for i in range(1, 6):
    t0 = time.time()
    urllib.request.urlopen(app + "/items", timeout=10).read()
    while value() <= baseline:
        time.sleep(0.25)
        if time.time() - t0 > 60:
            raise SystemExit("requête jamais visible dans Prometheus")
    delays.append(time.time() - t0)
    baseline = value()
    print(f"Essai {i} : visible après {delays[-1]:.2f} s")
    # Pauses inégales : sans elles, des essais espacés d'environ 15 s retomberaient chaque fois
    # au même point du cycle de collecte (constaté à une première exécution).
    time.sleep(pauses[i - 1])
print(f"DELAI min {min(delays):.2f} s, moyenne {sum(delays) / len(delays):.2f} s, "
      f"max {max(delays):.2f} s (intervalle du ServiceMonitor : 15 s)")
PY

# --- Charge connue ------------------------------------------------------------------------
step "6. Charge : ${TOTAL} requêtes à ${RATE} par seconde (85 % /items, 10 % /slow, 5 % /fail)"
$K -n "$NS_APP" delete job loadgen --ignore-not-found >/dev/null
sed -e "s|__NAME__|loadgen|" \
  -e "s|__COMMAND__|[\"python\",\"-m\",\"exp.loadgen\",\"--url\",\"http://exp-app.${NS_APP}.svc:8000\",\"--total\",\"${TOTAL}\",\"--rate\",\"${RATE}\"]|" \
  manifests/job.yaml.tmpl | $K apply -f - >/dev/null
$K -n "$NS_APP" wait --for=condition=complete job/loadgen --timeout=400s >/dev/null
LOAD_RESULT=$($K -n "$NS_APP" logs job/loadgen | sed -n 's/^RESULT //p')
echo "$LOAD_RESULT"
echo "Attente de trois cycles de collecte (45 s) après la fin de la charge..."
sleep 45
top_all "juste après la charge"

# --- Grafana --------------------------------------------------------------------------------
step "7. Grafana : santé, source de données, tableau de bord chargé par le sidecar"
forward "$NS_MON" kps-grafana 13000 80 /api/health
GRAFANA_PASSWORD=$($K -n "$NS_MON" get secret kps-grafana -o jsonpath='{.data.admin-password}' | base64 -d) \
  GRAFANA_URL="$GRAFANA_URL" EXPRS_FILE="$WORK/exprs.json" python3 - <<'PY'
import base64
import json
import os
import time
import urllib.parse
import urllib.request

base = os.environ["GRAFANA_URL"]
auth = "Basic " + base64.b64encode(f"admin:{os.environ['GRAFANA_PASSWORD']}".encode()).decode()


def get(path: str) -> object:
    request = urllib.request.Request(base + path, headers={"Authorization": auth})
    return json.load(urllib.request.urlopen(request, timeout=15))


print("GET /api/health :", json.dumps(get("/api/health")))
health = get("/api/datasources/uid/prometheus/health")
print("Source de données Prometheus (uid prometheus) :", json.dumps(health))
found = []
for _ in range(60):  # le sidecar recopie la ConfigMap dans Grafana en quelques secondes
    found = get("/api/search?" + urllib.parse.urlencode({"query": "Collector"}))
    if found:
        break
    time.sleep(2)
print("GET /api/search?query=Collector :", json.dumps(found, ensure_ascii=False))
dash = get("/api/dashboards/uid/collector-service")["dashboard"]
exprs = {}
for panel in dash["panels"]:
    print(f"Panneau {panel['id']} « {panel['title']} » :")
    for target in panel["targets"]:
        print(f"  [{target['refId']}] {target['expr']}")
        exprs[f"{panel['id']}{target['refId']}"] = target["expr"]
json.dump(exprs, open(os.environ["EXPRS_FILE"], "w"))
assert health["status"] == "OK" and found and len(dash["panels"]) == 5
print("GRAFANA OK : source de données saine, tableau de bord chargé, 5 panneaux")
PY

# --- Mesures 1 à 3 : Prometheus contre la vérité terrain ------------------------------------
step "Mesures 1 à 3 : Prometheus contre les valeurs injectées (requêtes lues dans Grafana)"
forward "$NS_MON" kps-prometheus 19090 9090 /-/ready
LOAD_RESULT="$LOAD_RESULT" PROM_URL="$PROM_URL" EXPRS_FILE="$WORK/exprs.json" TOTAL="$TOTAL" RATE="$RATE" \
  python3 - <<'PY'
import json
import os
import urllib.parse
import urllib.request

prom = os.environ["PROM_URL"]
load = json.loads(os.environ["LOAD_RESULT"])
exprs = json.load(open(os.environ["EXPRS_FILE"]))
total, rate = int(os.environ["TOTAL"]), float(os.environ["RATE"])


def query(expr: str, at: float | None = None) -> list[dict[str, object]]:
    params = {"query": expr}
    if at is not None:
        params["time"] = f"{at:.3f}"
    url = f"{prom}/api/v1/query?" + urllib.parse.urlencode(params)
    return json.load(urllib.request.urlopen(url, timeout=15))["data"]["result"]  # type: ignore[no-any-return]


def scalar(expr: str, at: float) -> float:
    return float(query(expr, at)[0]["value"][1])  # type: ignore[index]


end = load["end_ts"]
print(f"Charge : début {load['start_ts']}, fin {end} (horloge du cluster), "
      f"durée {end - load['start_ts']:.1f} s")
print("Requêtes envoyées :", json.dumps(load["statuses"]))

# Compteurs exacts : 5 requêtes /items de la mesure 4 s'ajoutent à la charge.
sent: dict[str, int] = {}
for key, count in load["statuses"].items():
    path = key.split()[0]
    sent[path] = sent.get(path, 0) + count
sent["/items"] += 5
print()
print(f"{'Compteur http_requests_total':<34}{'Envoyé':>10}{'Prometheus':>12}{'Écart':>8}")
for row in query('sum by (handler) (http_requests_total{job="exp-app"})'):
    handler = row["metric"]["handler"]  # type: ignore[index]
    seen = float(row["value"][1])  # type: ignore[index]
    print(f"{handler:<34}{sent[handler]:>10}{seen:>12.0f}{seen - sent[handler]:>+8.0f}")

print()
print(f"Instants évalués : fin de la charge ({end}), fenêtre de 1 minute.")
rows = []
inj_rate = rate
got = scalar(exprs["1A"], end)
rows.append(("1. Débit (req/s)", f"{inj_rate:.2f}", f"{got:.3f}", f"{got - inj_rate:+.3f}",
             f"{(got - inj_rate) / inj_rate * 100:+.1f} %"))
inj_err = load["statuses"].get("/fail 500", 0) / total
got = scalar(exprs["2A"], end)
rows.append(("2. Taux d'erreur 5xx", f"{inj_err * 100:.2f} %", f"{got * 100:.3f} %",
             f"{(got - inj_err) * 100:+.3f} pt", f"{(got - inj_err) / inj_err * 100:+.1f} %"))
slow_s = 0.2
client = load["client_p95_s"]
for label, key, ref in (
    ("3a. p95 /slow, bornes serrées (B)", "3B", slow_s),
    ("3b. p95 /slow, bornes par défaut (C)", "3C", slow_s),
    ("3c. p95 toutes routes, bornes serrées (A)", "3A", slow_s),
):
    got = scalar(exprs[key], end)
    rows.append((label, f"{ref:.3f} s", f"{got:.4f} s", f"{got - ref:+.4f} s",
                 f"{(got - ref) / ref * 100:+.1f} %"))
print(f"{'Mesure':<44}{'Injecté':>12}{'Prometheus':>14}{'Écart':>13}{'Écart relatif':>15}")
for r in rows:
    print(f"{r[0]:<44}{r[1]:>12}{r[2]:>14}{r[3]:>13}{r[4]:>15}")
print()
print("Panneaux d'infrastructure (requêtes lues dans Grafana, évaluées à la fin de la charge) :")
for key, label in (("4A", "Réplicas du Deployment exp-app"), ("5A", "CPU par pod (cœurs)")):
    result = query(exprs[key], end)
    if not result:
        raise SystemExit(f"La requête du panneau {key[0]} ne renvoie aucune valeur")
    for row in result:
        print(f"  {label} : {row['value'][1]}  {row['metric']}")  # type: ignore[index]
print()
print("Latence p95 mesurée côté client (httpx, générateur de charge) :",
      json.dumps(client))
PY

# --- Journaux JSON corrélés (contrats.md §1) -------------------------------------------------
step "8. Journaux JSON et X-Request-ID"
forward "$NS_APP" exp-app 18000 8000 /health/live
curl -s -D - -o /dev/null -H 'X-Request-ID: exp3-corr-check' "${APP_URL}/items" | grep -i '^x-request-id'
sleep 1
$K -n "$NS_APP" logs deploy/exp-app | grep 'exp3-corr-check'
echo "--- Dernière ligne de journal de la charge ---"
$K -n "$NS_APP" logs deploy/exp-app | grep -v exp3-corr-check | tail -n 1

# --- Synthèse -------------------------------------------------------------------------------
step "Synthèse"
disk "fin des mesures"
echo "--- kubectl top nodes ---"
$K top nodes || true
