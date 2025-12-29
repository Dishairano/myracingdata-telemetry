"""
WebSocket client for real-time telemetry streaming
"""

import json
import time
import threading
from typing import Optional, Callable
import websocket

class WebSocketClient:
    """WebSocket client for MyRacingData platform"""
    
    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key
        self.ws = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 2
        self.running = False
        self.on_connected = None
        self.on_disconnected = None
        self.thread = None
    
    def connect(self):
        """Connect to WebSocket server"""
        try:
            # Add API key to URL
            ws_url = f"{self.url}?api_key={self.api_key[:20]}..."
            print(f"DEBUG WS: Connecting to: {ws_url}")

            # Use full API key for actual connection
            full_ws_url = f"{self.url}?api_key={self.api_key}"

            self.ws = websocket.WebSocketApp(
                full_ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )

            # Run in separate thread
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

            # Wait a bit for connection
            print("DEBUG WS: Waiting for connection...")
            time.sleep(2)  # Increased wait time

            print(f"DEBUG WS: Connection status: {self.connected}")
            return self.connected

        except Exception as e:
            print(f"WebSocket connection error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def disconnect(self):
        """Disconnect from WebSocket server"""
        self.running = False
        if self.ws:
            self.ws.close()
        self.connected = False
    
    def send_telemetry(self, data: dict):
        """Send telemetry data to server"""
        if not self.connected or not self.ws:
            return False
        
        try:
            message = json.dumps({
                'type': 'telemetry',
                'data': data
            })
            self.ws.send(message)
            return True
        except Exception as e:
            print(f"Error sending telemetry: {e}")
            return False
    
    def _run(self):
        """Run WebSocket connection loop"""
        while self.running:
            try:
                self.ws.run_forever()
            except Exception as e:
                print(f"WebSocket error: {e}")
            
            # Reconnect logic
            if self.running and self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                print(f"Reconnecting... (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
                time.sleep(self.reconnect_delay * self.reconnect_attempts)
            else:
                break
    
    def _on_open(self, ws):
        """Called when connection is established"""
        print("✓ WebSocket connected")
        self.connected = True
        self.reconnect_attempts = 0
        
        if self.on_connected:
            self.on_connected()
    
    def _on_message(self, ws, message):
        """Called when message is received"""
        try:
            data = json.loads(message)
            # Handle server messages if needed
            if data.get('type') == 'ping':
                ws.send(json.dumps({'type': 'pong'}))
        except:
            pass
    
    def _on_error(self, ws, error):
        """Called on error"""
        print(f"DEBUG WS ERROR: {error}")
        print(f"DEBUG WS ERROR TYPE: {type(error)}")
        import traceback
        traceback.print_exc()
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Called when connection is closed"""
        print(f"WebSocket disconnected: {close_status_code} - {close_msg}")
        self.connected = False
        
        if self.on_disconnected:
            self.on_disconnected()
    
    @property
    def is_connected(self) -> bool:
        return self.connected
