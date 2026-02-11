#!/bin/bash
set -e

# Define paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"
BRAIN_DIR="$PROJECT_ROOT/brain"

# Activate Virtual Environment
if [ -d "$VENV_DIR" ]; then
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment not found at $VENV_DIR. Creating one..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r "$BRAIN_DIR/requirements.txt"

# Ensure project root is on PYTHONPATH so shared/ is importable
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

# Start the server
echo "Starting Brain Server..."
python "$BRAIN_DIR/server.py"
