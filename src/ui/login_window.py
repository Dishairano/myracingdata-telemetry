"""
Login Window for MyRacingData Telemetry Capture
One-time authentication before using the app
"""

import tkinter as tk
from tkinter import messagebox
import requests
import json
from pathlib import Path

class LoginWindow:
    """Login/Authentication window"""
    
    def __init__(self, config):
        self.config = config
        self.authenticated = False
        self.user_data = None
        
        self.root = tk.Tk()
        self.root.title("MyRacingData - Login")
        self.root.geometry("500x650")
        self.root.resizable(False, False)
        
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
        
    def setup_ui(self):
        """Setup UI"""
        self.root.configure(bg=self.colors['bg'])
        
        # Header with logo
        header = tk.Frame(self.root, bg=self.colors['bg'])
        header.pack(pady=(40, 20))
        
        logo = tk.Label(
            header,
            text="⚡",
            font=("Arial", 48),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        )
        logo.pack()
        
        title = tk.Label(
            header,
            text="MyRacingData",
            font=("Arial", 24, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        title.pack()
        
        subtitle = tk.Label(
            header,
            text="Telemetry Capture",
            font=("Arial", 12),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        )
        subtitle.pack()
        
        # Login card
        card = tk.Frame(self.root, bg=self.colors['surface'])
        card.pack(pady=20, padx=60, fill=tk.BOTH)
        
        card_title = tk.Label(
            card,
            text="Sign in to continue",
            font=("Arial", 14, "bold"),
            bg=self.colors['surface'],
            fg=self.colors['text']
        )
        card_title.pack(pady=(30, 20))
        
        # Email field
        self.create_input_field(card, "Email or Username", "email")
        
        # Password field
        self.create_input_field(card, "Password", "password", show="*")
        
        # Remember me checkbox
        remember_frame = tk.Frame(card, bg=self.colors['surface'])
        remember_frame.pack(pady=10, padx=30, fill=tk.X)
        
        self.remember_var = tk.BooleanVar(value=True)
        remember_check = tk.Checkbutton(
            remember_frame,
            text="Remember me",
            variable=self.remember_var,
            font=("Arial", 9),
            bg=self.colors['surface'],
            fg=self.colors['text_secondary'],
            selectcolor=self.colors['card'],
            activebackground=self.colors['surface'],
            activeforeground=self.colors['text']
        )
        remember_check.pack(side=tk.LEFT)
        
        # Login button
        self.login_button = tk.Button(
            card,
            text="Sign In",
            font=("Arial", 12, "bold"),
            bg=self.colors['primary'],
            fg=self.colors['text'],
            activebackground=self.colors['primary_dark'],
            activeforeground=self.colors['text'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.login,
            height=2
        )
        self.login_button.pack(pady=20, padx=30, fill=tk.X)
        
        # Or use API key
        separator_frame = tk.Frame(card, bg=self.colors['surface'])
        separator_frame.pack(pady=10, fill=tk.X, padx=30)
        
        sep_left = tk.Frame(separator_frame, bg=self.colors['border'], height=1)
        sep_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        sep_text = tk.Label(
            separator_frame,
            text="or",
            font=("Arial", 9),
            bg=self.colors['surface'],
            fg=self.colors['text_secondary']
        )
        sep_text.pack(side=tk.LEFT, padx=10)
        
        sep_right = tk.Frame(separator_frame, bg=self.colors['border'], height=1)
        sep_right.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # API Key option
        api_key_label = tk.Label(
            card,
            text="Use API Key",
            font=("Arial", 11, "bold"),
            bg=self.colors['surface'],
            fg=self.colors['text']
        )
        api_key_label.pack(pady=(10, 5))
        
        self.create_input_field(card, "API Key", "api_key", show="*")
        
        api_key_button = tk.Button(
            card,
            text="Continue with API Key",
            font=("Arial", 11, "bold"),
            bg=self.colors['card'],
            fg=self.colors['text'],
            activebackground='#3a3a3a',
            activeforeground=self.colors['text'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.login_with_api_key,
            height=2
        )
        api_key_button.pack(pady=15, padx=30, fill=tk.X)
        
        # Links
        links_frame = tk.Frame(card, bg=self.colors['surface'])
        links_frame.pack(pady=(10, 30))
        
        register_link = tk.Label(
            links_frame,
            text="Create Account",
            font=("Arial", 9, "underline"),
            bg=self.colors['surface'],
            fg=self.colors['primary'],
            cursor="hand2"
        )
        register_link.pack(side=tk.LEFT, padx=10)
        register_link.bind("<Button-1>", lambda e: self.open_register())
        
        forgot_link = tk.Label(
            links_frame,
            text="Get API Key",
            font=("Arial", 9, "underline"),
            bg=self.colors['surface'],
            fg=self.colors['text_secondary'],
            cursor="hand2"
        )
        forgot_link.pack(side=tk.LEFT, padx=10)
        forgot_link.bind("<Button-1>", lambda e: self.open_api_key_page())
        
        # Footer
        footer = tk.Label(
            self.root,
            text="https://myracingdata.com",
            font=("Arial", 8),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        )
        footer.pack(side=tk.BOTTOM, pady=20)
        
    def create_input_field(self, parent, placeholder, name, show=None):
        """Create input field"""
        frame = tk.Frame(parent, bg=self.colors['surface'])
        frame.pack(pady=8, padx=30, fill=tk.X)
        
        label = tk.Label(
            frame,
            text=placeholder,
            font=("Arial", 9),
            bg=self.colors['surface'],
            fg=self.colors['text_secondary'],
            anchor=tk.W
        )
        label.pack(fill=tk.X, pady=(0, 5))
        
        entry = tk.Entry(
            frame,
            font=("Arial", 11),
            bg=self.colors['card'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            relief=tk.FLAT,
            show=show
        )
        entry.pack(fill=tk.X, ipady=10)
        
        setattr(self, f"{name}_entry", entry)
        
        # Bind Enter key
        entry.bind('<Return>', lambda e: self.login() if name == 'password' else None)
        
    def login(self):
        """Login with email and password"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password")
            return
        
        # Disable button
        self.login_button.config(state=tk.DISABLED, text="Signing in...")
        self.root.update()
        
        try:
            # Login to MyRacingData API
            api_url = self.config.get('api_url', 'https://95.216.5.123/api/v1')
            
            response = requests.post(
                f"{api_url}/auth/login",
                json={'email': email, 'password': password},
                timeout=10,
                verify=False  # For self-signed cert
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Save authentication
                self.user_data = data.get('user', {})
                api_key = data.get('api_key') or data.get('token')
                
                if api_key:
                    self.config.set('api_key', api_key)
                    self.config.set('user_email', email)
                    
                    # Save auth token if remember me is checked
                    if self.remember_var.get():
                        self.save_auth_token(api_key, email)
                    
                    self.authenticated = True
                    messagebox.showinfo("Success", f"Welcome back, {self.user_data.get('name', email)}!")
                    self.root.quit()
                    self.root.destroy()
                else:
                    messagebox.showerror("Error", "Login successful but no API key received")
            else:
                error_msg = response.json().get('error', 'Invalid credentials')
                messagebox.showerror("Login Failed", error_msg)
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Could not connect to MyRacingData:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}")
        finally:
            self.login_button.config(state=tk.NORMAL, text="Sign In")
            
    def login_with_api_key(self):
        """Login with API key directly"""
        api_key = self.api_key_entry.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Please enter your API key")
            return
        
        # Validate API key
        try:
            api_url = self.config.get('api_url', 'https://95.216.5.123/api/v1')
            
            response = requests.get(
                f"{api_url}/users/me",
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                self.user_data = response.json()
                self.config.set('api_key', api_key)
                
                # Save auth token if remember me is checked
                if self.remember_var.get():
                    self.save_auth_token(api_key, self.user_data.get('email', 'user'))
                
                self.authenticated = True
                messagebox.showinfo("Success", f"Welcome, {self.user_data.get('name', 'User')}!")
                self.root.quit()
                self.root.destroy()
            else:
                messagebox.showerror("Error", "Invalid API key")
                
        except Exception as e:
            messagebox.showerror("Error", f"Validation failed: {str(e)}")
            
    def save_auth_token(self, api_key, email):
        """Save authentication token for next time"""
        auth_file = self.config.config_dir / 'auth.json'
        
        try:
            auth_data = {
                'api_key': api_key,
                'email': email,
                'authenticated': True
            }
            
            with open(auth_file, 'w') as f:
                json.dump(auth_data, f)
                
        except Exception as e:
            print(f"Could not save auth token: {e}")
            
    def check_saved_auth(self):
        """Check if there's a saved authentication"""
        auth_file = self.config.config_dir / 'auth.json'
        
        if auth_file.exists():
            try:
                with open(auth_file, 'r') as f:
                    auth_data = json.load(f)
                
                api_key = auth_data.get('api_key')
                if api_key:
                    # Validate saved key
                    api_url = self.config.get('api_url', 'https://95.216.5.123/api/v1')
                    
                    response = requests.get(
                        f"{api_url}/users/me",
                        headers={'Authorization': f'Bearer {api_key}'},
                        timeout=5,
                        verify=False
                    )
                    
                    if response.status_code == 200:
                        # Valid saved auth
                        self.user_data = response.json()
                        self.config.set('api_key', api_key)
                        self.authenticated = True
                        return True
                        
            except Exception:
                pass
        
        return False
        
    def open_register(self):
        """Open registration page"""
        import webbrowser
        webbrowser.open('https://95.216.5.123/auth/register')
        
    def open_api_key_page(self):
        """Open API key page"""
        import webbrowser
        webbrowser.open('https://95.216.5.123/settings/api-keys')
        
    def run(self):
        """Run the login window"""
        # Check for saved auth first
        if self.check_saved_auth():
            # Already authenticated, skip login
            self.root.destroy()
            return True
        
        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Run
        self.root.mainloop()
        
        return self.authenticated
