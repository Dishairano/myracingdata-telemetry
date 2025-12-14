@echo off
REM MyRacingData Telemetry Capture - Quick Start

echo Starting MyRacingData Telemetry Capture...
echo.

python src\main.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start
    echo.
    echo If Python is not installed, run: INSTALL-WINDOWS.bat
    echo.
    pause
)
