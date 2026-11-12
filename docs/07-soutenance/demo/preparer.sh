#!/usr/bin/env bash
# Vérification d'avant-démonstration : tout est-il prêt ? Ne modifie rien (lectures seulement).
#
#   docs/07-soutenance/demo/preparer.sh               contrôle complet (smoke.sh compris, environ 1 minute)
#   docs/07-soutenance/demo/preparer.sh --rapide      sans smoke.sh (rappel rapide, quelques secondes)
#   docs/07-soutenance/demo/preparer.sh --veille [h]  en plus, empêche la mise en veille du Mac pendant
#                                                     h heures (2 par défaut), par `caffeinate`
#
# Sortie : « PRÊT » (code 0), ou la liste de ce qui manque avec la commande qui y remédie (code 1).
# Les mots de passe sont lus dans deploy/local/.env, donnés à curl par un tube (jamais en argument,
# jamais affichés).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${HERE}/../../.." && pwd)"
ENV_FILE="${ROOT}/deploy/local/.env"
CTX="k3d-collector"
K="kubectl --context ${CTX} -n collector"
API="https://api.127.0.0.1.sslip.io"
RAPIDE=0; VEILLE=0; HEURES=2
while [[ $# -gt 0 ]]; do
  case "$1" in
    --rapide) RAPIDE=1 ;;
    --veille) VEILLE=1; if [[ "${2:-}" =~ ^[0-9]+$ ]]; then HEURES="$2"; shift; fi ;;
    *) echo "Usage : $0 [--rapide] [--veille [heures]]" >&2; exit 2 ;;
  esac
  shift
done

manques=0; alertes=0
ok() { printf 'OK      %s\n' "$1"; }
manque() { printf 'MANQUE  %s\n          -> %s\n' "$1" "$2"; manques=$((manques + 1)); }
alerte() { printf 'ATTENTION %s\n          -> %s\n' "$1" "$2"; alertes=$((alertes + 1)); }
http() { curl -s --max-time 10 -o /dev/null -w '%{http_code}' "$1" 2>/dev/null || true; }

echo "=== Avant la démonstration, $(date '+%d/%m/%Y %H:%M') ==="

# 1. Docker, ressources et disque
if docker info >/dev/null 2>&1; then
  cpu="$(docker info --format '{{.NCPU}}')"; mem="$(docker info --format '{{.MemTotal}}')"
  if [[ "$cpu" -ge 8 && "$mem" -ge 7500000000 ]]; then
    ok "Docker répond : ${cpu} CPU, $((mem / 1000000000)) Go de mémoire"
  else
    manque "Docker n'a que ${cpu} CPU et $((mem / 1000000000)) Go" "Docker Desktop > Settings > Resources : 10 CPU et 8 Go"
  fi
else
  manque "Docker ne répond pas" "ouvrir Docker Desktop et attendre qu'il soit prêt"
fi
libre="$(df -m / | awk 'NR==2 {print $4}')"
if [[ "$libre" -ge 10000 ]]; then ok "Disque : $((libre / 1000)) Go libres"
else manque "Disque : ${libre} Mo libres (moins de 10 000)" "libérer de la place (docker system prune ne doit pas toucher d'autres projets)"; fi

# 2. Cluster et nœuds
if prets="$(kubectl --context "$CTX" get nodes --no-headers 2>/dev/null | grep -c ' Ready ')" && [[ "$prets" -eq 3 ]]; then
  ok "Cluster ${CTX} : 3 nœuds Ready"
else
  manque "Cluster absent ou nœuds non prêts (${prets:-0}/3)" "docker start \$(docker ps -aq --filter name=k3d-collector) ; sinon deploy/local/cluster.sh create puis deploy.sh all <tag>"
fi

# 3. Pods, HPA, versions déployées
if $K get pods >/dev/null 2>&1; then
  mauvais="$($K get pods --no-headers | awk '$3 != "Running" && $3 != "Completed" {print $1 " (" $3 ")"}' | tr '\n' ' ')"
  [[ -z "$mauvais" ]] && ok "Aucun pod en échec" || manque "Pods en échec : ${mauvais}" "kubectl -n collector describe pod <nom> ; relancer deploy.sh services <tag>"
  nonprets="$($K get pods --no-headers | awk '$3 == "Running" {split($2, r, "/"); if (r[1] != r[2]) print $1}' | tr '\n' ' ')"
  [[ -z "$nonprets" ]] || manque "Pods pas encore prêts : ${nonprets}" "attendre une minute et relancer ce script"
  hpa_ko=""
  for name in catalog-service notification-service frontend; do
    etat="$($K get hpa "$name" -o jsonpath='{.status.currentReplicas}/{.status.desiredReplicas}' 2>/dev/null || true)"
    [[ "$etat" == "2/2" ]] || hpa_ko="${hpa_ko}${name}=${etat:-absent} "
  done
  if [[ -z "$hpa_ko" ]]; then ok "HPA des 3 composants à 2 réplicas"
  else manque "HPA pas à 2 réplicas : ${hpa_ko}" "attendre le retour à 2 (5 à 10 minutes après une charge) : kubectl -n collector get hpa -w"; fi
  tag="$($K get deploy catalog-service -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null | sed 's/@.*//; s/.*://')"
  ok "Version déployée : ${tag}"
