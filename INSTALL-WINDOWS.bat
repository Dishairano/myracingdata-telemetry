@echo off
REM MyRacingData Telemetry Capture - Easy Windows Installer
REM This script installs Python (if needed) and sets up the app

echo.
echo ========================================
echo MyRacingData Telemetry Capture
echo Easy Installation for Windows
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [1/4] Python not found. Installing Python 3.11...
    echo.
    echo Downloading Python installer...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe' -OutFile 'python-installer.exe'"
    
    echo Installing Python (this may take 2-3 minutes)...
    python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    echo Waiting for installation to complete...
    timeout /t 30 /nobreak >nul
    
    echo Cleaning up...
    del python-installer.exe
    
    echo Python installed successfully!
    echo.
) else (
    echo [1/4] Python found: 
    python --version
    echo.
)

REM Install dependencies
echo [2/4] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [3/4] Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\MyRacingData Telemetry.lnk'); $Shortcut.TargetPath = 'python'; $Shortcut.Arguments = '%CD%\src\main.py'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.Description = 'MyRacingData Telemetry Capture'; $Shortcut.Save()"

echo.
echo [4/4] Creating config directory...
if not exist "%USERPROFILE%\.myracingdata" mkdir "%USERPROFILE%\.myracingdata"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Desktop shortcut created: "MyRacingData Telemetry"
echo.
echo To start the app:
echo   - Double-click the desktop shortcut
echo   OR
echo   - Run: python src\main.py
echo.
echo First-time setup:
echo   1. Get API key from: https://95.216.5.123/settings/api-keys
echo   2. Edit config: %USERPROFILE%\.myracingdata\config.json
echo   3. Add your API key
echo.
echo Press any key to start the app now...
pause >nul

python src\main.py
