"""
Login Window for MyRacingData Telemetry Capture
One-time authentication before using the app.

Primary path: email + password (the account you signed up with). On success the
app obtains your long-lived API key (reusing the account's existing key, or
minting one) and saves it for the capture session. An API-key field is kept as
an advanced fallback.
"""

import tkinter as tk
from tkinter import messagebox
import requests
import json
from pathlib import Path

API_BASE = 'https://myracingdata.com/api/v1'
WS_URL = 'wss://myracingdata.com/api/v1/ws'


class LoginWindow:
    """Login/Authentication window"""

    def __init__(self, config):
        self.config = config
        self.authenticated = False
        self.user_data = None

        self.root = tk.Tk()
        self.root.title("MyRacingData - Sign In")
        self.root.geometry("500x720")
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

        self.apikey_visible = False
        self.setup_ui()

    def setup_ui(self):
        """Setup UI"""
        self.root.configure(bg=self.colors['bg'])

        # Header with logo
        header = tk.Frame(self.root, bg=self.colors['bg'])
        header.pack(pady=(36, 16))

        tk.Label(header, text="⚡", font=("Arial", 48), bg=self.colors['bg'], fg=self.colors['primary']).pack()
        tk.Label(header, text="MyRacingData", font=("Arial", 24, "bold"), bg=self.colors['bg'], fg=self.colors['text']).pack()
        tk.Label(header, text="Telemetry Capture", font=("Arial", 12), bg=self.colors['bg'], fg=self.colors['text_secondary']).pack()

        # Login card
        card = tk.Frame(self.root, bg=self.colors['surface'])
        card.pack(pady=20, padx=60, fill=tk.BOTH)

        tk.Label(card, text="Sign in", font=("Arial", 14, "bold"), bg=self.colors['surface'], fg=self.colors['text']).pack(pady=(28, 4))
        tk.Label(card, text="Use the email & password you signed up with", font=("Arial", 9), bg=self.colors['surface'], fg=self.colors['text_secondary']).pack(pady=(0, 16))

        # Email + password
        self.create_input_field(card, "Email", "email", on_enter=lambda e: self.password_entry.focus_set())
        self.create_input_field(card, "Password", "password", show="*", on_enter=lambda e: self.login())

        # Remember me
        remember_frame = tk.Frame(card, bg=self.colors['surface'])
        remember_frame.pack(pady=10, padx=30, fill=tk.X)
        self.remember_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            remember_frame, text="Remember me", variable=self.remember_var,
            font=("Arial", 9), bg=self.colors['surface'], fg=self.colors['text_secondary'],
            selectcolor=self.colors['card'], activebackground=self.colors['surface'],
            activeforeground=self.colors['text']
        ).pack(side=tk.LEFT)

        # Sign In button
        self.login_button = tk.Button(
            card, text="Sign In", font=("Arial", 12, "bold"),
            bg=self.colors['primary'], fg=self.colors['text'],
            activebackground=self.colors['primary_dark'], activeforeground=self.colors['text'],
            relief=tk.FLAT, cursor="hand2", command=self.login, height=2
        )
        self.login_button.pack(pady=(16, 12), padx=30, fill=tk.X)

        # Links row
        links_frame = tk.Frame(card, bg=self.colors['surface'])
        links_frame.pack(pady=(0, 6))
        tk.Label(links_frame, text="No account?", font=("Arial", 9), bg=self.colors['surface'], fg=self.colors['text_secondary']).pack(side=tk.LEFT, padx=(0, 6))
        register_link = tk.Label(links_frame, text="Create one", font=("Arial", 9, "underline"), bg=self.colors['surface'], fg=self.colors['primary'], cursor="hand2")
        register_link.pack(side=tk.LEFT)
        register_link.bind("<Button-1>", lambda e: self.open_register())

        # Advanced: API key fallback (hidden by default)
        self.apikey_toggle = tk.Label(card, text="Use an API key instead", font=("Arial", 9, "underline"), bg=self.colors['surface'], fg=self.colors['text_secondary'], cursor="hand2")
        self.apikey_toggle.pack(pady=(4, 18))
        self.apikey_toggle.bind("<Button-1>", lambda e: self.toggle_apikey())

        self.apikey_frame = tk.Frame(card, bg=self.colors['surface'])
        # built lazily / packed on toggle
        self.create_input_field(self.apikey_frame, "API Key", "api_key", show="*", on_enter=lambda e: self.login_with_api_key())
        apikey_btn = tk.Button(
            self.apikey_frame, text="Continue with API key", font=("Arial", 10, "bold"),
            bg=self.colors['card'], fg=self.colors['text'],
            activebackground=self.colors['border'], activeforeground=self.colors['text'],
            relief=tk.FLAT, cursor="hand2", command=self.login_with_api_key, height=1
        )
        apikey_btn.pack(pady=(6, 4), padx=30, fill=tk.X)
        getkey_link = tk.Label(self.apikey_frame, text="Get your API key", font=("Arial", 9, "underline"), bg=self.colors['surface'], fg=self.colors['primary'], cursor="hand2")
        getkey_link.pack(pady=(0, 20))
        getkey_link.bind("<Button-1>", lambda e: self.open_api_key_page())

        # Footer
        tk.Label(self.root, text="https://myracingdata.com", font=("Arial", 8), bg=self.colors['bg'], fg=self.colors['text_secondary']).pack(side=tk.BOTTOM, pady=16)

    def toggle_apikey(self):
        """Show/hide the advanced API-key fallback."""
        if self.apikey_visible:
            self.apikey_frame.pack_forget()
            self.apikey_toggle.config(text="Use an API key instead")
        else:
            self.apikey_frame.pack(fill=tk.X)
            self.apikey_toggle.config(text="Hide API key option")
        self.apikey_visible = not self.apikey_visible

    def create_input_field(self, parent, placeholder, name, show=None, on_enter=None):
        """Create a labelled input field; bind Enter to on_enter if given."""
        frame = tk.Frame(parent, bg=self.colors['surface'])
        frame.pack(pady=8, padx=30, fill=tk.X)

        tk.Label(frame, text=placeholder, font=("Arial", 9), bg=self.colors['surface'], fg=self.colors['text_secondary'], anchor=tk.W).pack(fill=tk.X, pady=(0, 5))

        entry = tk.Entry(
            frame, font=("Arial", 11), bg=self.colors['card'], fg=self.colors['text'],
            insertbackground=self.colors['text'], relief=tk.FLAT, show=show
        )
        entry.pack(fill=tk.X, ipady=10)
        setattr(self, f"{name}_entry", entry)

        if on_enter is not None:
            entry.bind('<Return>', on_enter)

    def login(self):
        """Sign in with email + password, then obtain a long-lived API key."""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()

        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password")
            return

        self.login_button.config(state=tk.DISABLED, text="Signing in...")
        self.root.update()

        self.config.set('api_url', API_BASE)
        self.config.set('ws_url', WS_URL)

        try:
            resp = requests.post(
                f"{API_BASE}/auth/login",
                json={'email': email, 'password': password},
                timeout=10, verify=False
            )
            if resp.status_code != 200:
                try:
                    msg = resp.json().get('error', 'Invalid credentials')
                except Exception:
                    msg = 'Invalid credentials'
                messagebox.showerror("Login Failed", msg)
                return

            data = resp.json()
            access = data.get('access_token') or data.get('accessToken') or data.get('token')
            self.user_data = data.get('user', {}) or {}
            if not access:
                messagebox.showerror("Error", "Signed in, but no token was returned.")
                return

            headers = {'Authorization': f'Bearer {access}'}

            # Reuse the account's existing key if it has one…
            api_key = None
            try:
                me = requests.get(f"{API_BASE}/auth/me", headers=headers, timeout=10, verify=False)
                if me.status_code == 200:
                    api_key = me.json().get('api_key')
            except requests.exceptions.RequestException:
                pass

            # …otherwise mint one for this app.
            if not api_key:
                mk = requests.post(
                    f"{API_BASE}/api-keys", headers=headers,
                    json={'key_name': 'Telemetry App'}, timeout=10, verify=False
                )
                if mk.status_code in (200, 201):
                    api_key = mk.json().get('api_key')

            if not api_key:
                messagebox.showerror("Error", "Signed in, but couldn't set up the app key.\nTry the API key option below.")
                return

            self.config.set('api_key', api_key)
            self.config.set('user_email', email)
            if self.remember_var.get():
                self.save_auth_token(api_key, email)

            self.authenticated = True
            self.root.quit()
            self.root.destroy()

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Could not connect to MyRacingData:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}")
        finally:
            try:
                self.login_button.config(state=tk.NORMAL, text="Sign In")
            except Exception:
                pass

    def login_with_api_key(self):
        """Advanced: authenticate with an API key directly."""
        api_key = self.api_key_entry.get().strip()

        if not api_key:
            messagebox.showerror("Error", "Please enter your API key")
            return

        try:
            self.config.set('api_url', API_BASE)
            self.config.set('ws_url', WS_URL)

            response = requests.get(
                f"{API_BASE}/users/me",
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=10, verify=False
            )

            if response.status_code == 200:
                self.user_data = response.json()
                self.config.set('api_key', api_key)
                if self.remember_var.get():
                    self.save_auth_token(api_key, self.user_data.get('email', 'user'))
                self.authenticated = True
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
            with open(auth_file, 'w') as f:
                json.dump({'api_key': api_key, 'email': email, 'authenticated': True}, f)
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
                    self.config.set('api_url', API_BASE)
                    self.config.set('ws_url', WS_URL)

                    response = requests.get(
                        f"{API_BASE}/users/me",
                        headers={'Authorization': f'Bearer {api_key}'},
                        timeout=5, verify=False
                    )

                    if response.status_code == 200:
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
        webbrowser.open('https://myracingdata.com/auth/register')

    def open_api_key_page(self):
        """Open API key page"""
        import webbrowser
        webbrowser.open('https://myracingdata.com/profile?tab=api-keys')

    def run(self):
        """Run the login window"""
        if self.check_saved_auth():
            self.root.destroy()
            return True

        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        self.root.mainloop()
        return self.authenticated
