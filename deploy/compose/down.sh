#!/usr/bin/env bash
# Arrête la pile locale. `--volumes` supprime aussi les données (PostgreSQL, RabbitMQ).
# Les images construites sont conservées. Le fichier .env n'est jamais supprimé.
set -euo pipefail
cd "$(dirname "$0")"

ARGS=()
[[ "${1:-}" == "--volumes" ]] && ARGS=(--volumes)
# --remove-orphans : retire aussi un conteneur laissé par une version précédente du fichier.
# Un .env absent ne doit pas empêcher l'arrêt : compose a seulement besoin des noms de services.
if [[ -f .env ]]; then
  docker compose down --remove-orphans ${ARGS[@]+"${ARGS[@]}"}
else
  docker compose --env-file .env.example down --remove-orphans ${ARGS[@]+"${ARGS[@]}"}
fi
