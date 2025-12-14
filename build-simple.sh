#!/bin/bash
# Simple build script - creates a Python ZIP app instead of .exe
# This works on Linux without Wine/Docker and runs on Windows

set -e

echo "🐍 Building MyRacingData Telemetry (Python ZIP format)"
echo "======================================================"

# Create output directory
mkdir -p dist

echo "📦 Creating Python application bundle..."

# Create a zipapp
python3 -m zipapp src -o dist/myracingdata-telemetry.pyz -p "/usr/bin/env python3"

echo ""
echo "✅ Build successful!"
echo "   Output: dist/myracingdata-telemetry.pyz"
echo ""
echo "📝 Usage on Windows:"
echo "   1. Install Python 3.11+ on Windows"
echo "   2. Install dependencies: pip install -r requirements.txt"
echo "   3. Run: python myracingdata-telemetry.pyz"
echo ""
echo "   OR run the source directly:"
echo "   python src/main.py"

# Also create a batch file for Windows
cat > dist/run-windows.bat << 'BAT'
@echo off
echo MyRacingData Telemetry Capture
echo ===============================

python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found!
    echo Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting telemetry capture...
python src/main.py

pause
BAT

echo "✓ Created run-windows.bat for easy Windows execution"
echo ""
echo "📦 Alternative: Just copy the entire folder to Windows and run run-windows.bat"
