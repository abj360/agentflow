#!/usr/bin/env bash
# run-local.sh --- boots the full agentflow stack locally with one command.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "created .env from .env.example — edit it to change defaults"
fi

echo "booting agentflow: api :8000, console :3000, postgres :5432, redis :6379"
docker compose --project-directory . -f docker/docker-compose.yml up --build "$@"
