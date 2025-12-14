"""
Settings Window for MyRacingData Telemetry Capture
"""

import tkinter as tk
from tkinter import ttk, messagebox

class SettingsWindow:
    """Settings configuration window"""
    
    def __init__(self, parent, config):
        self.config = config
        self.window = tk.Toplevel(parent)
        self.window.title("Settings - MyRacingData")
        self.window.geometry("600x500")
        self.window.resizable(False, False)
        
        # Dark theme colors
        self.colors = {
            'bg': '#0a0a0a',
            'surface': '#1e1e1e',
            'card': '#2a2a2a',
            'primary': '#ef4444',
            'text': '#ffffff',
            'text_secondary': '#9ca3af',
        }
        
        self.setup_ui()
        self.load_settings()
        
        # Make modal
        self.window.transient(parent)
        self.window.grab_set()
        
    def setup_ui(self):
        """Setup UI"""
        self.window.configure(bg=self.colors['bg'])
        
        # Header
        header = tk.Frame(self.window, bg=self.colors['surface'])
        header.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(
            header,
            text="⚙ Settings",
            font=("Arial", 16, "bold"),
            bg=self.colors['surface'],
            fg=self.colors['text']
        )
        title.pack(pady=20, padx=20, anchor=tk.W)
        
        # Content
        content = tk.Frame(self.window, bg=self.colors['bg'])
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        
        # API Configuration
        self.create_section(content, "API Configuration")
        
        self.create_field(content, "API URL:", "api_url")
        self.create_field(content, "WebSocket URL:", "ws_url")
        self.create_field(content, "API Key:", "api_key", show="*")
        
        # Capture Settings
        self.create_section(content, "Capture Settings", pady=(20, 10))
        
        self.create_field(content, "Update Rate (Hz):", "update_rate_hz")
        
        # Buttons
        button_frame = tk.Frame(self.window, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, padx=30, pady=(0, 30))
        
        save_btn = tk.Button(
            button_frame,
            text="Save Settings",
            font=("Arial", 11, "bold"),
            bg=self.colors['primary'],
            fg=self.colors['text'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.save_settings,
            width=15,
            height=2
        )
        save_btn.pack(side=tk.RIGHT)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            font=("Arial", 11),
            bg=self.colors['card'],
            fg=self.colors['text'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.window.destroy,
            width=15,
            height=2
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
    def create_section(self, parent, title, pady=(0, 10)):
        """Create section title"""
        label = tk.Label(
            parent,
            text=title,
            font=("Arial", 12, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text'],
            anchor=tk.W
        )
        label.pack(fill=tk.X, pady=pady)
        
    def create_field(self, parent, label, key, show=None):
        """Create input field"""
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(fill=tk.X, pady=5)
        
        label_widget = tk.Label(
            frame,
            text=label,
            font=("Arial", 10),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary'],
            width=20,
            anchor=tk.W
        )
        label_widget.pack(side=tk.LEFT)
        
        entry = tk.Entry(
            frame,
            font=("Arial", 10),
            bg=self.colors['card'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            relief=tk.FLAT,
            show=show
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        
        setattr(self, f"{key}_entry", entry)
        
    def load_settings(self):
        """Load current settings"""
        self.api_url_entry.insert(0, self.config.get('api_url', ''))
        self.ws_url_entry.insert(0, self.config.get('ws_url', ''))
        self.api_key_entry.insert(0, self.config.get('api_key', ''))
        self.update_rate_hz_entry.insert(0, str(self.config.get('update_rate_hz', 60)))
        
    def save_settings(self):
        """Save settings"""
        try:
            # Validate
            update_rate = int(self.update_rate_hz_entry.get())
            if update_rate < 1 or update_rate > 120:
                raise ValueError("Update rate must be between 1 and 120")
            
            # Save
            self.config.set('api_url', self.api_url_entry.get())
            self.config.set('ws_url', self.ws_url_entry.get())
            self.config.set('api_key', self.api_key_entry.get())
            self.config.set('update_rate_hz', update_rate)
            
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully!")
            self.window.destroy()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
