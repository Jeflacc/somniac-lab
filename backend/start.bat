@echo off
echo Starting Somniac AI Backend...
cd /d %~dp0
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt -q
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
