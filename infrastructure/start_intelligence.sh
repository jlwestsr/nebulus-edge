#!/bin/bash
# Start Nebulus Intelligence server

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/venv"

cd "$PROJECT_DIR"

# Activate Virtual Environment
if [ -d "$VENV_DIR" ]; then
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment not found at $VENV_DIR. Creating one..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
fi

echo "Installing dependencies..."
pip install -q -r intelligence/requirements.txt

echo "Starting Intelligence Server..."
python -m intelligence.server
