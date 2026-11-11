#!/usr/bin/env bash
# Copie dans le presse-papiers du Mac le mot de passe d'un compte de démonstration, SANS JAMAIS
# l'afficher, puis vide le presse-papiers après un délai. Sert à se connecter en direct (Cmd+V
# dans le champ de Keycloak ou de Grafana) sans montrer le fichier deploy/local/.env.
#
#   docs/07-soutenance/demo/mot-de-passe.sh <admin|alice|bob|chloe|grafana> [délai en secondes]
#   docs/07-soutenance/demo/mot-de-passe.sh --vider        vide tout de suite le presse-papiers
#
# Le délai par défaut est de 30 s. Le presse-papiers n'est vidé que s'il contient encore ce mot de
# passe (si tu as copié autre chose entre-temps, on n'y touche pas). Le mot de passe passe par un
# tube (printf | pbcopy), jamais en argument d'une commande : il n'apparaît pas dans `ps`.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${HERE}/../../../deploy/local/.env"
DELAY="${2:-30}"

if [[ "${1:-}" == "--vider" ]]; then
  printf '' | pbcopy
  echo "Presse-papiers vidé."
  exit 0
fi

case "${1:-}" in
  admin) key=ADMIN_PASSWORD ;;
  alice) key=ALICE_PASSWORD ;;
  bob) key=BOB_PASSWORD ;;
  chloe) key=CHLOE_PASSWORD ;;
  grafana) key=GRAFANA_ADMIN_PASSWORD ;;
  *) echo "Usage : $0 <admin|alice|bob|chloe|grafana> [délai en secondes] | --vider" >&2; exit 2 ;;
esac
[[ "$DELAY" =~ ^[0-9]+$ ]] || { echo "Le délai doit être un nombre de secondes." >&2; exit 2; }
[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env introuvable : le cluster est-il déployé ?" >&2; exit 1; }

pw="$(grep -m1 -E "^${key}=" "$ENV_FILE" | cut -d= -f2- | grep .)" \
  || { echo "Clé ${key} absente ou vide dans deploy/local/.env." >&2; exit 1; }
# Si le script est interrompu (Ctrl+C...) avant le lancement de la tâche de vidage, on vide tout de
# suite : le mot de passe ne doit jamais rester dans le presse-papiers sans minuterie.
trap 'printf "" | pbcopy' INT TERM EXIT
printf '%s' "$pw" | pbcopy
echo "Mot de passe de « $1 » copié. Colle-le avec Cmd+V ; le presse-papiers sera vidé dans ${DELAY} s."

# Tâche de fond, détachée du terminal : attend, puis vide si le contenu est toujours le mot de passe.
(
  sleep "$DELAY"
  if [[ "$(pbpaste)" == "$pw" ]]; then printf '' | pbcopy; fi
) >/dev/null 2>&1 &
disown $!
trap - INT TERM EXIT   # la tâche de fond prend le relais
