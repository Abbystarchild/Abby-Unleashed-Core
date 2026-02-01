#!/usr/bin/env python3
"""
Abby Browser - Custom browser for Abby Unleashed

A lightweight browser specifically designed for Abby that:
- Auto-grants microphone permissions (no prompts!)
- Allows audio autoplay without restrictions
- Handles all media permissions automatically
- Provides a clean, focused interface
- Runs on localhost with full capabilities

No more browser permission headaches!
"""

import sys
import os

# Check for PyQt6 first, fall back to PyQt5
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
        QWidget, QPushButton, QLineEdit, QLabel, QStatusBar,
        QToolBar, QSizePolicy, QMessageBox
    )
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import (
        QWebEnginePage, QWebEngineProfile, QWebEngineSettings,
        QWebEnginePermission
    )
    from PyQt6.QtCore import QUrl, Qt, QSize, pyqtSignal, QTimer
    from PyQt6.QtGui import QIcon, QAction, QFont, QPalette, QColor
    PYQT_VERSION = 6
    print("Using PyQt6")
except ImportError:
    try:
        from PyQt5.QtWidgets import (
            QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
            QWidget, QPushButton, QLineEdit, QLabel, QStatusBar,
            QToolBar, QSizePolicy, QMessageBox
        )
        from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
        from PyQt5.QtCore import QUrl, Qt, QSize, pyqtSignal, QTimer
        from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
        PYQT_VERSION = 5
        print("Using PyQt5")
    except ImportError:
        print("=" * 60)
        print("ERROR: PyQt6 or PyQt5 with WebEngine is required!")
        print("=" * 60)
        print("\nInstall with:")
        print("  pip install PyQt6 PyQt6-WebEngine")
        print("\nOr:")
        print("  pip install PyQt5 PyQtWebEngine")
        print("=" * 60)
        sys.exit(1)


class AbbyWebPage(QWebEnginePage):
    """
    Custom web page that auto-grants all permissions Abby needs.
    No more clicking "Allow" on microphone prompts!
    """
    
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self._setup_permission_handling()
    
    def _setup_permission_handling(self):
        """Set up automatic permission granting"""
        if PYQT_VERSION == 6:
            # PyQt6 uses featurePermissionRequested (same as Qt5 actually)
            try:
                self.featurePermissionRequested.connect(self._handle_feature_permission)
                print("Connected to featurePermissionRequested")
            except Exception as e:
                print(f"Warning: Could not connect permission handler: {e}")
        else:
            # PyQt5 uses featurePermissionRequested
            self.featurePermissionRequested.connect(self._handle_feature_permission)
    
    def _handle_feature_permission(self, origin, feature):
        """Handle permission requests - auto-grant everything Abby needs"""
        if PYQT_VERSION == 6:
            feature_names = {
                QWebEnginePage.Feature.MediaAudioCapture: "Microphone",
                QWebEnginePage.Feature.MediaVideoCapture: "Camera",
                QWebEnginePage.Feature.MediaAudioVideoCapture: "Camera+Mic",
                QWebEnginePage.Feature.Notifications: "Notifications",
                QWebEnginePage.Feature.Geolocation: "Location",
                QWebEnginePage.Feature.DesktopVideoCapture: "Screen Capture",
                QWebEnginePage.Feature.DesktopAudioVideoCapture: "Screen+Audio",
            }
            granted = QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
        else:
            feature_names = {
                QWebEnginePage.MediaAudioCapture: "Microphone",
                QWebEnginePage.MediaVideoCapture: "Camera",
                QWebEnginePage.MediaAudioVideoCapture: "Camera+Mic",
                QWebEnginePage.Notifications: "Notifications",
                QWebEnginePage.Geolocation: "Location",
            }
            granted = QWebEnginePage.PermissionGrantedByUser
        
        feature_name = feature_names.get(feature, f"Unknown({feature})")
        print(f"🔓 Auto-granting permission: {feature_name} for {origin.toString()}")
        
        # Grant the permission
        self.setFeaturePermission(origin, feature, granted)
    
    def javaScriptConsoleMessage(self, level, message, line, source):
        """Forward JavaScript console messages to Python console"""
        if PYQT_VERSION == 6:
            # PyQt6 uses enum
            level_val = level.value if hasattr(level, 'value') else int(level)
        else:
            level_val = level
        
        levels = {0: "DEBUG", 1: "INFO", 2: "WARN", 3: "ERROR"}
        level_name = levels.get(level_val, "LOG")
        # Only show warnings and errors to reduce noise
        if level_val >= 2:
            print(f"[JS {level_name}] {message} ({source}:{line})")


