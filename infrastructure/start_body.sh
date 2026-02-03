#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BODY_DIR="$PROJECT_ROOT/body"

echo "Starting Nebulus Edge Body (Open WebUI)..."
cd "$BODY_DIR" && docker compose up -d
echo "Open WebUI started at http://localhost:3000"
