"""
MyRacingData Telemetry Capture
Main application entry point
"""

import sys
import time
import threading
from collections import deque
from pathlib import Path

import urllib3
# The API has a valid cert; requests still uses verify=False (legacy), which
# otherwise floods the log with InsecureRequestWarning. Quiet it.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def _setup_logging():
    """In a windowed (no-console) build stdout/stderr are None, so the app's
    print()s would crash. Redirect them to a rotating-ish log file."""
    try:
        log_dir = Path.home() / '.myracingdata'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = open(log_dir / 'client.log', 'a', buffering=1, encoding='utf-8', errors='replace')
        if sys.stdout is None:
            sys.stdout = log_file
        if sys.stderr is None:
            sys.stderr = log_file
    except Exception:
        pass


_setup_logging()

from config import Config
from capture.canonical import normalize
from games.ac import ACTelemetry
from games.acc_shared_memory import ACCSharedMemoryReader
from games.lmu import LMUTelemetry
from network.websocket_client import WebSocketClient
from ui.system_tray import SystemTrayApp

class TelemetryCapture:
    """Main telemetry capture application"""
    
    def __init__(self):
        self.config = Config()
        self.ac = ACTelemetry()
        self.lmu = LMUTelemetry()
        self.acc = ACCSharedMemoryReader()
        self.ws_client = None
        self.active_game = None
        self.running = False
        self.capture_thread = None
        self.sender_thread = None
        self.monitor_thread = None
        self.data_count = 0
        self.last_status_update = 0
        self.session_id = None
        self.last_frame = None  # most recent normalized frame, for the UI readout
        self.log_callback = None  # Store callback for use in capture loop

        # Decouple capture from network: the reader thread samples shared memory
        # at the configured Hz into this buffer; the sender thread drains it in
        # batches. Keeps sample timing steady at 120Hz (a blocking WS send in the
        # read loop would jitter/drop frames). Bounded so it can't grow forever
        # if the network stalls.
        self._send_buf = deque(maxlen=2400)
        self._buf_lock = threading.Lock()

        print(f"🏁 MyRacingData Telemetry Capture v{Config.VERSION}")
        print("=" * 60)
        print(f"✓ Assetto Corsa support: Enabled")
        print(f"✓ Le Mans Ultimate support: Enabled")
        print(f"✓ Assetto Corsa Competizione support: Enabled (shared memory)")
    
    def start(self, log_callback=None):
        """Start telemetry capture"""
        import requests
        import json as json_module

        # Store callback for use in capture loop
        self.log_callback = log_callback

        def log(msg):
            print(msg)
            if log_callback:
                log_callback(msg)

        log("\n" + "="*60)
        log("DEBUG: Starting telemetry capture...")
        log("="*60)

        if self.running:
            log("⚠ Already running")
            return False

        # Check for API key
        log(f"DEBUG: Checking API key...")
        log(f"DEBUG: API key exists: {bool(self.config.api_key)}")
        if self.config.api_key:
            log(f"DEBUG: API key value: {self.config.api_key[:20]}...")
        log(f"DEBUG: API URL: {self.config.api_url}")

        if not self.config.api_key:
            log("❌ No API key configured!")
            log("   Please set your API key in the settings")
            return False

        # No session is created up front. The monitor thread creates one (with
        # the real track/car) when a sim session goes live, and ends it when the
        # sim leaves to the menu/exits — so each on-track session is its own
        # backend session.
        self.session_id = None
        self.ws_client = None

        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        self.sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
        self.sender_thread.start()
        self.monitor_thread = threading.Thread(target=self._session_monitor, daemon=True)
        self.monitor_thread.start()

        log("✓ Capture started — waiting for a sim session…")
        return True

    def _session_monitor(self):
        """Create/end a backend session as the sim enters/leaves a live session.

        active_game is set by the reader when a sim session is live and cleared
        when it ends (sim status goes OFF). We mirror that into one backend
        session per on-track session.
        """
        while self.running:
            time.sleep(0.5)
            try:
                if self.active_game and not self.session_id:
                    self._begin_session()
                elif not self.active_game and self.session_id:
                    self._end_session('sim session ended')
            except Exception as e:
                self._log(f"⚠ Session monitor error: {e}")

    def _begin_session(self):
        """Create a backend session for the currently-detected sim + connect WS."""
        import requests
        reader = {'ac': self.ac, 'acc': self.acc, 'lmu': self.lmu}.get(self.active_game)
        track = getattr(reader, 'track_name', None) or 'Unknown'
        car = getattr(reader, 'car_name', None) or 'Unknown'
        game = self.active_game

        try:
            resp = requests.post(
                f"{self.config.api_url}/sessions",
                headers={'Authorization': f'Bearer {self.config.api_key}', 'Content-Type': 'application/json'},
                json={'track_name': track, 'car_name': car, 'game': game},
                verify=False, timeout=10,
            )
            if resp.status_code != 201:
                self._log(f"❌ Failed to create session: {resp.status_code}")
                return
            data = resp.json()
            sid = data.get('session', {}).get('id') or data.get('id')
            if not sid:
                return

            ws = WebSocketClient(f"{self.config.ws_url}/session/{sid}", self.config.api_key)
            if not ws.connect():
                self._log("❌ WebSocket connection failed")
                return

            with self._buf_lock:
                self._send_buf.clear()  # drop any pre-session frames
            self.session_id = sid
            self.ws_client = ws
            self.data_count = 0
            self.last_status_update = 0
            self._log(f"🏁 Session started — {track} · {car}")
        except Exception as e:
            self._log(f"❌ Session start failed: {e}")

    def _end_session(self, reason=''):
        """End the current backend session and close its WebSocket."""
        import requests
        sid = self.session_id
        ws = self.ws_client
        self.session_id = None
        self.ws_client = None
        if ws:
            try:
                ws.disconnect()
            except Exception:
                pass
        if sid:
            try:
                requests.patch(
                    f"{self.config.api_url}/sessions/{sid}/end",
                    headers={'Authorization': f'Bearer {self.config.api_key}'},
                    verify=False, timeout=5,
                )
            except Exception:
                pass
            self._log(f"⏹ Session ended ({reason}) — {self.data_count:,} samples")

    def stop(self):
        """Stop telemetry capture"""
        import requests

        if not self.running:
            return

        print("⏹ Stopping telemetry capture...")
        self.running = False

        # End the active backend session (if any)
        if self.session_id:
            self._end_session('stopped')

        # Disconnect games
        if self.ac.is_connected:
            self.ac.disconnect()
        if self.lmu.is_connected:
            self.lmu.disconnect()
        if self.acc.is_connected:
            self.acc.disconnect()

        self.active_game = None
        print("✓ Stopped")
    
    def _capture_loop(self):
        """Reader: sample shared memory at the configured Hz into the buffer.

        Only reads + normalizes (cheap); the network send happens on the sender
        thread so a blocking WS write can't disturb the sample timing at 120Hz.
        """
        update_interval = 1.0 / self.config.update_rate_hz

        while self.running:
            loop_start = time.time()

            raw = self._read_telemetry()
            frame = normalize(self.active_game, raw)
            if frame:
                self.last_frame = frame
                with self._buf_lock:
                    self._send_buf.append(frame)

            elapsed = time.time() - loop_start
            time.sleep(max(0, update_interval - elapsed))

    def _sender_loop(self):
        """Sender: drain the buffer and ship it as telemetry batches (~20/s)."""
        SEND_INTERVAL = 0.05  # seconds between batches

        while self.running:
            time.sleep(SEND_INTERVAL)

            with self._buf_lock:
                if not self._send_buf:
                    continue
                batch = list(self._send_buf)
                self._send_buf.clear()

            # Snapshot the client — the monitor thread may swap/clear it between
            # sessions. If there's no active session, the batch is simply dropped.
            ws = self.ws_client
            if ws and ws.is_connected:
                ws.send_batch(batch)
                self.data_count += len(batch)

                if time.time() - self.last_status_update > 5:
                    last = batch[-1]
                    self._log(f"📊 Capturing: {last['game']} | "
                              f"Speed: {last.get('speed_kmh', 0):.1f} km/h | "
                              f"Packets sent: {self.data_count}")
                    self.last_status_update = time.time()


    def _log(self, msg):
        """Helper to log to both console and GUI"""
        print(msg)
        if self.log_callback:
            self.log_callback(msg)

    def _read_telemetry(self):
        """Try to read telemetry from games"""

        # If we have an active game, keep reading from it. read() returning None
        # just means "no new frame this tick" — the sim hasn't advanced its
        # packet id yet (e.g. car in the menu/garage). That is NOT a disconnect,
        # so we keep polling. A reader only flips is_connected to False on an
        # actual shared-memory error (sim closed), which sends us back to detect.
        readers = {'ac': self.ac, 'acc': self.acc, 'lmu': self.lmu}
        labels = {'ac': 'Assetto Corsa', 'acc': 'Assetto Corsa Competizione',
                  'lmu': 'Le Mans Ultimate'}
        if self.active_game in readers:
            reader = readers[self.active_game]
            if reader.is_connected:
                return reader.read()
            self._log(f"⚠ {labels[self.active_game]} disconnected")
            self.active_game = None
            return None

        # No active game, try to detect one. ACC (the launch sim) is tried first
        # so it gets its own full-channel reader; AC and ACC share the same
        # shared-memory names, so whichever is tried first claims a live session.
        else:
            # Try ACC (shared memory, full channels)
            if self.acc.connect():
                self.active_game = 'acc'
                self._log("✓ Assetto Corsa Competizione detected!")
                return None

            # Try Assetto Corsa
            if self.ac.connect():
                self.active_game = 'ac'
                self._log("✓ Assetto Corsa detected!")
                return None

            # Try Le Mans Ultimate
            if self.lmu.connect():
                self.active_game = 'lmu'
                self._log("✓ Le Mans Ultimate detected!")
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

    def ui_state(self):
        """Full state for the UI: status + the latest live readout."""
        f = self.last_frame or {}
        game_labels = {
            'ac': 'Assetto Corsa', 'acc': 'Assetto Corsa Competizione', 'lmu': 'Le Mans Ultimate',
        }
        return {
            'running': self.running,
            'game': self.active_game,
            'game_label': game_labels.get(self.active_game, '—'),
            'connected': bool(self.ws_client and self.ws_client.is_connected),
            'data_count': self.data_count,
            'session_id': self.session_id,
            'hz': self.config.update_rate_hz,
            'has_key': bool(self.config.api_key),
            'version': Config.VERSION,
            'speed': round(f.get('speed_kmh', 0) or 0, 1),
            'rpm': int(f.get('rpm', 0) or 0),
            'gear': f.get('gear', 0),
            'throttle': round(f.get('throttle_input', 0) or 0),
            'brake': round(f.get('brake_input', 0) or 0),
            'lap': f.get('lap_number', 0),
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
        # GUI mode — modern PyWebView UI first; fall back to the classic tkinter
        # UI (then system tray) if the webview runtime isn't available.
        try:
            from ui.webview_app import run_webview
            run_webview(app)
            app.stop()
            return
        except Exception as e:
            print(f"⚠ Modern UI unavailable ({e}); falling back to classic UI")

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
