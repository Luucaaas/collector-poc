#!/usr/bin/env bash
# Lance les parcours Playwright contre le cluster k3d (https://app.127.0.0.1.sslip.io).
# Les mots de passe des comptes de démonstration sont lus dans deploy/local/.env et exportés dans
# l'environnement de ce seul processus : ils ne sont ni affichés, ni passés en argument, ni écrits.
# Le certificat mkcert doit être reconnu par Chromium (mkcert -install fait) : la vérification TLS
# n'est jamais désactivée.
#   ./run-cluster.sh               les 6 parcours
#   CAPTURES=1 ./run-cluster.sh    la spécification des captures d'écran (e2e/resultats/captures/)
#   ./run-cluster.sh -g "alice"    options de `playwright test`
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE="../deploy/local/.env"
[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env introuvable : le cluster a-t-il été déployé (deploy/local/deploy.sh) ?" >&2; exit 1; }

# Valeur d'une clé du .env, jamais affichée ; clé absente : message explicite et arrêt.
read_var() {
  grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | grep . \
    || { echo "Clé $1 absente ou vide dans deploy/local/.env." >&2; return 1; }
}

E2E_ADMIN_PASSWORD="$(read_var ADMIN_PASSWORD)"
E2E_ALICE_PASSWORD="$(read_var ALICE_PASSWORD)"
E2E_CHLOE_PASSWORD="$(read_var CHLOE_PASSWORD)"
export E2E_ADMIN_PASSWORD E2E_ALICE_PASSWORD E2E_CHLOE_PASSWORD
export E2E_BASE_URL="https://app.127.0.0.1.sslip.io"

curl -fsS -o /dev/null "$E2E_BASE_URL/" || { echo "$E2E_BASE_URL ne répond pas (ou certificat non reconnu) : le cluster est-il lancé ?" >&2; exit 1; }
curl -fsS -o /dev/null "https://auth.127.0.0.1.sslip.io/realms/collector/.well-known/openid-configuration" || { echo "https://auth.127.0.0.1.sslip.io ne répond pas : Keycloak est-il prêt ?" >&2; exit 1; }

exec npx playwright test "$@"
