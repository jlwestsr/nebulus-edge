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

# Start the server
echo "Starting Brain Server..."
# Using python -m to run the server script directly since it has a __main__ block
# Alternatively could use uvicorn brain.server:app --host 0.0.0.0 --port 8080
python "$BRAIN_DIR/server.py"
