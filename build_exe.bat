@echo off
echo Building Abby Unleashed Launcher...
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat

echo Installing PyInstaller if needed...
pip install pyinstaller --quiet

echo.
echo Building executable...
pyinstaller --onefile --windowed --name "Abby Unleashed" --icon=abby.ico launcher.py --distpath . --clean

echo.
echo Cleaning up...
rmdir /s /q build 2>nul
del /q "Abby Unleashed.spec" 2>nul

echo.
echo ========================================
echo   Build complete!
echo   "Abby Unleashed.exe" created
echo ========================================
pause