class AbbyBrowser(QMainWindow):
    """
    The main Abby Browser window - a purpose-built browser for Abby.
    """
    
    def __init__(self, url="http://localhost:8080"):
        super().__init__()
        self.default_url = url
        self._setup_window()
        self._setup_profile()
        self._setup_browser()
        self._setup_toolbar()
        self._setup_statusbar()
        self._apply_dark_theme()
        
        # Navigate to Abby
        self.navigate_to(self.default_url)
    
    def _setup_window(self):
        """Configure the main window"""
        self.setWindowTitle("🤖 Abby Browser")
        self.setMinimumSize(1200, 800)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 1400) // 2
        y = (screen.height() - 900) // 2
        self.setGeometry(x, y, 1400, 900)
    
    def _setup_profile(self):
        """Configure browser profile with permissive settings"""
        self.profile = QWebEngineProfile.defaultProfile()
        
        # Set a custom user agent
        self.profile.setHttpUserAgent(
            "AbbyBrowser/1.0 (Abby Unleashed; Desktop Client) "
            "AppleWebKit/537.36 Chrome/120.0.0.0"
        )
        
        # Configure settings
        settings = self.profile.settings()
        
        if PYQT_VERSION == 6:
            # PyQt6 settings
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)  # Allow autoplay!
            settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
        else:
            # PyQt5 settings
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
            settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)  # Allow autoplay!
            settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
            settings.setAttribute(QWebEngineSettings.ScreenCaptureEnabled, True)
    
    def _setup_browser(self):
        """Set up the web browser view"""
        # Create the browser widget
        self.browser = QWebEngineView()
        
        # Create our custom page with auto-permissions
        self.page = AbbyWebPage(self.profile, self.browser)
        self.browser.setPage(self.page)
        
        # Connect signals
        self.browser.loadStarted.connect(self._on_load_started)
        self.browser.loadProgress.connect(self._on_load_progress)
        self.browser.loadFinished.connect(self._on_load_finished)
        self.browser.titleChanged.connect(self._on_title_changed)
        
        # Set as central widget
        self.setCentralWidget(self.browser)
    
    def _setup_toolbar(self):
        """Create a minimal toolbar"""
        toolbar = QToolBar("Navigation")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Style the toolbar
        toolbar.setStyleSheet("""
            QToolBar {
                background: #1e1e2e;
                border: none;
                padding: 5px;
                spacing: 5px;
            }
            QToolButton {
                background: #313244;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                color: #cdd6f4;
                font-size: 14px;
            }
            QToolButton:hover {
                background: #45475a;
            }
            QToolButton:pressed {
                background: #585b70;
            }
        """)
        
        # Back button
        if PYQT_VERSION == 6:
            back_action = QAction("◀ Back", self)
            back_action.triggered.connect(self.browser.back)
            toolbar.addAction(back_action)
            
            # Forward button
            forward_action = QAction("Forward ▶", self)
            forward_action.triggered.connect(self.browser.forward)
            toolbar.addAction(forward_action)
            
            # Reload button
            reload_action = QAction("🔄 Reload", self)
            reload_action.triggered.connect(self.browser.reload)
            toolbar.addAction(reload_action)
            
            # Home button
            home_action = QAction("🏠 Abby", self)
            home_action.triggered.connect(lambda: self.navigate_to(self.default_url))
            toolbar.addAction(home_action)
        else:
            # PyQt5 uses the same pattern
            back_btn = QPushButton("◀ Back")
            back_btn.clicked.connect(self.browser.back)
            toolbar.addWidget(back_btn)
            
            forward_btn = QPushButton("Forward ▶")
            forward_btn.clicked.connect(self.browser.forward)
            toolbar.addWidget(forward_btn)
            
            reload_btn = QPushButton("🔄 Reload")
            reload_btn.clicked.connect(self.browser.reload)
            toolbar.addWidget(reload_btn)
            
            home_btn = QPushButton("🏠 Abby")
            home_btn.clicked.connect(lambda: self.navigate_to(self.default_url))
            toolbar.addWidget(home_btn)
        
        # Add spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding if PYQT_VERSION == 6 else QSizePolicy.Expanding, 
                            QSizePolicy.Policy.Preferred if PYQT_VERSION == 6 else QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL...")
        self.url_bar.setStyleSheet("""
            QLineEdit {
                background: #313244;
                border: 2px solid #45475a;
                border-radius: 8px;
                padding: 8px 12px;
                color: #cdd6f4;
                font-size: 13px;
                min-width: 400px;
            }
            QLineEdit:focus {
                border-color: #89b4fa;
            }
        """)
        self.url_bar.returnPressed.connect(self._navigate_from_urlbar)
        toolbar.addWidget(self.url_bar)
        
        # Add spacer
        spacer2 = QWidget()
        spacer2.setSizePolicy(QSizePolicy.Policy.Expanding if PYQT_VERSION == 6 else QSizePolicy.Expanding,
                             QSizePolicy.Policy.Preferred if PYQT_VERSION == 6 else QSizePolicy.Preferred)
        toolbar.addWidget(spacer2)
        
        # Fullscreen button
        if PYQT_VERSION == 6:
            fullscreen_action = QAction("⛶ Fullscreen", self)
            fullscreen_action.triggered.connect(self._toggle_fullscreen)
            toolbar.addAction(fullscreen_action)
            
            # Dev tools button
            devtools_action = QAction("🔧 DevTools", self)
            devtools_action.triggered.connect(self._open_devtools)
            toolbar.addAction(devtools_action)
        else:
            fullscreen_btn = QPushButton("⛶ Fullscreen")
            fullscreen_btn.clicked.connect(self._toggle_fullscreen)
            toolbar.addWidget(fullscreen_btn)
            
            devtools_btn = QPushButton("🔧 DevTools")
            devtools_btn.clicked.connect(self._open_devtools)
            toolbar.addWidget(devtools_btn)
    
    def _setup_statusbar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Permission indicator
        self.perm_label = QLabel("🔓 All permissions granted")
        self.perm_label.setStyleSheet("color: #a6e3a1; padding: 0 10px;")
        self.status_bar.addPermanentWidget(self.perm_label)
        
        # Connection indicator
        self.conn_label = QLabel("⚡ Ready")
        self.conn_label.setStyleSheet("color: #89b4fa; padding: 0 10px;")
        self.status_bar.addPermanentWidget(self.conn_label)
        
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background: #1e1e2e;
                color: #cdd6f4;
                border-top: 1px solid #313244;
            }
        """)
    
    def _apply_dark_theme(self):
        """Apply dark theme to the window"""
        self.setStyleSheet("""
            QMainWindow {
                background: #1e1e2e;
            }
        """)
    
    def navigate_to(self, url):
        """Navigate to a URL"""
        if not url.startswith(('http://', 'https://', 'file://')):
            url = 'http://' + url
        self.browser.setUrl(QUrl(url))
        self.url_bar.setText(url)
    
    def _navigate_from_urlbar(self):
        """Navigate to URL entered in URL bar"""
        url = self.url_bar.text().strip()
        if url:
            self.navigate_to(url)
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def _open_devtools(self):
        """Open developer tools (if available)"""
        # Note: DevTools require a separate window in QtWebEngine
        QMessageBox.information(
            self, 
            "Developer Tools",
            "Press F12 in Chrome/Edge to debug the page,\n"
            "or check the Python console for JS errors.\n\n"
            "To enable full DevTools, run:\n"
            "set QTWEBENGINE_REMOTE_DEBUGGING=9222"
        )
    
    def _on_load_started(self):
        """Called when page starts loading"""
        self.conn_label.setText("⏳ Loading...")
        self.conn_label.setStyleSheet("color: #f9e2af; padding: 0 10px;")
    
    def _on_load_progress(self, progress):
        """Called during page load"""
        self.conn_label.setText(f"⏳ Loading {progress}%...")
    
    def _on_load_finished(self, success):
        """Called when page finishes loading"""
        if success:
            self.conn_label.setText("⚡ Connected")
            self.conn_label.setStyleSheet("color: #a6e3a1; padding: 0 10px;")
            self.status_bar.showMessage("Page loaded successfully", 3000)
            
            # Inject helper script to enable extra features
            self._inject_helper_script()
        else:
            self.conn_label.setText("❌ Error")
            self.conn_label.setStyleSheet("color: #f38ba8; padding: 0 10px;")
            self.status_bar.showMessage("Failed to load page", 5000)
    
    def _on_title_changed(self, title):
        """Update window title when page title changes"""
        if title:
            self.setWindowTitle(f"🤖 Abby Browser - {title}")
        else:
            self.setWindowTitle("🤖 Abby Browser")
        
        # Update URL bar
        self.url_bar.setText(self.browser.url().toString())
    
    def _inject_helper_script(self):
        """Inject JavaScript to enable additional features"""
        script = """
        (function() {
            // Mark that we're in Abby Browser
            window.ABBY_BROWSER = true;
            window.ABBY_BROWSER_VERSION = '1.0';
            
            // Auto-enable audio context if suspended
            if (window.AudioContext || window.webkitAudioContext) {
                const OriginalAudioContext = window.AudioContext || window.webkitAudioContext;
                const originalCreate = OriginalAudioContext.prototype.createGain;
                
                // Patch to auto-resume suspended contexts
                document.addEventListener('DOMContentLoaded', function() {
                    const contexts = [];
                    const OriginalContext = window.AudioContext || window.webkitAudioContext;
                    window.AudioContext = window.webkitAudioContext = function() {
                        const ctx = new OriginalContext();
                        contexts.push(ctx);
                        return ctx;
                    };
                });
            }
            
            // Override permission query to always return granted
            if (navigator.permissions && navigator.permissions.query) {
                const originalQuery = navigator.permissions.query.bind(navigator.permissions);
                navigator.permissions.query = function(desc) {
                    return originalQuery(desc).then(function(status) {
                        // Create a fake status that always says granted
                        return {
                            state: 'granted',
                            onchange: null,
                            addEventListener: function() {},
                            removeEventListener: function() {}
                        };
                    }).catch(function() {
                        return { state: 'granted' };
                    });
                };
            }
            
            console.log('🤖 Abby Browser helper script loaded');
        })();
        """
        self.page.runJavaScript(script)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.F11 if PYQT_VERSION == 6 else Qt.Key_F11:
            self._toggle_fullscreen()
        elif event.key() == (Qt.Key.Escape if PYQT_VERSION == 6 else Qt.Key_Escape):
            if self.isFullScreen():
                self.showNormal()
        elif event.key() == (Qt.Key.F5 if PYQT_VERSION == 6 else Qt.Key_F5):
            self.browser.reload()
        else:
            super().keyPressEvent(event)


def main():
    """Launch the Abby Browser"""
    print("=" * 60)
    print("🤖 Abby Browser - Custom browser for Abby Unleashed")
    print("=" * 60)
    print()
    print("Features:")
    print("  ✅ Auto-grants microphone permission")
    print("  ✅ Auto-grants camera permission")
    print("  ✅ Allows audio autoplay")
    print("  ✅ No permission prompts!")
    print("  ✅ Dark theme")
    print()
    print("Shortcuts:")
    print("  F5  - Reload")
    print("  F11 - Toggle fullscreen")
    print("  Esc - Exit fullscreen")
    print()
    
    # Parse command line args
    url = "http://localhost:8080"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    print(f"Connecting to: {url}")
    print("=" * 60)
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Abby Browser")
    app.setOrganizationName("Abby Unleashed")
    
    # Enable high DPI scaling
    if PYQT_VERSION == 6:
        pass  # Automatic in Qt6
    else:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create and show browser
    browser = AbbyBrowser(url)
    browser.show()
    
    # Run the application
    sys.exit(app.exec() if PYQT_VERSION == 6 else app.exec_())


if __name__ == "__main__":
    main()
