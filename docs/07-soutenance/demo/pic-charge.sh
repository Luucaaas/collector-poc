#!/usr/bin/env bash
# Pic de charge en direct (moins de 2 minutes) : version courte et visuelle du protocole 5
# (docs/04-experimentations/05-charge-disponibilite). À regarder dans le terminal :
#
#   docs/07-soutenance/demo/pic-charge.sh
#
# Déroulé :
#   1. Locust (tests/load, profil « peak ») envoie un pic de 300 utilisateurs simulés tout de suite
#      (pas de charge de référence avant : le protocole 5 l'a déjà mesurée) ;
#   2. l'écran se rafraîchit toutes les 2 s : HPA, pods de catalog-service, requêtes et échecs ;
#   3. quand les 5 réplicas sont prêts (ou au bout de 75 s), un pod de catalog-service est supprimé
#      après quelques secondes : automatiquement, ou tout de suite si tu appuies sur la touche « s » ;
#   4. le remplacement est chronométré, la charge continue 10 s, puis s'arrête ;
#   5. bilan : réplicas atteints, délai de remplacement, requêtes, échecs.
# Le retour à 2 réplicas se fait ensuite seul (fenêtre de stabilisation de l'HPA : 5 à 10 minutes mesurées) :
# il n'est pas attendu ici.
#
# Variables facultatives (valeurs par défaut entre parenthèses) :
#   PEAK_USERS (300) PEAK_RATE (20)   utilisateurs simulés, arrivée par seconde (300 et non 200 : le pic de 200
#                                     du protocole 5 suit 4 minutes de charge de référence ; ici le pic démarre
#                                     à froid, 300 fait atteindre les 5 réplicas de façon plus régulière)
#   AFTER_FIVE (12)                   secondes d'attente à 5 réplicas avant la suppression automatique
#   MAX_WAIT (75)                     attente maximale des 5 réplicas, puis suppression quand même
#   AFTER_DELETE (10)                 secondes de charge maintenues après le retour des réplicas
#   AUTO (1)                          0 : supprime seulement sur la touche « s »
#
# Sur le cluster, ce script ne fait que du trafic HTTP, des lectures (kubectl get) et UNE
# modification : `kubectl delete pod` sur un pod de catalog-service. Il refuse de démarrer si
# catalog-service n'est pas à 2 réplicas prêts. Les mots de passe sont lus dans deploy/local/.env et
# donnés au seul processus Locust (jamais affichés, jamais en argument, jamais écrits).
# Si tu interromps (Ctrl+C), Locust est arrêté proprement.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${HERE}/../../.." && pwd)"
LOAD="${ROOT}/tests/load"
ENV_FILE="${ROOT}/deploy/local/.env"
CTX="k3d-collector"
K="kubectl --context ${CTX} -n collector"
API="https://api.127.0.0.1.sslip.io"
LABEL="app.kubernetes.io/name=catalog-service"
PEAK_USERS="${PEAK_USERS:-300}"
PEAK_RATE="${PEAK_RATE:-20}"
AFTER_FIVE="${AFTER_FIVE:-12}"
MAX_WAIT="${MAX_WAIT:-75}"
AFTER_DELETE="${AFTER_DELETE:-10}"
AUTO="${AUTO:-1}"

now() { perl -MTime::HiRes=time -e 'printf "%.3f\n", time'; }
read_var() {
  grep -m1 -E "^$1=" "$ENV_FILE" | cut -d= -f2- | grep . \
    || { echo "Clé $1 absente ou vide dans deploy/local/.env." >&2; return 1; }
}
ready_count() { $K get deploy catalog-service -o jsonpath='{.status.readyReplicas}' 2>/dev/null || true; }

