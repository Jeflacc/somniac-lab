#!/bin/bash
echo "Starting G4F API Server locally on port 1337..."

# Create venv if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Ensure g4f and all API server dependencies are installed
pip install -U g4f curl_cffi browser_cookie3 a2wsgi uvicorn fastapi

# Start G4F API (no GUI, API-only mode)
python3 -m g4f.cli api --no-gui
