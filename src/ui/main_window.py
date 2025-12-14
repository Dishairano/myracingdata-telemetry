"""
Main GUI Window for MyRacingData Telemetry Capture
Modern, professional interface with dark theme
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime

class MainWindow:
    """Main application window"""
    
    def __init__(self, capture_app):
        self.capture_app = capture_app
        self.root = tk.Tk()
        self.root.title("MyRacingData Telemetry Capture")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Dark theme colors
        self.colors = {
            'bg': '#0a0a0a',
            'surface': '#1e1e1e',
            'card': '#2a2a2a',
            'primary': '#ef4444',
            'primary_dark': '#dc2626',
            'success': '#10b981',
            'text': '#ffffff',
            'text_secondary': '#9ca3af',
            'border': '#374151'
        }
        
        self.setup_ui()
        self.update_status()
        
    def setup_ui(self):
        """Setup the user interface"""
        
        # Configure root window
        self.root.configure(bg=self.colors['bg'])
        
        # Header
        self.create_header()
        
        # Main content area
        self.create_main_content()
        
        # Footer
        self.create_footer()
        
    def create_header(self):
        """Create header with logo and title"""
        header = tk.Frame(self.root, bg=self.colors['surface'], height=80)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)
        
        # Logo and title
        title_frame = tk.Frame(header, bg=self.colors['surface'])
        title_frame.pack(side=tk.LEFT, padx=20, pady=20)
        
        logo_label = tk.Label(
            title_frame,
            text="⚡",
            font=("Arial", 32),
            bg=self.colors['surface'],
            fg=self.colors['primary']
        )
        logo_label.pack(side=tk.LEFT, padx=(0, 10))
        
        title_label = tk.Label(
            title_frame,
            text="MyRacingData",
            font=("Arial", 20, "bold"),
            bg=self.colors['surface'],
            fg=self.colors['text']
        )
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(
            title_frame,
            text="Telemetry Capture",
            font=("Arial", 10),
            bg=self.colors['surface'],
            fg=self.colors['text_secondary']
        )
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Status indicator
        self.status_frame = tk.Frame(header, bg=self.colors['surface'])
        self.status_frame.pack(side=tk.RIGHT, padx=20)
        
        self.status_indicator = tk.Label(
            self.status_frame,
            text="●",
            font=("Arial", 20),
            bg=self.colors['surface'],
            fg='#6b7280'
        )
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_text = tk.Label(
            self.status_frame,
            text="Stopped",
            font=("Arial", 12, "bold"),
            bg=self.colors['surface'],
            fg=self.colors['text_secondary']
        )
        self.status_text.pack(side=tk.LEFT)
        
    def create_main_content(self):
        """Create main content area"""
        main = tk.Frame(self.root, bg=self.colors['bg'])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - Controls
        left_panel = tk.Frame(main, bg=self.colors['surface'], width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        self.create_control_panel(left_panel)
        
        # Right panel - Log
        right_panel = tk.Frame(main, bg=self.colors['surface'])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_log_panel(right_panel)
        
    def create_control_panel(self, parent):
        """Create control panel with buttons and status"""
        
        # Title
        title = tk.Label(
            parent,
            text="Control Panel",
            font=("Arial", 14, "bold"),
            bg=self.colors['surface'],
            fg=self.colors['text']
        )
        title.pack(pady=(20, 10), padx=20, anchor=tk.W)
        
        # Start/Stop buttons
        button_frame = tk.Frame(parent, bg=self.colors['surface'])
        button_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.start_button = tk.Button(
            button_frame,
            text="▶ Start Capture",
            font=("Arial", 12, "bold"),
            bg=self.colors['primary'],
            fg=self.colors['text'],
            activebackground=self.colors['primary_dark'],
            activeforeground=self.colors['text'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.start_capture,
            height=2
        )
        self.start_button.pack(fill=tk.X, pady=(0, 10))
        
        self.stop_button = tk.Button(
            button_frame,
            text="⏹ Stop Capture",
            font=("Arial", 12, "bold"),
            bg=self.colors['card'],
            fg=self.colors['text'],
            activebackground='#3a3a3a',
            activeforeground=self.colors['text'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.stop_capture,
            height=2,
            state=tk.DISABLED
        )
        self.stop_button.pack(fill=tk.X)
        
        # Separator
        sep = tk.Frame(parent, bg=self.colors['border'], height=1)
        sep.pack(fill=tk.X, pady=20, padx=20)
        
        # Status information
        status_title = tk.Label(
            parent,
            text="Status Information",
            font=("Arial", 12, "bold"),
            bg=self.colors['surface'],
            fg=self.colors['text']
        )
        status_title.pack(pady=(0, 10), padx=20, anchor=tk.W)
        
        # Status cards
        self.create_status_card(parent, "Game Detected:", "None", "game_status")
        self.create_status_card(parent, "Connection:", "Disconnected", "connection_status")
        self.create_status_card(parent, "Packets Sent:", "0", "packets_status")
        self.create_status_card(parent, "Uptime:", "00:00:00", "uptime_status")
        
        # Separator
        sep = tk.Frame(parent, bg=self.colors['border'], height=1)
        sep.pack(fill=tk.X, pady=20, padx=20)
        
        # Settings button
        settings_btn = tk.Button(
            parent,
            text="⚙ Settings",
            font=("Arial", 10),
            bg=self.colors['card'],
            fg=self.colors['text_secondary'],
            activebackground='#3a3a3a',
            activeforeground=self.colors['text'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_settings
        )
        settings_btn.pack(pady=10, padx=20, fill=tk.X)
        
    def create_status_card(self, parent, label, value, name):
        """Create a status information card"""
        card = tk.Frame(parent, bg=self.colors['card'])
        card.pack(pady=5, padx=20, fill=tk.X)
        
        label_widget = tk.Label(
            card,
            text=label,
            font=("Arial", 9),
            bg=self.colors['card'],
            fg=self.colors['text_secondary'],
            anchor=tk.W
        )
        label_widget.pack(side=tk.LEFT, padx=10, pady=8)
        
        value_widget = tk.Label(
            card,
            text=value,
            font=("Arial", 9, "bold"),
            bg=self.colors['card'],
            fg=self.colors['text'],
            anchor=tk.E
        )
        value_widget.pack(side=tk.RIGHT, padx=10, pady=8)
        
        setattr(self, name, value_widget)
        
    def create_log_panel(self, parent):
        """Create log output panel"""
        
        # Title
        title = tk.Label(
            parent,
            text="Activity Log",
            font=("Arial", 14, "bold"),
            bg=self.colors['surface'],
            fg=self.colors['text']
        )
        title.pack(pady=(20, 10), padx=20, anchor=tk.W)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(
            parent,
            font=("Consolas", 9),
            bg=self.colors['bg'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Configure tags for colored output
        self.log_text.tag_config('info', foreground='#60a5fa')
        self.log_text.tag_config('success', foreground='#10b981')
        self.log_text.tag_config('warning', foreground='#f59e0b')
        self.log_text.tag_config('error', foreground='#ef4444')
        
    def create_footer(self):
        """Create footer"""
        footer = tk.Frame(self.root, bg=self.colors['surface'], height=40)
        footer.pack(fill=tk.X)
        footer.pack_propagate(False)
        
        footer_text = tk.Label(
            footer,
            text="MyRacingData Telemetry Capture v1.0.0 | https://myracingdata.com",
            font=("Arial", 8),
            bg=self.colors['surface'],
            fg=self.colors['text_secondary']
        )
        footer_text.pack(side=tk.LEFT, padx=20)
        
    def log(self, message, level='info'):
        """Add message to log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted, level)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def start_capture(self):
        """Start telemetry capture"""
        success = self.capture_app.start()
        
        if success:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_indicator.config(fg=self.colors['success'])
            self.status_text.config(text="Running", fg=self.colors['success'])
            self.log("Telemetry capture started", 'success')
        else:
            self.log("Failed to start capture - check API key configuration", 'error')
            messagebox.showerror(
                "Start Failed",
                "Failed to start capture.\n\nPlease check:\n- API key is configured\n- Internet connection"
            )
            
    def stop_capture(self):
        """Stop telemetry capture"""
        self.capture_app.stop()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_indicator.config(fg='#6b7280')
        self.status_text.config(text="Stopped", fg=self.colors['text_secondary'])
        self.log("Telemetry capture stopped", 'info')
        
    def update_status(self):
        """Update status information"""
        if hasattr(self, 'game_status'):
            status = self.capture_app.get_status()
            
            # Update game detection
            game = status.get('game', 'None')
            if game == 'ac':
                game = 'Assetto Corsa'
            elif game == 'lmu':
                game = 'Le Mans Ultimate'
            self.game_status.config(text=game)
            
            # Update connection
            connected = status.get('connected', False)
            self.connection_status.config(
                text="Connected" if connected else "Disconnected",
                fg=self.colors['success'] if connected else self.colors['text']
            )
            
            # Update packets
            packets = status.get('data_count', 0)
            self.packets_status.config(text=f"{packets:,}")
            
            # Update uptime
            if status.get('running', False):
                # Calculate uptime (simplified)
                uptime = "Running"
                self.uptime_status.config(text=uptime)
        
        # Schedule next update
        self.root.after(1000, self.update_status)
        
    def open_settings(self):
        """Open settings window"""
        from .settings_window import SettingsWindow
        SettingsWindow(self.root, self.capture_app.config)
        
    def run(self):
        """Run the GUI"""
        # Center window
        self.center_window()
        
        # Log initial message
        self.log("MyRacingData Telemetry Capture initialized", 'success')
        self.log("Click 'Start Capture' to begin streaming telemetry", 'info')
        
        # Start main loop
        self.root.mainloop()
        
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