fi

# 4. Résolution des noms par le Mac (celle qu'utilisent Chrome et Safari, pas celle de curl).
# Un réseau à DNS64 (partage de connexion d'un iPhone, certains Wi-Fi) répond aussi une adresse IPv6
# de passerelle (64:ff9b::7f00:1) que le navigateur essaie en premier : connexion coupée
# (ERR_CONNECTION_RESET) alors que curl et smoke.sh passent. Sans Internet, sslip.io ne répond pas.
# Parade : déclarer les 4 hôtes dans /etc/hosts (127.0.0.1 et ::1, le cluster écoute sur les deux).
HOTES="app.127.0.0.1.sslip.io api.127.0.0.1.sslip.io auth.127.0.0.1.sslip.io grafana.127.0.0.1.sslip.io"
REMEDE_HOSTS="sudo sh -c 'printf \"127.0.0.1 ${HOTES}\\n::1 ${HOTES}\\n\" >> /etc/hosts' (par toi, mot de passe demandé)"
HOSTS_FILE="${HOSTS_FILE:-/etc/hosts}"
# declare_dans_hosts <ip> <nom> : vrai si une ligne non commentée associe ce nom à cette adresse.
declare_dans_hosts() {
  awk -v ip="$1" -v nom="$2" '{ sub(/#.*/, "") } $1 == ip { for (i = 2; i <= NF; i++) if ($i == nom) t = 1 }
    END { exit !t }' "$HOSTS_FILE" 2>/dev/null
}
declares=0; mauvais_noms=""
for h in $HOTES; do
  declare_dans_hosts 127.0.0.1 "$h" && declare_dans_hosts ::1 "$h" && declares=$((declares + 1))
  adresses="$(dscacheutil -q host -a name "$h" 2>/dev/null | awk '/^ip(v6)?_address:/ {print $2}' | sort -u | tr '\n' ' ')"
  autres="$(tr ' ' '\n' <<< "$adresses" | grep -vE '^(127\.0\.0\.1|::1)?$' | tr '\n' ' ' || true)"
  if [[ -z "${adresses// /}" ]]; then mauvais_noms="${mauvais_noms}${h} (non résolu) "
  elif [[ -n "${autres// /}" ]]; then mauvais_noms="${mauvais_noms}${h} (aussi ${autres% }) "; fi
done
if [[ -n "$mauvais_noms" ]]; then
  manque "Le navigateur ne joindra pas le cluster : ${mauvais_noms}" "$REMEDE_HOSTS"
elif [[ $declares -eq 4 ]]; then
  ok "Les 4 hôtes sont déclarés dans /etc/hosts : la démo ne dépend ni du réseau ni d'Internet"
else
  alerte "Hôtes résolus par sslip.io : il faut Internet et un réseau sans DNS64" "$REMEDE_HOSTS"
fi

# 5. Test de fumée, Grafana, Keycloak, application
if [[ $RAPIDE -eq 1 ]]; then
  alerte "smoke.sh sauté (--rapide)" "lancer deploy/local/smoke.sh"
else
  if sortie="$("${ROOT}/deploy/local/smoke.sh" 2>&1)"; then
    ok "smoke.sh : $(grep -c '^OK' <<< "$sortie") contrôles verts"
  else
    manque "smoke.sh échoue ($(grep -c '^ECHEC' <<< "$sortie") contrôle(s))" "deploy/local/smoke.sh pour le détail"
  fi
fi
[[ "$(http https://auth.127.0.0.1.sslip.io/realms/collector/.well-known/openid-configuration)" == 200 ]] \
  && ok "Keycloak joignable (https://auth.127.0.0.1.sslip.io)" \
  || manque "Keycloak ne répond pas" "kubectl -n collector get pods -l app=keycloak ; attendre qu'il soit prêt"
[[ "$(http https://app.127.0.0.1.sslip.io/)" == 200 ]] \
  && ok "Application joignable (https://app.127.0.0.1.sslip.io), certificat reconnu" \
  || manque "L'application ne répond pas (ou certificat non reconnu)" "mkcert -install (à faire par toi, mot de passe demandé) ; deploy/local/smoke.sh"
[[ "$(http https://grafana.127.0.0.1.sslip.io/login)" == 200 ]] \
  && ok "Grafana joignable (https://grafana.127.0.0.1.sslip.io)" \
  || manque "Grafana ne répond pas" "deploy/local/deploy.sh monitoring"

