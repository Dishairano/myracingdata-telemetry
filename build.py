#!/usr/bin/env python3
"""
Build script for MyRacingData Telemetry Capture
Creates a standalone Windows executable
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    print("🔨 Building MyRacingData Telemetry Capture")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    print("✓ Dependencies installed")
    
    # Clean previous build
    print("\n🧹 Cleaning previous build...")
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed {dir_name}/")
    
    # Build with PyInstaller
    print("\n🔨 Building executable with PyInstaller...")
    subprocess.run([sys.executable, "-m", "PyInstaller", "myracingdata.spec"], check=True)
    
    # Check output
    exe_path = Path("dist/MyRacingData-Telemetry.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n✅ Build successful!")
        print(f"   Output: {exe_path}")
        print(f"   Size: {size_mb:.1f} MB")
        
        # Create distribution package
        print("\n📦 Creating distribution package...")
        create_distribution()
        
        print("\n🎉 Done!")
        print("\nTo test the executable:")
        print(f"  {exe_path.absolute()}")
        
    else:
        print("\n❌ Build failed - executable not found")
        sys.exit(1)

def create_distribution():
    """Create a distribution ZIP file"""
    dist_dir = Path("dist")
    
    # Copy README
    shutil.copy("README.md", dist_dir / "README.txt")
    
    # Create example config
    with open(dist_dir / "config.ini.example", "w") as f:
        f.write("""# MyRacingData Telemetry Capture Configuration
# Copy this file to: C:\\Users\\YourName\\.myracingdata\\config.json

{
  "api_url": "https://95.216.5.123/api/v1",
  "ws_url": "wss://95.216.5.123/api/v1/ws",
  "api_key": "YOUR_API_KEY_HERE",
  "update_rate_hz": 60,
  "buffer_size": 1000,
  "auto_start": true,
  "minimize_to_tray": true,
  "enable_logging": true
}
""")
    
    # Create ZIP
    import zipfile
    
    zip_path = Path("MyRacingData-Telemetry-v1.0.0.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(dist_dir / "MyRacingData-Telemetry.exe", "MyRacingData-Telemetry.exe")
        zipf.write(dist_dir / "README.txt", "README.txt")
        zipf.write(dist_dir / "config.ini.example", "config.ini.example")
    
    print(f"✓ Distribution package created: {zip_path}")

if __name__ == '__main__':
    main()
