@echo off
echo Starting Log Viewer...
start "Log Viewer" cmd /k "python -m logview --port 9999"

:: Give the server a moment to start
timeout /t 2 /nobreak >nul

echo Starting Log Generator...
python tools\log_generator.py --port 9999 --duration 30