# 6. Mots de passe : présents, et celui de Grafana accepté (sans l'afficher)
if [[ -f "$ENV_FILE" ]]; then
  absents=""
  for cle in ADMIN_PASSWORD ALICE_PASSWORD BOB_PASSWORD CHLOE_PASSWORD GRAFANA_ADMIN_PASSWORD; do
    grep -qE "^${cle}=.+" "$ENV_FILE" || absents="${absents}${cle} "
  done
  [[ -z "$absents" ]] && ok "Mots de passe de démo présents dans deploy/local/.env" \
    || manque "Mots de passe absents : ${absents}" "deploy/local/deploy.sh infra (les génère)"
  gpw="$(grep -m1 -E '^GRAFANA_ADMIN_PASSWORD=' "$ENV_FILE" | cut -d= -f2- || true)"
  if [[ -n "$gpw" ]]; then
    code="$(printf 'user = "admin:%s"\n' "$gpw" | curl -s --max-time 10 -o /dev/null -w '%{http_code}' -K - https://grafana.127.0.0.1.sslip.io/api/org 2>/dev/null || true)"
    [[ "$code" == 200 ]] && ok "Mot de passe de Grafana accepté (mot-de-passe.sh grafana le copie)" \
      || manque "Grafana refuse le mot de passe du .env (HTTP ${code})" "deploy/local/deploy.sh monitoring (réaligne le mot de passe)"
  fi
else
  manque "deploy/local/.env introuvable" "deploy/local/deploy.sh infra"
fi

# 7. Outils : Locust (uv), Chromium de Playwright, autorité mkcert
if [[ -x "${ROOT}/tests/load/.venv/bin/locust" ]]; then ok "Environnement uv de tests/load : Locust présent"
else manque "Locust absent" "cd tests/load && uv sync"; fi
if [[ -x "${ROOT}/frontend/node_modules/.bin/playwright" ]] && ls -d "${HOME}"/Library/Caches/ms-playwright/chromium-* >/dev/null 2>&1; then
  ok "Playwright et son Chromium présents"
else manque "Playwright ou Chromium absent" "cd frontend && npm ci && npx playwright install chromium"; fi
[[ -f "$(mkcert -CAROOT 2>/dev/null)/rootCA.pem" ]] && ok "Autorité mkcert présente" || manque "Autorité mkcert absente" "mkcert -install (par toi)"

# 8. Catalogue propre : seulement le jeu de la démo
cats="$(curl -s --max-time 10 "${API}/catalog/api/v1/categories" 2>/dev/null | python3 -c '
import json, sys
try:
    print("|".join(sorted(c["name"] for c in json.load(sys.stdin)["items"])))
except Exception:
    print("?")' || true)"
attendu="Cartes à collectionner|Figurines|Jeux vidéo rétro|Monnaies et timbres|Vinyles"
if [[ "$cats" == "$attendu" ]]; then
  total="$(curl -s --max-time 10 "${API}/catalog/api/v1/articles?limit=1" | python3 -c 'import json,sys; print(json.load(sys.stdin)["total"])' 2>/dev/null || echo 0)"
  [[ "$total" -ge 11 ]] && ok "Catalogue propre : 5 catégories de démo, ${total} articles" \
    || manque "Catalogue incomplet (${total} articles)" "docs/07-soutenance/demo/donnees-demo.sh"
elif [[ "$cats" == "" ]]; then
  manque "Catalogue vide" "docs/07-soutenance/demo/donnees-demo.sh"
else
  manque "Le catalogue contient autre chose que le jeu de la démo" "refaire un cluster neuf puis donnees-demo.sh (script-demo.md, « La veille »)"
fi

# 9. Dernier run de la CI sur main
if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
  for wf in backend frontend; do
    ligne="$(gh run list --workflow "${wf}.yml" --branch main --limit 1 --json status,conclusion,headSha --jq '.[0] | "\(.status) \(.conclusion) \(.headSha[0:7])"' 2>/dev/null || true)"
    case "$ligne" in
      "completed success "*) ok "CI ${wf} sur main : verte (commit ${ligne##* })" ;;
      "completed "*) manque "CI ${wf} sur main : ${ligne}" "gh run list --workflow ${wf}.yml --branch main ; lancer 'gh run view --log-failed'" ;;
      "") alerte "CI ${wf} : état illisible" "gh auth status" ;;
      *) alerte "CI ${wf} sur main : en cours (${ligne})" "attendre la fin du run avant de lancer la démo" ;;
    esac
  done
else
  alerte "gh absent ou non connecté : état de la CI non vérifié" "gh auth login (par toi)"
fi

# 10. Mise en veille
if [[ $VEILLE -eq 1 ]]; then
  caffeinate -dis -t $((HEURES * 3600)) >/dev/null 2>&1 &
  echo "Veille empêchée pendant ${HEURES} h (caffeinate, processus $!). Pour l'arrêter : kill $!"
  disown $!
fi

echo
if [[ $manques -eq 0 ]]; then
  [[ $alertes -eq 0 ]] && echo "PRÊT : tout est vert." || echo "PRÊT, avec ${alertes} point(s) d'attention ci-dessus."
else
  echo "PAS PRÊT : ${manques} point(s) à corriger (commande indiquée sous chaque MANQUE)."
  exit 1
fi
