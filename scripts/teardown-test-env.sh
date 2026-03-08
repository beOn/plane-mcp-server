#!/usr/bin/env bash
# Tear down the ephemeral test stack, removing all data.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "==> Tearing down ephemeral test stack..."
docker compose -f docker-compose-test.yml down -v --remove-orphans 2>&1

echo "==> Done. All test containers and volumes removed."
