#!/bin/bash
# Start Nebulus Intelligence server

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -q -r intelligence/requirements.txt

echo "Starting Intelligence Server..."
python -m intelligence.server
