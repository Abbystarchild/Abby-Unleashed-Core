import os
import signal
import subprocess

class VoiceInterruption:
    def __init__(self):
        self.active_playback_process = None

    def start_speech(self, audio_path):
        """Starts ElevenLabs playback as a subprocess."""
        # Using a simple CLI player like 'ffplay' or your existing 'mp3_player.exe'
        self.active_playback_process = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", audio_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def trigger_barge_in(self):
        """Called by the Vosk VAD thread when user speech is detected."""
        if self.active_playback_process and self.active_playback_process.poll() is None:
            print("🚀 INTERRUPT: User is speaking. Killing audio stream...")
            self.active_playback_process.terminate() # Graceful kill
            # Send a signal to the 32B Model to stop generating/revise
            return True
        return False