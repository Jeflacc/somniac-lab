#!/bin/bash
echo "Starting G4F API Server locally on port 1337..."

# Create venv if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Ensure g4f is installed
pip install -U g4f curl_cffi browser_cookie3

# Start G4F API
python3 -m g4f.cli api
