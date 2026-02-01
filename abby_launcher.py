#!/usr/bin/env python3
"""
Abby Unleashed Launcher
=======================
One-click launcher that starts:
1. The API server (api_server.py)
2. The Abby Browser (abby_browser.py)

This is the main entry point for running Abby Unleashed.
"""

import sys
import os
import subprocess
import time
import threading
import signal

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Track subprocesses for cleanup
server_process = None
browser_process = None


def find_python():
    """Find the Python executable to use"""
    # Try venv first
    venv_python = os.path.join(SCRIPT_DIR, 'venv', 'Scripts', 'python.exe')
    if os.path.exists(venv_python):
        return venv_python
    
    # Fall back to current Python
    return sys.executable


def find_pythonw():
    """Find pythonw for GUI apps (no console window)"""
    python = find_python()
    pythonw = python.replace('python.exe', 'pythonw.exe')
    if os.path.exists(pythonw):
        return pythonw
    return python


def start_server(port=8080):
    """Start the API server"""
    global server_process
    
    python = find_python()
    server_script = os.path.join(SCRIPT_DIR, 'api_server.py')
    
    if not os.path.exists(server_script):
        print(f"❌ Server script not found: {server_script}")
        return None
    
    print(f"🚀 Starting Abby server on port {port}...")
    
    # Start server with --no-browser since we'll launch it ourselves
    server_process = subprocess.Popen(
        [python, server_script, '--port', str(port), '--no-browser'],
        cwd=SCRIPT_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
    )
    
    return server_process


def start_browser(url="http://localhost:8080"):
    """Start the Abby Browser"""
    global browser_process
    
    pythonw = find_pythonw()
    browser_script = os.path.join(SCRIPT_DIR, 'abby_browser.py')
    
    if not os.path.exists(browser_script):
        print(f"❌ Browser script not found: {browser_script}")
        print("Opening in default browser instead...")
        import webbrowser
        webbrowser.open(url)
        return None
    
    print(f"🌐 Launching Abby Browser -> {url}")
    
    browser_process = subprocess.Popen(
        [pythonw, browser_script, url],
        cwd=SCRIPT_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    
    return browser_process


def wait_for_server(url, timeout=30):
    """Wait for server to be ready"""
    import urllib.request
    import urllib.error
    
    print("⏳ Waiting for server to start...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(f"{url}/api/health", timeout=2)
            print("✅ Server is ready!")
            return True
        except (urllib.error.URLError, ConnectionRefusedError, TimeoutError):
            time.sleep(0.5)
    
    print("⚠️ Server didn't respond in time, launching browser anyway...")
    return False


def cleanup(signum=None, frame=None):
    """Clean up subprocesses on exit"""
    global server_process, browser_process
    
    print("\n🛑 Shutting down Abby Unleashed...")
    
    if browser_process and browser_process.poll() is None:
        browser_process.terminate()
        print("  Browser closed")
    
    if server_process and server_process.poll() is None:
        server_process.terminate()
        print("  Server stopped")
    
    sys.exit(0)


def main():
    """Main launcher entry point"""
    print("=" * 60)
    print("🤖 Abby Unleashed Launcher")
    print("=" * 60)
    print()
    
    # Parse arguments
    port = 8080
    for i, arg in enumerate(sys.argv[1:]):
        if arg == '--port' and i + 2 < len(sys.argv):
            port = int(sys.argv[i + 2])
    
    url = f"http://localhost:{port}"
    
    # Set up cleanup handler
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    if os.name == 'nt':
        signal.signal(signal.SIGBREAK, cleanup)
    
    # Start the server
    server = start_server(port)
    if not server:
        print("❌ Failed to start server!")
        input("Press Enter to exit...")
        return 1
    
    # Wait for server to be ready
    wait_for_server(url, timeout=30)
    
    # Small extra delay for stability
    time.sleep(1)
    
    # Start the browser
    browser = start_browser(url)
    
    print()
    print("=" * 60)
    print("✨ Abby Unleashed is running!")
    print(f"   Server: {url}")
    print("   Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    # Wait for server to exit (or user interrupt)
    try:
        server.wait()
    except KeyboardInterrupt:
        cleanup()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
