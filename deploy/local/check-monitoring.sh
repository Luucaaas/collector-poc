#!/usr/bin/env bash
# Vérifie l'observabilité du cluster `collector` (tâche P6-04) :
#   1. cibles Prometheus : les 2 réplicas des 2 services doivent être `up` ;
#   2. un peu de trafic sur les routes publiques (200 boucles de 3 requêtes) ;
#   3. chaque requête du tableau de bord est exécutée par l'API de Grafana (/api/ds/query) pour
#      chaque service : aucune ne doit renvoyer une série vide (sauf le délai des notifications, non vérifiable sans
#      notification créée ; un panneau propre à un autre service est sauté) ;
#   4. mémoire et CPU des pods (metrics-server).
# Prometheus n'est pas exposé : accès par `kubectl port-forward` (fermé en fin de script).
# Le mot de passe de Grafana est lu dans le Secret `grafana-admin`, écrit dans un fichier 600
# (format netrc, lu par curl) puis supprimé : jamais en argument ni affiché.
#
# Usage : deploy/local/check-monitoring.sh
set -euo pipefail

CTX="k3d-collector"
K="kubectl --context ${CTX} -n collector"
HERE="$(cd "$(dirname "$0")" && pwd)"
DASHBOARD="$(cd "${HERE}/../.." && pwd)/deploy/infra/monitoring/dashboards/collector-service.json"
API="https://api.127.0.0.1.sslip.io"
GRAFANA="grafana.127.0.0.1.sslip.io"
tmp="$(mktemp -d)"
pf=""
trap '[[ -z "$pf" ]] || kill "$pf" 2>/dev/null || true; rm -rf "$tmp"' EXIT
chmod 700 "$tmp"

step() { printf '\n=== %s ===\n' "$*"; }

step "1. Cibles Prometheus (port-forward 19090)"
$K port-forward svc/kps-prometheus 19090:9090 >/dev/null 2>&1 &
pf=$!
disown "$pf"   # évite le message « Terminated » du shell à la fermeture
for _ in $(seq 1 30); do curl -s -o /dev/null --max-time 2 http://127.0.0.1:19090/-/ready && break; sleep 1; done
# Juste après `deploy.sh monitoring`, Prometheus n'a pas encore chargé les ServiceMonitor : on
# réessaie jusqu'à 3 minutes avant de conclure à l'échec.
ok=0
for _ in $(seq 1 60); do
  if curl -s http://127.0.0.1:19090/api/v1/targets | python3 -c '
import json, sys
targets = [t for t in json.load(sys.stdin)["data"]["activeTargets"]
           if t["labels"].get("job") in ("catalog-service", "notification-service")]
for t in sorted(targets, key=lambda t: (t["labels"]["job"], t["labels"]["pod"])):
    print(f'"'"'{t["labels"]["job"]:22} {t["labels"]["pod"]:42} {t["health"]}'"'"')
up = [t for t in targets if t["health"] == "up"]
print(f"{len(up)} cibles up sur {len(targets)} (attendu : 4 sur 4)")
sys.exit(0 if len(targets) == 4 and len(up) == 4 else 1)' > "${tmp}/targets.txt"; then
    ok=1
    break
  fi
  sleep 3
done
cat "${tmp}/targets.txt"
[[ "$ok" == 1 ]] || { echo "Cibles Prometheus incomplètes." >&2; exit 1; }

step "2. Trafic (600 requêtes)"
for _ in $(seq 1 200); do
  curl -s -o /dev/null "${API}/catalog/api/v1/categories"
  curl -s -o /dev/null "${API}/catalog/api/v1/articles"
  curl -s -o /dev/null "${API}/notification/api/v1/me/notifications"   # 401 sans jeton : compté quand même
done
echo "Fait. Attente de deux cycles de collecte (35 s) pour que rate() ait deux points."
sleep 35

step "3. Requêtes du tableau de bord via l'API de Grafana"
( umask 077; printf 'machine %s login admin password %s\n' "$GRAFANA" \
    "$($K get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d)" > "${tmp}/netrc" )
python3 - "$DASHBOARD" "${tmp}/netrc" "$GRAFANA" <<'PY'
import json, re, subprocess, sys
dash = json.load(open(sys.argv[1]))
netrc, host = sys.argv[2], sys.argv[3]
empty = 0
for svc in ("catalog-service", "notification-service"):
    print(f"-- {svc}")
    for panel in dash["panels"]:
        # Panneau dont la requête fixe un `job` : propre à ce service, sauté pour les autres.
        fixed = {j for t in panel["targets"] for j in re.findall(r'job="([a-z-]+)"', t["expr"])}
        if fixed and svc not in fixed:
            print(f"   {panel['title'][:30]:30} | sauté : propre à {', '.join(sorted(fixed))}")
            continue
        for target in panel["targets"]:
            body = {"queries": [{"refId": "A", "datasource": {"type": "prometheus", "uid": "prometheus"},
                                 "expr": target["expr"].replace("$service", svc), "range": True,
                                 "intervalMs": 15000, "maxDataPoints": 300}],
                    "from": "now-5m", "to": "now"}
            out = subprocess.run(["curl", "-s", "--netrc-file", netrc, "-H", "Content-Type: application/json",
                                  "-d", json.dumps(body), f"https://{host}/api/ds/query"],
                                 capture_output=True, text=True).stdout
            res = json.loads(out)["results"]["A"]
            series = []
            for frame in res.get("frames", []):
                values = frame["data"]["values"]
                points = [v for v in (values[1] if len(values) > 1 else []) if v is not None and v == v]
                if points:
                    series.append(points[-1])
            if "error" not in res and not series and "notification_delay_seconds" in target["expr"]:
                # Pas d'événement ayant créé de notification depuis le démarrage : le panneau est vide
                # sans que la chaîne soit en défaut. Ce n'est pas un échec, mais ce n'est pas vérifié.
                print(f"   {panel['title'][:30]:30} | {target['legendFormat'][:32]:32} | non vérifiable : aucune notification créée depuis le démarrage (lancer les parcours Playwright ou Locust)")
                continue
            if "error" in res or not series:
                empty += 1
            shown = ", ".join(f"{v:.4g}" for v in series[:3]) or "VIDE"
            print(f"   {panel['title'][:30]:30} | {target['legendFormat'][:32]:32} | {len(series)} série(s), dernière valeur : {shown}")
sys.exit(1 if empty else 0)
PY
# Note toujours vraie, quelle que soit la valeur relevée : le p95 est interpolé entre les bornes de
# l'histogramme des services (0,05 / 0,1 / 0,2 / 0,3 / 0,5 / 1 / 2,5 s), sa précision est celle de
# ces bornes.
echo "Lecture du p95 : valeur interpolée entre les bornes de l'histogramme (0,05 / 0,1 / 0,2 / 0,3 / 0,5 / 1 / 2,5 s)."
echo "Un p95 de 0,0475 s (0,95 x 0,05) signifie que toutes les requêtes sont dans le premier intervalle (moins de 50 ms)."

step "4. Mémoire et CPU des pods (metrics-server)"
$K top pods --no-headers | sort
$K top pods --no-headers | grep -E 'kps|prometheus|grafana' | python3 -c '
import sys
mem = cpu = 0.0
for line in sys.stdin:
    p = line.split()
    cpu += float(p[1].rstrip("m"))
    mem += float(p[2][:-2]) * {"Ki": 1 / 1024, "Mi": 1, "Gi": 1024}[p[2][-2:]]
print(f"TOTAL pile d observabilité : {mem:.0f} Mi, {cpu:.0f} m CPU")'
