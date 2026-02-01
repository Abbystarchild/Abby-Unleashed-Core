@echo off
title Abby Unleashed Server
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo.
echo ========================================
echo    Abby Unleashed - Enhanced Server
echo ========================================
echo.
echo Starting server on port 8080...
echo Access locally: http://localhost:8080
echo Access from phone: http://192.168.254.31:8080
echo.
echo Press Ctrl+C to stop the server
echo.
python api_server.py --port 8080
pause
