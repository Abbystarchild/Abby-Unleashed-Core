@echo off
title Abby Unleashed
color 0B

echo ============================================================
echo                  ABBY UNLEASHED
echo ============================================================
echo.

:: Store script directory (remove trailing backslash for clean paths)
set "ABBY_DIR=%~dp0"
set "ABBY_DIR=%ABBY_DIR:~0,-1%"
cd /d "%ABBY_DIR%"

echo Working directory: %ABBY_DIR%
echo.

:: Check if venv exists
if not exist "%ABBY_DIR%\venv\Scripts\python.exe" (
    echo ERROR: Python virtual environment not found!
    pause
    exit /b 1
)

echo Starting Abby Server...

:: Start the server in a new window
start "Abby Server" /D "%ABBY_DIR%" cmd /k ""%ABBY_DIR%\venv\Scripts\python.exe" "%ABBY_DIR%\api_server.py" --no-browser"

:: Wait for server
echo Waiting for server...
timeout /t 4 /nobreak > nul

:: Launch browser - Chrome or Edge work best with local speech recognition
echo Launching browser...

:: Try Chrome first (best compatibility)
set "CHROME_PATH="
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME_PATH=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME_PATH=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_PATH=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"

if defined CHROME_PATH (
    echo Found Chrome - launching...
    start "" "%CHROME_PATH%" --app=http://localhost:8080
    goto :end
)

:: Try Edge
set "EDGE_PATH="
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "EDGE_PATH=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "EDGE_PATH=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"

if defined EDGE_PATH (
    echo Found Edge - launching...
    start "" "%EDGE_PATH%" --app=http://localhost:8080
    goto :end
)

:: Last resort - default browser
echo Opening default browser...
start "" "http://localhost:8080"

:end
echo.
echo Abby is running at http://localhost:8080
timeout /t 3