command -v uv >/dev/null || { echo "uv est requis (brew install uv)." >&2; exit 1; }
command -v mkcert >/dev/null || { echo "mkcert est requis." >&2; exit 1; }
[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env introuvable : le cluster est-il déployé ?" >&2; exit 1; }
admin_pw="$(read_var ADMIN_PASSWORD)"; alice_pw="$(read_var ALICE_PASSWORD)"
bob_pw="$(read_var BOB_PASSWORD)"; chloe_pw="$(read_var CHLOE_PASSWORD)"
REQUESTS_CA_BUNDLE="$(mkcert -CAROOT)/rootCA.pem"
[[ -f "$REQUESTS_CA_BUNDLE" ]] || { echo "Autorité mkcert introuvable (mkcert -install fait ?)." >&2; exit 1; }
export REQUESTS_CA_BUNDLE

[[ "$(ready_count)" == 2 ]] || { echo "catalog-service n'est pas à 2 réplicas prêts : attendre le retour au repos (preparer.sh --rapide)." >&2; exit 1; }

WORK="$(mktemp -d)"
LOG="${WORK}/requetes.csv"
STOP="${WORK}/arret"
locust_pid=""
tty_mode=0; [[ -t 1 ]] && tty_mode=1
cleanup() {
  if [[ -n "$locust_pid" ]] && kill -0 "$locust_pid" 2>/dev/null; then
    : > "$STOP"; sleep 3; kill "$locust_pid" 2>/dev/null || true
  fi
  [[ -t 0 ]] && stty echo 2>/dev/null || true
  rm -rf "$WORK"
}
trap cleanup EXIT
trap 'echo; echo "Interrompu : arrêt de Locust."; exit 130' INT TERM

# Nombre de requêtes et d'échecs de la charge (les lignes « [connexion] » et « [prépa] » sont exclues).
counts() {
  awk -F, 'NR > 1 && $2 !~ /^\[/ {n++; f += $5} END {printf "%d %d", n, f}' "$LOG" 2>/dev/null || printf '0 0'
}

# Affiche l'écran de suivi.
screen() {   # $1 : message de la ligne d'état
  local elapsed total failed
  elapsed="$(python3 -c "print(int($(now) - $t_start))")"
  read -r total failed <<< "$(counts)"
  [[ $tty_mode -eq 1 ]] && printf '\033[H\033[2J'
  echo "PIC DE CHARGE : ${PEAK_USERS} utilisateurs simulés, t = ${elapsed} s"
  echo "Requêtes envoyées : ${total}    échecs : ${failed}"
  echo
  $K get hpa catalog-service || true
  echo
  $K get pods -l "$LABEL" || true
  echo
  echo "$1"
}

: > "$LOG"
echo "Démarrage de Locust (connexion de l'admin et de chloe, création de la catégorie de charge)..."
cd "$LOAD"
LOAD_PROFILE=peak LOAD_NOMINAL_USERS=1 LOAD_NOMINAL_RATE=1 LOAD_NOMINAL_SECONDS=0 \
LOAD_PEAK_USERS="$PEAK_USERS" LOAD_PEAK_RATE="$PEAK_RATE" LOAD_MAX_SECONDS=600 \
LOAD_REQUEST_LOG="$LOG" LOAD_STOP_FILE="$STOP" \
LOAD_ADMIN_PASSWORD="$admin_pw" LOAD_ALICE_PASSWORD="$alice_pw" \
LOAD_BOB_PASSWORD="$bob_pw" LOAD_CHLOE_PASSWORD="$chloe_pw" \
uv run --quiet locust -f locustfile.py --headless --host "$API" \
  --exit-code-on-error 0 --only-summary > "${WORK}/locust.log" 2>&1 &
locust_pid=$!
cd "$HERE"

t_start="$(now)"
max_ready=2; t_five=""
victim=""; t_delete=""; t_new_ready=""; t_recovered=""; fails_at_delete=0
phase=attente   # attente -> supprime -> maintien
five_since=""
manual=0

# Boucle de suivi : un tour toutes les 2 s (`read -t` sert aussi de pause et lit la touche « s »).
while true; do
  kill -0 "$locust_pid" 2>/dev/null || { echo "Locust s'est arrêté (voir ci-dessous)." >&2; tail -5 "${WORK}/locust.log" >&2; exit 1; }
  ready="$(ready_count)"; ready="${ready:-0}"
  t_now="$(now)"
  (( ready > max_ready )) && max_ready=$ready
  if [[ -z "$t_five" && "$ready" -ge 5 ]]; then t_five="$t_now"; fi

  case "$phase" in
    attente)
      since_start="$(python3 -c "print($t_now - $t_start)")"
      msg="En attente des 5 réplicas prêts (prêts : ${ready}/5)."
      [[ -n "$t_five" ]] && msg="5 réplicas prêts en $(python3 -c "print(f'{$t_five - $t_start:.0f}')") s."
      [[ "$AUTO" == 1 ]] && msg="${msg} Touche « s » : supprimer un pod maintenant (sinon, ${AFTER_FIVE} s après les 5 réplicas)." \
        || msg="${msg} Touche « s » : supprimer un pod maintenant."
      go=0
      [[ $manual -eq 1 ]] && go=1
      if [[ "$AUTO" == 1 ]]; then
        [[ -n "$t_five" ]] && python3 -c "import sys; sys.exit(0 if $t_now - $t_five >= $AFTER_FIVE else 1)" && go=1
        python3 -c "import sys; sys.exit(0 if $t_now - $t_start >= $MAX_WAIT else 1)" && go=1
      fi
      if [[ $go -eq 1 ]]; then
        victim="$($K get pods -l "$LABEL" -o jsonpath='{range .items[?(@.status.containerStatuses[0].ready==true)]}{.metadata.name}{"\n"}{end}' | sed -n 1p)"
        [[ -n "$victim" ]] || { echo "Aucun pod prêt à supprimer." >&2; exit 1; }
        before_ready="$ready"
        before_names="$($K get pods -l "$LABEL" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}')"
        read -r _ fails_at_delete <<< "$(counts)"
        t_delete="$(now)"
        $K delete pod "$victim" --wait=false >/dev/null
        phase=supprime
        msg="Pod supprimé : ${victim}. Kubernetes le remplace."
      fi
      screen "$msg"
      ;;
    supprime)
      listing="$($K get pods -l "$LABEL" -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.containerStatuses[0].ready}{" "}{.metadata.deletionTimestamp}{"\n"}{end}')"
      if [[ -z "$t_new_ready" ]]; then
        while read -r name state terminating; do
          [[ -n "$name" && "$state" == true && -z "$terminating" ]] || continue
          grep -qx "$name" <<< "$before_names" || { t_new_ready="$(now)"; break; }
        done <<< "$listing"
      fi
      if [[ -n "$t_new_ready" && "$ready" -ge "$before_ready" ]]; then
        t_recovered="$(now)"; phase=maintien
      fi
      screen "Pod supprimé : ${victim}. En attente du remplaçant prêt."
      # Délai maximal : sans remplaçant au bout de 120 s, on sort de la boucle (bilan sans remplacement).
      if python3 -c "import sys; sys.exit(0 if $t_now - $t_delete >= 120 else 1)"; then
        echo "Pas de remplaçant prêt après 120 s : arrêt de la charge." >&2
        break
      fi
      ;;
    maintien)
      screen "Remplaçant prêt en $(python3 -c "print(f'{$t_new_ready - $t_delete:.1f}')") s. La charge continue ${AFTER_DELETE} s encore."
      python3 -c "import sys; sys.exit(0 if $t_now - $t_recovered >= $AFTER_DELETE else 1)" && break
      ;;
  esac

  if [[ -t 0 ]]; then
    key=""; read -r -s -n 1 -t 2 key || true
    [[ "$key" == s || "$key" == S ]] && manual=1
  else
    sleep 2
  fi
