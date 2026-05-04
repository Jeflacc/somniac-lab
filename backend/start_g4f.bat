@echo off
echo Starting G4F API Server locally on port 1337...
cd /d %~dp0
call venv\Scripts\activate
python -m g4f.cli api
pause
