#!/usr/bin/env bash
# Lance les parcours Playwright contre la pile docker compose (deploy/compose/up.sh déjà lancé).
# Les mots de passe des comptes de démonstration sont lus dans deploy/compose/.env et exportés dans
# l'environnement de ce seul processus : ils ne sont ni affichés, ni passés en argument, ni écrits.
#   ./run-compose.sh              tous les parcours
#   ./run-compose.sh -g "alice"   options de `playwright test`
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE="../deploy/compose/.env"
[[ -f "$ENV_FILE" ]] || { echo "deploy/compose/.env introuvable : lancer deploy/compose/up.sh d'abord." >&2; exit 1; }

# Valeur d'une clé du .env, jamais affichée ; clé absente : message explicite et arrêt.
read_var() {
  grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | grep . \
    || { echo "Clé $1 absente ou vide dans deploy/compose/.env." >&2; return 1; }
}

E2E_ADMIN_PASSWORD="$(read_var ADMIN_PASSWORD)"
E2E_ALICE_PASSWORD="$(read_var ALICE_PASSWORD)"
E2E_CHLOE_PASSWORD="$(read_var CHLOE_PASSWORD)"
export E2E_ADMIN_PASSWORD E2E_ALICE_PASSWORD E2E_CHLOE_PASSWORD

curl -fsS -o /dev/null http://localhost:8001/health/ready || { echo "catalog-service ne répond pas : la pile compose est-elle lancée ?" >&2; exit 1; }

exec npx playwright test "$@"
