import logging
import os
import queue
import threading
from typing import Optional, Callable

# Existing imports
try:
    import numpy as np
except ImportError:
    np = None

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    sd = None

from .stt_engine import STTEngine
from .tts_engine import TTSEngine
from .vad_detector import VADDetector
from .wake_word import WakeWordDetector
from .interrupt_logic import VoiceInterruption # <-- IMPORT THE NEW GIFT

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(
        self,
        stt_model: str = "base.en",
        tts_voice: str = "en_US-amy-medium",
        tts_backend: str = None,
        wake_word: str = "hey abby",
        vad_threshold: float = 0.5,
        sample_rate: int = 16000,
        wake_word_key: Optional[str] = None
    ):
        self.sample_rate = sample_rate
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self._state_lock = threading.Lock()
        self._wake_word_active = False

        # --- 1. INITIALIZE THE BARGE-IN LOGIC ---
        self.interrupter = VoiceInterruption()
        
        # Auto-detect TTS
        if tts_backend is None:
            if os.getenv("ELEVENLABS_API_KEY") and os.getenv("ELEVENLABS_VOICE_ID"):
                tts_backend = "elevenlabs"
            else:
                tts_backend = "piper"
        self.tts_backend = tts_backend

        self.stt = STTEngine(model_size=stt_model)
        
        # Initialize TTS Engine
        if tts_backend == "elevenlabs":
            from .elevenlabs_tts import ElevenLabsTTS
            self.tts = ElevenLabsTTS(sample_rate=sample_rate)
        else:
            self.tts = TTSEngine(voice=tts_voice, sample_rate=sample_rate)
        
        self.vad = VADDetector(threshold=vad_threshold, sample_rate=sample_rate)
        self.wake_word_detector = WakeWordDetector(wake_word=wake_word, access_key=wake_word_key)
        self.task_executor: Optional[Callable[[str], str]] = None

    def _speak(self, text: str):
        """
        Unified Speech Logic: Handles interruptible playback.
        """
        if not SOUNDDEVICE_AVAILABLE:
            print(f"Abby: {text}")
            return

        try:
            # 1. Synthesize Audio
            # (Ensure your tts_engine returns a file path for ElevenLabs)
            audio_path = self.tts.synthesize_to_file(text) 
            
            if audio_path and os.path.exists(audio_path):
                # 2. Start playback via the new interrupt logic
                self.interrupter.start_speech(audio_path)
                
                # 3. Monitor for interruption via VAD on the 7950X
                while self.interrupter.active_playback_process.poll() is None:
                    # Check for live speech in the incoming audio queue
                    if not self.audio_queue.empty():
                        latest_chunk = self.audio_queue.get_nowait()
                        if self.vad.detect(latest_chunk):
                            if self.interrupter.trigger_barge_in():
                                logger.info("📢 INTERRUPTED: Abby is pausing to listen.")
                                return "INTERRUPTED"
                return "FINISHED"
            else:
                print(f"Abby: {text}")

        except Exception as e:
            logger.error(f"Speech synthesis error: {e}")
            print(f"Abby: {text}")

    # ... (Rest of your existing methods: initialize, start_listening, etc.) ...