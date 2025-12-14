#!/bin/bash
# Build Windows .exe on Linux using Wine + PyInstaller

set -e

echo "🔨 Building MyRacingData Telemetry for Windows (on Linux)"
echo "=========================================================="

# Check if Wine is installed
if ! command -v wine &> /dev/null; then
    echo "❌ Wine is not installed!"
    echo ""
    echo "Installing Wine..."
    
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo dpkg --add-architecture i386
        sudo apt update
        sudo apt install -y wine wine64 wine32
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS/Fedora
        sudo dnf install -y wine
    elif [ -f /etc/arch-release ]; then
        # Arch Linux
        sudo pacman -S wine
    else
        echo "❌ Unsupported Linux distribution"
        echo "   Please install Wine manually: https://www.winehq.org/"
        exit 1
    fi
fi

echo "✓ Wine installed: $(wine --version)"

# Check if Python is installed in Wine
if ! wine python --version &> /dev/null; then
    echo ""
    echo "📦 Installing Python 3.11 in Wine..."
    
    # Download Python installer
    PYTHON_INSTALLER="python-3.11.0-amd64.exe"
    if [ ! -f "$PYTHON_INSTALLER" ]; then
        echo "   Downloading Python 3.11.0..."
        wget https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe
    fi
    
    # Install Python silently
    echo "   Installing Python (this may take a few minutes)..."
    wine $PYTHON_INSTALLER /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    # Wait for installation
    sleep 10
    
    echo "✓ Python installed in Wine"
fi

echo ""
echo "🐍 Python version: $(wine python --version)"

# Install pip packages in Wine
echo ""
echo "📦 Installing Python dependencies in Wine..."
wine python -m pip install --upgrade pip
wine python -m pip install -r requirements.txt
wine python -m pip install pyinstaller

echo "✓ Dependencies installed"

# Build with PyInstaller
echo ""
echo "🔨 Building Windows executable with PyInstaller..."
wine pyinstaller myracingdata.spec --clean

# Check output
if [ -f "dist/MyRacingData-Telemetry.exe" ]; then
    SIZE=$(du -h dist/MyRacingData-Telemetry.exe | cut -f1)
    echo ""
    echo "✅ Build successful!"
    echo "   Output: dist/MyRacingData-Telemetry.exe"
    echo "   Size: $SIZE"
    
    # Create distribution package
    echo ""
    echo "📦 Creating distribution package..."
    
    mkdir -p dist/package
    cp dist/MyRacingData-Telemetry.exe dist/package/
    cp README.md dist/package/README.txt
    
    cat > dist/package/config.ini.example << 'CONFIG'
# MyRacingData Telemetry Capture Configuration
# Copy this to: C:\Users\YourName\.myracingdata\config.json

{
  "api_url": "https://95.216.5.123/api/v1",
  "ws_url": "wss://95.216.5.123/api/v1/ws",
  "api_key": "YOUR_API_KEY_HERE",
  "update_rate_hz": 60,
  "auto_start": true
}
CONFIG
    
    cd dist/package
    zip -r ../../MyRacingData-Telemetry-v1.0.0.zip *
    cd ../..
    
    echo "✓ Distribution package created: MyRacingData-Telemetry-v1.0.0.zip"
    
    echo ""
    echo "🎉 Done!"
    echo ""
    echo "To test on Windows:"
    echo "  1. Copy MyRacingData-Telemetry-v1.0.0.zip to Windows PC"
    echo "  2. Extract and run MyRacingData-Telemetry.exe"
    
else
    echo ""
    echo "❌ Build failed - executable not found"
    exit 1
fi

