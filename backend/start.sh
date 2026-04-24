#!/bin/bash
echo "Starting Somniac AI Backend..."
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

PORT=${PORT:-8000}
uvicorn main:app --host 0.0.0.0 --port $PORT --reload
