#!/usr/bin/env bash
# Stops the local stack. `--volumes` also deletes the data (PostgreSQL, RabbitMQ).
# The built images are kept. The .env file is never deleted.
set -euo pipefail
cd "$(dirname "$0")"

ARGS=()
[[ "${1:-}" == "--volumes" ]] && ARGS=(--volumes)
# --remove-orphans: also removes a container left by a previous version of the file.
# A missing .env must not prevent the shutdown: compose only needs the service names.
if [[ -f .env ]]; then
  docker compose down --remove-orphans ${ARGS[@]+"${ARGS[@]}"}
else
  docker compose --env-file .env.example down --remove-orphans ${ARGS[@]+"${ARGS[@]}"}
fi
