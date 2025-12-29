"""
Configuration management for MyRacingData Telemetry Capture
"""

import os
import json
from pathlib import Path

class Config:
    """Application configuration"""
    
    # Version
    VERSION = "1.0.0"
    APP_NAME = "MyRacingData Telemetry Capture"
    
    # Default settings
    DEFAULTS = {
        'api_url': 'https://myracingdata.com/api/v1',
        'ws_url': 'wss://myracingdata.com/api/v1/ws',
        'api_key': '',
        'update_rate_hz': 60,
        'buffer_size': 1000,
        'auto_start': True,
        'minimize_to_tray': True,
        'enable_logging': True
    }
    
    def __init__(self):
        self.config_dir = Path.home() / '.myracingdata'
        self.config_file = self.config_dir / 'config.json'
        self.settings = self.DEFAULTS.copy()
        self.load()
    
    def load(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    saved = json.load(f)
                    self.settings.update(saved)
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save(self):
        """Save configuration to file"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.settings[key] = value
        self.save()
    
    @property
    def api_url(self):
        return self.settings['api_url']
    
    @property
    def ws_url(self):
        return self.settings['ws_url']
    
    @property
    def api_key(self):
        return self.settings['api_key']
    
    @property
    def update_rate_hz(self):
        return self.settings['update_rate_hz']
