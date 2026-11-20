#!/usr/bin/env bash
# Copies the password of a demo account to the Mac clipboard, WITHOUT EVER
# displaying it, then clears the clipboard after a delay. Used to log in live (Cmd+V
# in the Keycloak or Grafana field) without showing the deploy/local/.env file.
#
#   docs/07-soutenance/demo/mot-de-passe.sh <admin|alice|bob|chloe|grafana> [delay in seconds]
#   docs/07-soutenance/demo/mot-de-passe.sh --vider        clears the clipboard immediately
#
# The default delay is 30 s. The clipboard is only cleared if it still contains this
# password (if you copied something else in the meantime, it is left alone). The password goes through a
# pipe (printf | pbcopy), never as a command argument: it does not appear in `ps`.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${HERE}/../../../deploy/local/.env"
DELAY="${2:-30}"

if [[ "${1:-}" == "--vider" ]]; then
  printf '' | pbcopy
  echo "Clipboard cleared."
  exit 0
fi

case "${1:-}" in
  admin) key=ADMIN_PASSWORD ;;
  alice) key=ALICE_PASSWORD ;;
  bob) key=BOB_PASSWORD ;;
  chloe) key=CHLOE_PASSWORD ;;
  grafana) key=GRAFANA_ADMIN_PASSWORD ;;
  *) echo "Usage: $0 <admin|alice|bob|chloe|grafana> [delay in seconds] | --vider" >&2; exit 2 ;;
esac
[[ "$DELAY" =~ ^[0-9]+$ ]] || { echo "The delay must be a number of seconds." >&2; exit 2; }
[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env not found: is the cluster deployed?" >&2; exit 1; }

pw="$(grep -m1 -E "^${key}=" "$ENV_FILE" | cut -d= -f2- | grep .)" \
  || { echo "Key ${key} missing or empty in deploy/local/.env." >&2; exit 1; }
# If the script is interrupted (Ctrl+C...) before the clearing task is launched, clear
# immediately: the password must never stay in the clipboard without a timer.
trap 'printf "" | pbcopy' INT TERM EXIT
printf '%s' "$pw" | pbcopy
echo "Password of '$1' copied. Paste it with Cmd+V; the clipboard will be cleared in ${DELAY} s."

# Background task, detached from the terminal: waits, then clears if the content is still the password.
(
  sleep "$DELAY"
  if [[ "$(pbpaste)" == "$pw" ]]; then printf '' | pbcopy; fi
) >/dev/null 2>&1 &
disown $!
trap - INT TERM EXIT   # the background task takes over
