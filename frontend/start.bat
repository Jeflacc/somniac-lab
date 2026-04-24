@echo off
echo Starting Somniac Frontend...
cd /d %~dp0
npm install
npm run dev
pause
