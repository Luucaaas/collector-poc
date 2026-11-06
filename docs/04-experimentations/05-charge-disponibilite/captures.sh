#!/usr/bin/env bash
# Captures du tableau de bord Grafana « Collector - service » pour une exécution du protocole 5.
#
#   docs/04-experimentations/05-charge-disponibilite/captures.sh <dossier de résultats> [<motif>]
#
# Le motif (facultatif) ne garde que les captures dont le nom de fichier le contient, pour reprendre
# celles qui manquent : Grafana peut être tué par manque de mémoire (limite de 384 Mi) pendant une
# série de captures (voir protocole.md, difficultés).
#
# Lancé par run.sh (CAPTURES=1) ou à part, sur un dossier de résultats existant : Prometheus ne
# garde que 2 h de mesures, il faut donc le lancer dans les 2 h qui suivent l'exécution.
# Écrit dans le dossier de résultats 4 PNG : grafana-pic-<service>.png (de 1 min avant le pic à
# 15 s après l'arrêt de la charge) et grafana-retour-<service>.png (de 1 min avant la charge à
# 30 s après le retour à 2 réplicas), pour catalog-service et notification-service.
# Le mot de passe de Grafana est lu dans deploy/local/.env et donné au seul processus Playwright en
# préfixe de commande (jamais affiché, jamais en argument, jamais écrit) ; la spécification le pose
# dans le champ par `evaluate` et ne photographie jamais la page de connexion.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${HERE}/../../.." && pwd)"
RESULTS="${1:?usage : captures.sh <dossier de résultats> [<motif>]}"
PATTERN="${2:-}"
ENV_FILE="${ROOT}/deploy/local/.env"
[[ -f "${RESULTS}/fenetre.json" && -f "${RESULTS}/chronologie.tsv" ]] \
  || { echo "${RESULTS} ne contient pas fenetre.json et chronologie.tsv." >&2; exit 1; }
RESULTS="$(cd "$RESULTS" && pwd)"
grafana_pw="$(grep -E '^GRAFANA_ADMIN_PASSWORD=' "$ENV_FILE" | head -1 | cut -d= -f2- | grep .)" \
  || { echo "Clé GRAFANA_ADMIN_PASSWORD absente ou vide dans deploy/local/.env." >&2; exit 1; }

plan="$(python3 - "$RESULTS" "$PATTERN" <<'PY'
import json, sys
d, pattern = sys.argv[1], sys.argv[2]
w = json.load(open(f"{d}/fenetre.json"))
ev = {}
for line in open(f"{d}/chronologie.tsv"):
    t, n, *_ = line.rstrip("\n").split("\t")
    ev[n] = float(t)
ms = lambda s: int(s * 1000)
peak_from, peak_to = ms(w["peak_start"] - 60), ms(ev["stop"] + 15)
full_from = ms(w["nominal_start"] - 60)
full_to = ms(ev.get("observation_end", ev["stop"]) + 30)
plan = []
for svc in ("catalog-service", "notification-service"):
    plan.append({"file": f"{d}/grafana-pic-{svc}.png", "service": svc, "from": peak_from, "to": peak_to})
    plan.append({"file": f"{d}/grafana-retour-{svc}.png", "service": svc, "from": full_from, "to": full_to})
print(json.dumps([c for c in plan if pattern in c["file"]]))
PY
)"
cd "${ROOT}/frontend"
E2E_BASE_URL="https://app.127.0.0.1.sslip.io" GRAFANA_CAPTURES=1 \
  GRAFANA_PASSWORD="$grafana_pw" GRAFANA_CAPTURE_PLAN="$plan" npx playwright test
