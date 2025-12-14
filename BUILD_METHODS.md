# Building Windows .exe on Linux

There are 3 methods to build the Windows executable on Linux:

---

## Method 1: Docker (Recommended) ✅

**Pros**: Clean, isolated, reproducible
**Cons**: Requires Docker, ~2GB download

### Steps:

```bash
cd myracingdata-telemetry-capture

# Install Docker if needed
sudo apt install docker.io
sudo usermod -aG docker $USER  # Add user to docker group
newgrp docker  # Apply group change

# Build
./build-docker.sh
```

**Time**: ~15 minutes first time, ~2 minutes after

**Output**: `dist/MyRacingData-Telemetry.exe`

---

## Method 2: Wine (Direct) ⚡

**Pros**: Faster, no Docker needed
**Cons**: Can mess with system Wine config

### Steps:

```bash
cd myracingdata-telemetry-capture

# Install Wine
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install wine wine64 wine32

# Build
./build-on-linux.sh
```

**Time**: ~10 minutes first time (downloads Python), ~1 minute after

**Output**: `dist/MyRacingData-Telemetry.exe`

---

## Method 3: GitHub Actions (Cloud) ☁️

**Pros**: No local setup needed
**Cons**: Requires GitHub account

### Steps:

1. Push code to GitHub
2. Create `.github/workflows/build.yml`:

```yaml
name: Build Windows Exe

on: [push]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pyinstaller myracingdata.spec
      - uses: actions/upload-artifact@v3
        with:
          name: MyRacingData-Telemetry
          path: dist/MyRacingData-Telemetry.exe
```

3. Download artifact from GitHub Actions

---

## Method 4: Cross-Compile with PyInstaller (Experimental) 🧪

**Not recommended**: PyInstaller doesn't officially support cross-compilation

---

## Comparison

| Method | Setup Time | Build Time | Reliability | Isolation |
|--------|------------|------------|-------------|-----------|
| Docker | 15 min | 2-5 min | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Wine | 10 min | 1-2 min | ⭐⭐⭐⭐ | ⭐⭐ |
| GitHub Actions | 5 min | 5-10 min | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Troubleshooting

### Docker: "permission denied"
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Wine: "Python not found"
```bash
# Make sure Python installer finished
wine python --version

# If not, reinstall
cd myracingdata-telemetry-capture
wget https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe
wine python-3.11.0-amd64.exe
```

### Build fails: "module not found"
```bash
# Make sure all deps installed
wine python -m pip install -r requirements.txt
```

---

## Quick Start (Docker)

```bash
cd myracingdata-telemetry-capture
./build-docker.sh
```

Wait 15 minutes, get `MyRacingData-Telemetry.exe` ✅

---

## Quick Start (Wine - if Docker not available)

```bash
cd myracingdata-telemetry-capture  
./build-on-linux.sh
```

Downloads Python automatically, builds exe ✅

---

**Recommended**: Use Docker for clean, reproducible builds!
