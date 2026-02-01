"""
Abby Unleashed Launcher
=======================
A simple GUI launcher for the Abby Unleashed server.
Can be compiled to .exe with: pyinstaller --onefile --windowed --icon=abby.ico launcher.py
"""

import os
import sys
import subprocess
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
import socket
import time

# Get the directory where this script/exe is located
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuration
DEFAULT_PORT = 8080
SERVER_SCRIPT = os.path.join(BASE_DIR, "api_server.py")
VENV_PYTHON = os.path.join(BASE_DIR, "venv", "Scripts", "python.exe")


def get_local_ip():
    """Get the local IP address for network access."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"


def is_port_in_use(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


class AbbyLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Abby Unleashed")
        self.root.geometry("400x350")
        self.root.resizable(False, False)
        
        # Try to set icon if available
        icon_path = os.path.join(BASE_DIR, "abby.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        
        self.server_process = None
        self.port = DEFAULT_PORT
        self.local_ip = get_local_ip()
        
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#6366f1", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(
            header, 
            text="✨ Abby Unleashed", 
            font=("Segoe UI", 18, "bold"),
            fg="white",
            bg="#6366f1"
        )
        title.pack(pady=15)
        
        # Main content
        content = tk.Frame(self.root, padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Status
        self.status_label = tk.Label(
            content,
            text="● Server Stopped",
            font=("Segoe UI", 12),
            fg="#ef4444"
        )
        self.status_label.pack(pady=(0, 15))
        
        # Port setting
        port_frame = tk.Frame(content)
        port_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(port_frame, text="Port:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value=str(DEFAULT_PORT))
        self.port_entry = tk.Entry(port_frame, textvariable=self.port_var, width=8, font=("Segoe UI", 10))
        self.port_entry.pack(side=tk.LEFT, padx=10)
        
        # URLs (hidden initially)
        self.url_frame = tk.Frame(content)
        
        self.local_url = tk.Label(
            self.url_frame,
            text="",
            font=("Segoe UI", 9),
            fg="#6366f1",
            cursor="hand2"
        )
        self.local_url.pack(pady=2)
        self.local_url.bind("<Button-1>", lambda e: self.open_browser("local"))
        
        self.network_url = tk.Label(
            self.url_frame,
            text="",
            font=("Segoe UI", 9),
            fg="#6366f1",
            cursor="hand2"
        )
        self.network_url.pack(pady=2)
        self.network_url.bind("<Button-1>", lambda e: self.open_browser("network"))
        
        # Buttons
        btn_frame = tk.Frame(content)
        btn_frame.pack(pady=20)
        
        self.start_btn = tk.Button(
            btn_frame,
            text="▶ Start Server",
            font=("Segoe UI", 11, "bold"),
            bg="#10b981",
            fg="white",
            width=14,
            height=2,
            command=self.start_server,
            relief=tk.FLAT
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(
            btn_frame,
            text="■ Stop Server",
            font=("Segoe UI", 11, "bold"),
            bg="#ef4444",
            fg="white",
            width=14,
            height=2,
            command=self.stop_server,
            state=tk.DISABLED,
            relief=tk.FLAT
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Open browser button
        self.browser_btn = tk.Button(
            content,
            text="🌐 Open in Browser",
            font=("Segoe UI", 10),
            command=lambda: self.open_browser("local"),
            state=tk.DISABLED
        )
        self.browser_btn.pack(pady=10)
        
        # Log area
        log_label = tk.Label(content, text="Server Log:", font=("Segoe UI", 9), anchor="w")
        log_label.pack(fill=tk.X)
        
        self.log_text = tk.Text(content, height=4, font=("Consolas", 8), state=tk.DISABLED)
        self.log_text.pack(fill=tk.X, pady=5)
        
    def log(self, message):
        """Add message to log area."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def start_server(self):
        """Start the Abby server."""
        try:
            self.port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            return
            
        if is_port_in_use(self.port):
            messagebox.showerror("Error", f"Port {self.port} is already in use")
            return
            
        if not os.path.exists(VENV_PYTHON):
            messagebox.showerror("Error", f"Python venv not found at:\n{VENV_PYTHON}")
            return
            
        if not os.path.exists(SERVER_SCRIPT):
            messagebox.showerror("Error", f"Server script not found at:\n{SERVER_SCRIPT}")
            return
        
        self.log(f"Starting server on port {self.port}...")
        
        # Start server in background
        try:
            self.server_process = subprocess.Popen(
                [VENV_PYTHON, SERVER_SCRIPT, "--port", str(self.port)],
                cwd=BASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            # Start thread to read output
            threading.Thread(target=self.read_output, daemon=True).start()
            
            # Update UI
            self.status_label.config(text="● Server Running", fg="#10b981")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.port_entry.config(state=tk.DISABLED)
            self.browser_btn.config(state=tk.NORMAL)
            
            # Show URLs
            self.local_url.config(text=f"📍 Local: http://localhost:{self.port}")
            self.network_url.config(text=f"📱 Network: http://{self.local_ip}:{self.port}")
            self.url_frame.pack(pady=10)
            
            self.log(f"Server started! Access at http://localhost:{self.port}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server:\n{e}")
            self.log(f"Error: {e}")
            
    def stop_server(self):
        """Stop the Abby server."""
        if self.server_process:
            self.log("Stopping server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
            
        # Update UI
        self.status_label.config(text="● Server Stopped", fg="#ef4444")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.NORMAL)
        self.browser_btn.config(state=tk.DISABLED)
        self.url_frame.pack_forget()
        
        self.log("Server stopped")
        
    def read_output(self):
        """Read server output in background thread."""
        if self.server_process:
            for line in iter(self.server_process.stdout.readline, b''):
                if line:
                    text = line.decode('utf-8', errors='replace').strip()
                    # Only log important lines
                    if any(x in text.lower() for x in ['error', 'warning', 'running', 'started', 'loaded']):
                        self.root.after(0, lambda t=text: self.log(t[:80]))
                        
    def open_browser(self, which="local"):
        """Open the web interface in browser."""
        if which == "local":
            url = f"http://localhost:{self.port}"
        else:
            url = f"http://{self.local_ip}:{self.port}"
        webbrowser.open(url)
        
    def on_close(self):
        """Handle window close."""
        if self.server_process:
            if messagebox.askyesno("Confirm", "Server is running. Stop and exit?"):
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()
            
    def run(self):
        """Start the launcher."""
        self.root.mainloop()


if __name__ == "__main__":
    app = AbbyLauncher()
    app.run()
