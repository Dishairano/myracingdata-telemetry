#!/bin/bash
# Build standalone Windows executable using Nuitka
# Nuitka creates truly standalone executables (better than PyInstaller)

set -e

echo "🔨 Building MyRacingData Telemetry with Nuitka"
echo "==============================================="

# Install Nuitka if not present
if ! python3 -c "import nuitka" 2>/dev/null; then
    echo "📦 Installing Nuitka..."
    pip3 install nuitka ordered-set zstandard
fi

echo "✓ Nuitka ready"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Build with Nuitka
echo ""
echo "🔨 Building standalone executable..."
python3 -m nuitka \
    --standalone \
    --onefile \
    --output-dir=dist \
    --output-filename=MyRacingData-Telemetry.bin \
    --enable-plugin=tk-inter \
    --follow-imports \
    --include-package=websocket \
    --include-package=pystray \
    --include-package=PIL \
    src/main.py

if [ -f "dist/MyRacingData-Telemetry.bin" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "   Output: dist/MyRacingData-Telemetry.bin"
    SIZE=$(du -h dist/MyRacingData-Telemetry.bin | cut -f1)
    echo "   Size: $SIZE"
    echo ""
    echo "📝 Note: This is a Linux binary."
    echo "   For Windows, we need to use Wine or cross-compile."
else
    echo "❌ Build failed"
    exit 1
fi