done

# Arrêt de la charge, puis bilan.
: > "$STOP"
t_stop="$(now)"
wait "$locust_pid" 2>/dev/null || true
locust_pid=""
read -r total failed <<< "$(counts)"
bilan="$(python3 - "$LOG" "${t_delete:-0}" "${t_recovered:-$(now)}" <<'PY'
import csv, sys
log, t_delete, t_recovered = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
rows = [r for r in csv.DictReader(open(log)) if not r["name"].startswith("[")]
s5xx = sum(1 for r in rows if r["status"].startswith("5"))
window = [r for r in rows if t_delete <= float(r["epoch"]) <= t_recovered]
failed_window = sum(1 for r in window if r["failed"] == "1")
reads = sorted(float(r["response_ms"]) for r in rows if r["name"] == "GET /articles")
p95 = reads[int(0.95 * (len(reads) - 1))] if reads else 0
print(f"{s5xx} {len(window)} {failed_window} {p95:.0f}")
PY
)"
read -r s5xx window_total window_failed p95 <<< "$bilan"
[[ $tty_mode -eq 1 ]] && printf '\033[H\033[2J'
# Le bilan est affiché puis enregistré (horodaté, sans secret) dans resultats/.
mkdir -p "${HERE}/resultats"
BILAN_FILE="${HERE}/resultats/pic-$(date +%Y%m%d-%H%M%S).txt"
{
echo "================ BILAN DU PIC DE CHARGE ================"
echo "Charge             : ${PEAK_USERS} utilisateurs simulés, ${total} requêtes en $(python3 -c "print(f'{$t_stop - $t_start:.0f}')") s"
if [[ -n "$t_five" ]]; then
  echo "Montée de l'HPA    : 2 à ${max_ready} réplicas prêts, 5 atteints $(python3 -c "print(f'{$t_five - $t_start:.0f}')") s après le début"
else
  echo "Montée de l'HPA    : 2 à ${max_ready} réplicas prêts (5 non atteints)"
fi
echo "Pod supprimé       : ${victim:-aucun}"
if [[ -n "$t_new_ready" ]]; then
  echo "Remplacement       : remplaçant prêt en $(python3 -c "print(f'{$t_new_ready - $t_delete:.1f}')") s, effectif de nouveau complet en $(python3 -c "print(f'{$t_recovered - $t_delete:.1f}')") s"
  echo "Pendant le remplacement : ${window_failed} échec(s) sur ${window_total} requêtes"
fi
echo "Échecs au total    : ${failed} sur ${total} requêtes (dont ${s5xx} réponse(s) 5xx)"
echo "Lecture du catalogue : p95 = ${p95} ms (seuil I3 : 300 ms)"
echo "Retour à 2 réplicas : seul, d'ici 5 à 10 minutes (fenêtre de stabilisation de l'HPA, mesure du protocole 5 et des répétitions)."
echo "========================================================="
} | tee "$BILAN_FILE"
echo "Bilan enregistré : ${BILAN_FILE#"${ROOT}"/}"
