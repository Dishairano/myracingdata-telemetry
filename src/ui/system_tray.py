"""
System Tray Application
"""

import sys
from pathlib import Path

try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
except ImportError:
    print("❌ pystray or Pillow not installed")
    print("   Run: pip install pystray Pillow")
    sys.exit(1)

class SystemTrayApp:
    """System tray application for telemetry capture"""
    
    def __init__(self, capture_app):
        self.capture_app = capture_app
        self.icon = None
        self.running = False
    
    def run(self):
        """Start the system tray application"""
        # Create icon
        image = self._create_icon()
        
        # Create menu
        menu = (
            item('Start Capture', self._on_start, default=True),
            item('Stop Capture', self._on_stop),
            item('Status', self._on_status),
            item('Settings', self._on_settings),
            pystray.Menu.SEPARATOR,
            item('Exit', self._on_exit)
        )
        
        # Create system tray icon
        self.icon = pystray.Icon(
            "MyRacingData",
            image,
            "MyRacingData Telemetry Capture",
            menu
        )
        
        # Auto-start if configured
        if self.capture_app.config.get('auto_start', False):
            self.capture_app.start()
        
        # Run
        self.running = True
        self.icon.run()
    
    def _create_icon(self):
        """Create application icon"""
        # Create a simple icon with lightning bolt
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw red circle
        dc.ellipse([4, 4, 60, 60], fill=(239, 68, 68, 255))
        
        # Draw lightning bolt (simplified)
        bolt = [
            (32, 16),
            (26, 32),
            (32, 32),
            (28, 48),
            (36, 32),
            (32, 32),
            (38, 16)
        ]
        dc.polygon(bolt, fill=(255, 255, 255, 255))
        
        return image
    
    def _on_start(self, icon, item):
        """Start capture"""
        if not self.capture_app.running:
            success = self.capture_app.start()
            if success:
                self._notify("Capture Started", "Waiting for game...")
            else:
                self._notify("Error", "Failed to start capture")
    
    def _on_stop(self, icon, item):
        """Stop capture"""
        if self.capture_app.running:
            self.capture_app.stop()
            self._notify("Capture Stopped", "Telemetry capture stopped")
    
    def _on_status(self, icon, item):
        """Show status"""
        status = self.capture_app.get_status()
        
        if status['running']:
            game = status['game'] or 'None'
            connected = "Yes" if status['connected'] else "No"
            message = f"Game: {game}\nConnected: {connected}\nPackets: {status['data_count']}"
        else:
            message = "Not running"
        
        self._notify("Status", message)
    
    def _on_settings(self, icon, item):
        """Open settings"""
        # TODO: Create settings window
        self._notify("Settings", "Settings window coming soon!\n\nEdit config.json in:\n" + 
                    str(self.capture_app.config.config_dir))
    
    def _on_exit(self, icon, item):
        """Exit application"""
        self.capture_app.stop()
        self.running = False
        icon.stop()
    
    def _notify(self, title, message):
        """Show notification"""
        if self.icon:
            self.icon.notify(message, title)
