# 🏁 MyRacingData Telemetry Capture

Professional telemetry capture for **Assetto Corsa** and **Le Mans Ultimate**.

Captures **EVERY data point** from the game and streams it to MyRacingData platform in real-time.

---

## ✨ Features

- **Complete Data Capture**: 150+ data points from AC, 200+ from LMU
- **High Frequency**: 60Hz update rate
- **Auto-Detection**: Automatically finds running game
- **Low Overhead**: < 1% CPU impact
- **System Tray**: Runs minimized in background
- **Real-time Streaming**: WebSocket connection to MyRacingData

---

## 📊 Captured Data

### Assetto Corsa (~150 data points)
- Speed, RPM, gear, throttle, brake, steering, clutch
- G-forces (lateral, longitudinal, vertical)
- Tire temperatures (inner, middle, outer per tire)
- Tire pressure, wear, slip, load
- Brake temperatures (4 corners)
- Fuel level
- ERS/KERS status
- DRS available/enabled
- Lap times, sector times, delta
- Track position, session info
- Track temperature, air temperature, wind
- Damage levels
- And much more...

### Le Mans Ultimate (~200 data points)
- Everything from AC, plus:
- Detailed suspension deflection
- Aerodynamic downforce (front/rear)
- Drag coefficient
- Ride height (front/rear)
- Wing heights
- Lateral forces per tire
- Grip fraction per tire
- Engine oil & water temperature
- Clutch RPM
- Detailed damage (8 zones)
- Last impact data
- Path position
- And much more...

---

## 🚀 Quick Start

### 1. Download

Download the latest release:
- `MyRacingData-Telemetry.exe` (Windows)

### 2. Get API Key

1. Go to https://95.216.5.123/settings/api-keys
2. Generate a new API key
3. Copy it

### 3. Configure

First run will create a config file at:
```
C:\Users\YourName\.myracingdata\config.json
```

Edit it and add your API key:
```json
{
  "api_url": "https://95.216.5.123/api/v1",
  "ws_url": "wss://95.216.5.123/api/v1/ws",
  "api_key": "YOUR_API_KEY_HERE",
  "update_rate_hz": 60,
  "auto_start": true
}
```

### 4. Run

Double-click `MyRacingData-Telemetry.exe`

You'll see a system tray icon (⚡ in red circle)

### 5. Start Game

Start **Assetto Corsa** or **Le Mans Ultimate**

The app will automatically detect the game and start capturing!

---

## 🎮 Supported Games

| Game | Status | Data Points | Notes |
|------|--------|-------------|-------|
| **Assetto Corsa** | ✅ Full Support | ~150 | Native shared memory |
| **Le Mans Ultimate** | ✅ Full Support | ~200 | rFactor 2 engine |

---

## 💻 System Tray Menu

Right-click the system tray icon:

- **Start Capture** - Begin telemetry capture
- **Stop Capture** - Stop capturing
- **Status** - Show current status
- **Settings** - Open settings (coming soon)
- **Exit** - Close application

---

## 🔧 Console Mode

For debugging or server use, run in console mode:

```bash
MyRacingData-Telemetry.exe --no-gui
```

Press `Ctrl+C` to stop.

---

## 📊 Data Format

Data is sent in JSON format via WebSocket:

```json
{
  "game": "assetto_corsa",
  "timestamp": 1705251234.567,
  "speed_kmh": 287.5,
  "rpm": 11450,
  "gear": 7,
  "throttle": 1.0,
  "brake": 0.0,
  "tires": [
    {
      "position": "front_left",
      "temp_core": 85.3,
      "pressure": 26.5,
      "wear": 0.92
    },
    ...
  ],
  ...
}
```

---

## 🛠️ Building from Source

### Requirements
- Python 3.11+
- Windows 10/11

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run from Source
```bash
python src/main.py
```

### Build Executable
```bash
pyinstaller myracingdata.spec
```

Output: `dist/MyRacingData-Telemetry.exe`

---

## 🐛 Troubleshooting

### "No game detected"
- Make sure the game is actually running
- For AC: Check if shared memory is enabled
- For LMU: Make sure you're in a session (not menus)

### "Failed to connect to server"
- Check your internet connection
- Verify API key is correct
- Check if firewall is blocking connection

### "High CPU usage"
- Lower update rate in config (try 30 Hz instead of 60)
- Close other background applications

### No data showing in MyRacingData
- Check WebSocket connection status
- Verify API key is valid
- Check server logs

---

## 📝 Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `api_url` | https://95.216.5.123/api/v1 | API server URL |
| `ws_url` | wss://95.216.5.123/api/v1/ws | WebSocket server URL |
| `api_key` | (empty) | Your API key |
| `update_rate_hz` | 60 | Update frequency (Hz) |
| `auto_start` | true | Auto-start on launch |
| `enable_logging` | true | Enable debug logging |

---

## 🎯 Performance

- **CPU Usage**: < 1%
- **RAM Usage**: ~50 MB
- **Network**: ~10 KB/s at 60Hz
- **Latency**: < 50ms

---

## 📄 License

Copyright © 2025 MyRacingData. All rights reserved.

---

## 🆘 Support

Need help?
- Website: https://95.216.5.123/
- Documentation: https://95.216.5.123/docs

---

**Version**: 1.0.0
**Platform**: Windows 10/11
**Games**: Assetto Corsa, Le Mans Ultimate
