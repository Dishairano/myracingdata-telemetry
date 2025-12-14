#!/bin/bash
# Build Windows .exe using Docker

set -e

echo "🐳 Building MyRacingData Telemetry using Docker"
echo "================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo ""
    echo "Install Docker:"
    echo "  Ubuntu/Debian: sudo apt install docker.io"
    echo "  Or visit: https://docs.docker.com/engine/install/"
    exit 1
fi

echo "✓ Docker installed: $(docker --version)"

# Build Docker image
echo ""
echo "📦 Building Docker image (this may take 10-15 minutes)..."
docker build -t myracingdata-builder .

echo "✓ Docker image built"

# Run build
echo ""
echo "🔨 Building Windows executable..."
docker run --rm -v $(pwd)/dist:/app/dist myracingdata-builder

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
    
    echo "✓ Distribution package: MyRacingData-Telemetry-v1.0.0.zip"
    echo ""
    echo "🎉 Done!"
    
else
    echo ""
    echo "❌ Build failed"
    exit 1
fi
