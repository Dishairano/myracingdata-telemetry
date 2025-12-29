"""
MyRacingData Telemetry Capture
Main application entry point
"""

import sys
import time
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from games.ac import ACTelemetry
from games.lmu import LMUTelemetry
from network.websocket_client import WebSocketClient
from ui.system_tray import SystemTrayApp

# Try to import ACC - it's optional
try:
    from games.acc import ACCTelemetryReader
    ACC_AVAILABLE = True
except ImportError:
    ACCTelemetryReader = None
    ACC_AVAILABLE = False
    print("⚠ ACC support not available (accapi not installed)")

class TelemetryCapture:
    """Main telemetry capture application"""
    
    def __init__(self):
        self.config = Config()
        self.ac = ACTelemetry()
        self.lmu = LMUTelemetry()
        self.acc = ACCTelemetryReader() if ACC_AVAILABLE else None
        self.ws_client = None
        self.active_game = None
        self.running = False
        self.capture_thread = None
        self.data_count = 0
        self.last_status_update = 0

        print(f"🏁 MyRacingData Telemetry Capture v{Config.VERSION}")
        print("=" * 60)
        print(f"✓ Assetto Corsa support: Enabled")
        print(f"✓ Le Mans Ultimate support: Enabled")
        print(f"{'✓' if ACC_AVAILABLE else '✗'} Assetto Corsa Competizione support: {'Enabled' if ACC_AVAILABLE else 'Disabled (accapi not installed)'}")
    
    def start(self):
        """Start telemetry capture"""
        print("\n" + "="*60)
        print("DEBUG: Starting telemetry capture...")
        print("="*60)

        if self.running:
            print("⚠ Already running")
            return False

        # Check for API key
        print(f"DEBUG: Checking API key...")
        print(f"DEBUG: API key exists: {bool(self.config.api_key)}")
        if self.config.api_key:
            print(f"DEBUG: API key value: {self.config.api_key[:20]}...")
        print(f"DEBUG: API URL: {self.config.api_url}")
        print(f"DEBUG: WS URL: {self.config.ws_url}")

        if not self.config.api_key:
            print("❌ No API key configured!")
            print("   Please set your API key in the settings")
            return False

        # Connect to WebSocket
        print(f"🔌 Connecting to {self.config.ws_url}...")
        self.ws_client = WebSocketClient(
            self.config.ws_url,
            self.config.api_key
        )

        print("DEBUG: Attempting WebSocket connection...")
        connection_result = self.ws_client.connect()
        print(f"DEBUG: WebSocket connection result: {connection_result}")

        if not connection_result:
            print("❌ Failed to connect to server")
            print(f"DEBUG: WebSocket client connected state: {self.ws_client.connected}")
            return False
        
        # Start capture thread
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        print("✓ Telemetry capture started")
        print("   Waiting for game to start...")
        return True
    
    def stop(self):
        """Stop telemetry capture"""
        if not self.running:
            return

        print("⏹ Stopping telemetry capture...")
        self.running = False

        # Disconnect games
        if self.ac.is_connected:
            self.ac.disconnect()
        if self.lmu.is_connected:
            self.lmu.disconnect()
        if self.acc and self.acc.is_connected():
            self.acc.stop()

        # Disconnect WebSocket
        if self.ws_client:
            self.ws_client.disconnect()

        self.active_game = None
        print("✓ Stopped")
    
    def _capture_loop(self):
        """Main capture loop - runs at configured Hz"""
        update_interval = 1.0 / self.config.update_rate_hz
        
        while self.running:
            loop_start = time.time()
            
            # Try to detect and read from games
            data = self._read_telemetry()
            
            if data:
                # Send to server
                if self.ws_client and self.ws_client.is_connected:
                    self.ws_client.send_telemetry(data)
                    self.data_count += 1
                    
                    # Print status every 5 seconds
                    if time.time() - self.last_status_update > 5:
                        print(f"📊 Capturing: {data['game']} | "
                              f"Speed: {data.get('speed_kmh', 0):.1f} km/h | "
                              f"Packets sent: {self.data_count}")
                        self.last_status_update = time.time()
            
            # Sleep to maintain update rate
            elapsed = time.time() - loop_start
            sleep_time = max(0, update_interval - elapsed)
            time.sleep(sleep_time)
    
    def _read_telemetry(self):
        """Try to read telemetry from games"""

        # If we have an active game, try to read from it
        if self.active_game == 'ac' and self.ac.is_connected:
            data = self.ac.read()
            if data:
                return data
            # Connection lost
            self.ac.disconnect()
            self.active_game = None
            print("⚠ Assetto Corsa disconnected")

        elif self.active_game == 'acc' and self.acc and self.acc.is_connected():
            data = self.acc.get_latest_telemetry()
            if data:
                return data
            # Connection lost
            self.acc.stop()
            self.active_game = None
            print("⚠ Assetto Corsa Competizione disconnected")

        elif self.active_game == 'lmu' and self.lmu.is_connected:
            data = self.lmu.read()
            if data:
                return data
            # Connection lost
            self.lmu.disconnect()
            self.active_game = None
            print("⚠ Le Mans Ultimate disconnected")

        # No active game, try to detect one
        else:
            # Try Assetto Corsa
            if self.ac.connect():
                self.active_game = 'ac'
                print("✓ Assetto Corsa detected!")
                return None

            # Try ACC (only if available)
            if ACC_AVAILABLE and self.acc and self.acc.start():
                self.active_game = 'acc'
                print("✓ Assetto Corsa Competizione detected!")
                return None

            # Try Le Mans Ultimate
            if self.lmu.connect():
                self.active_game = 'lmu'
                print("✓ Le Mans Ultimate detected!")
                return None

        return None
    
    def get_status(self):
        """Get current status"""
        return {
            'running': self.running,
            'game': self.active_game,
            'connected': self.ws_client and self.ws_client.is_connected if self.ws_client else False,
            'data_count': self.data_count
        }

def main():
    """Main entry point"""
    
    # Create application
    app = TelemetryCapture()
    
    # Check if running with GUI
    if '--no-gui' in sys.argv:
        # Console mode
        print("Running in console mode (Ctrl+C to stop)")
        
        try:
            app.start()
            
            # Keep running
            while True:
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n⏹ Stopping...")
            app.stop()
            sys.exit(0)
    
    else:
        # GUI mode
        try:
            # Login first (one-time)
            from ui.login_window import LoginWindow
            
            login = LoginWindow(app.config)
            authenticated = login.run()
            
            if not authenticated:
                print("❌ Authentication required to use the application")
                sys.exit(1)
            
            # Open main window after successful login
            from ui.main_window import MainWindow
            
            gui = MainWindow(app)
            gui.run()
            
        except Exception as e:
            print(f"❌ Failed to start GUI: {e}")
            print("   Falling back to system tray mode...")
            
            try:
                tray_app = SystemTrayApp(app)
                tray_app.run()
            except Exception as e2:
                print(f"❌ Failed to start system tray: {e2}")
                print("   Try running with --no-gui flag for console mode")
                sys.exit(1)

if __name__ == '__main__':
    main()
