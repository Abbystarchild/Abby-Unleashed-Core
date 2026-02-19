from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, Log
from textual.containers import Container, Horizontal, Vertical
import torch_directml
import pygame
import os

class OverwatchDashboard(App):
    CSS = """
    Screen { background: #0a0a0a; color: #00ff41; }
    #vram-panel { border: solid #00ff41; height: 15%; margin: 1; }
    #agent-log { border: double #00ffff; height: 40%; margin: 1; }
    #system-controls { border: heavy #ff00ff; height: 30%; }
    .neon-label { color: #ff00ff; text-style: bold; }
    """

    def on_mount(self):
        # Initializing the Soundtrack
        pygame.mixer.init()
        if os.path.exists("media/cyberpunk_ambient.mp3"):
            pygame.mixer.music.load("media/cyberpunk_ambient.mp3")
            pygame.mixer.music.play(-1) # Loop forever

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            # 1. HARDWARE TELEMETRY
            yield Static("⚡ [neon-label]SYSTEM VITAL SIGNS[/]", id="vram-panel")
            
            with Horizontal():
                # 2. AGENT CONTROL & LOGS
                with Vertical():
                    yield Log(id="agent-log", highlight=True)
                    yield DataTable(id="prompt-library")
                
                # 3. TOGGLES & SWITCHES
                with Vertical(id="system-controls"):
                    yield Static("🔘 [neon-label]UNSHACKLED MODE: ON[/]")
                    yield Static("🔘 [neon-label]BARGE-IN VOICE: ACTIVE[/]")
                    yield Static("🔘 [neon-label]SHADOW AUDIT: RUNNING[/]")
                    
        yield Footer()

    def update_telemetry(self):
        # DirectML Hardware Monitor logic here
        pass

if __name__ == "__main__":
    app = OverwatchDashboard()
    app.run()