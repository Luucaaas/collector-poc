#!/usr/bin/env bash
# Jeu de données de la démonstration : 5 catégories, une boutique par vendeur (alice, bob),
# 11 articles crédibles, et chloe qui suit la catégorie « Figurines ».
#
#   docs/07-soutenance/demo/donnees-demo.sh
#
# Relançable sans doublon (rien n'est recréé s'il existe déjà). Les données sont créées par l'API
# publique, avec le vrai flux de connexion PKCE (comme le navigateur) : c'est ce que montre le
# catalogue pendant la démonstration.
#
# CATALOGUE PROPRE : l'API n'a pas de suppression, donc les données de test (parcours Playwright
# « E2E », test de charge « Charge ») ne s'effacent pas. La solution la plus simple est de refaire
# un cluster neuf la veille (cluster.sh delete, create, deploy.sh all <tag>), puis de lancer ce
# script. Si le catalogue contient autre chose que le jeu de la démo, le script le dit et sort
# avec le code 3.
#
# Les mots de passe sont lus dans deploy/local/.env et donnés au seul processus Python en préfixe de
# commande : jamais affichés, jamais en argument, jamais écrits.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${HERE}/../../.." && pwd)"
ENV_FILE="${ROOT}/deploy/local/.env"

# Valeur d'une clé du .env, jamais affichée ; clé absente ou vide : message et arrêt.
read_var() {
  grep -m1 -E "^$1=" "$ENV_FILE" | cut -d= -f2- | grep . \
    || { echo "Clé $1 absente ou vide dans deploy/local/.env." >&2; return 1; }
}

command -v uv >/dev/null || { echo "uv est requis (brew install uv)." >&2; exit 1; }
command -v mkcert >/dev/null || { echo "mkcert est requis." >&2; exit 1; }
[[ -f "$ENV_FILE" ]] || { echo "deploy/local/.env introuvable : le cluster est-il déployé ?" >&2; exit 1; }
admin_pw="$(read_var ADMIN_PASSWORD)"; alice_pw="$(read_var ALICE_PASSWORD)"
bob_pw="$(read_var BOB_PASSWORD)"; chloe_pw="$(read_var CHLOE_PASSWORD)"
# Autorité du cluster : la vérification TLS n'est jamais désactivée.
REQUESTS_CA_BUNDLE="$(mkcert -CAROOT)/rootCA.pem"
[[ -f "$REQUESTS_CA_BUNDLE" ]] || { echo "Autorité mkcert introuvable (mkcert -install fait ?)." >&2; exit 1; }
export REQUESTS_CA_BUNDLE

# `uv run --project` utilise l'environnement de tests/load (requests vient de Locust).
DEMO_ADMIN_PASSWORD="$admin_pw" DEMO_ALICE_PASSWORD="$alice_pw" \
DEMO_BOB_PASSWORD="$bob_pw" DEMO_CHLOE_PASSWORD="$chloe_pw" \
  uv run --quiet --project "${ROOT}/tests/load" python -u "${HERE}/donnees_demo.py"
