"""
Conversation Manager - PersonaPlex Integration
Manages the flow of speech-to-speech conversations

Supports multiple TTS backends:
- Piper TTS (local, free, fast)
- ElevenLabs (your cloned voice via API)
"""
import logging
import os
import queue
import threading
from typing import Optional, Callable, Dict, Any

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

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages speech-to-speech conversation flow
    PersonaPlex-inspired real-time interaction
    
    Supports two TTS backends:
    - 'piper': Local TTS using Piper (default, free)
    - 'elevenlabs': Cloud TTS using your ElevenLabs voice clone
    """
    
    def __init__(
        self,
        stt_model: str = "base.en",
        tts_voice: str = "en_US-amy-medium",
        tts_backend: str = None,  # 'piper' or 'elevenlabs' - auto-detects if None
        wake_word: str = "hey abby",
        vad_threshold: float = 0.5,
        sample_rate: int = 16000,
        wake_word_key: Optional[str] = None
    ):
        """
        Initialize conversation manager
        
        Args:
            stt_model: Whisper model size
            tts_voice: Piper voice model (used if tts_backend='piper')
            tts_backend: 'piper' for local TTS, 'elevenlabs' for cloud voice clone
                        If None, auto-detects based on ELEVENLABS_API_KEY
            wake_word: Wake word phrase
            vad_threshold: VAD detection threshold
            sample_rate: Audio sample rate
            wake_word_key: Porcupine access key
        """
        self.sample_rate = sample_rate
        self.is_listening = False
        self.audio_queue = queue.Queue()
        
        # Thread safety for wake word state
        self._state_lock = threading.Lock()
        self._wake_word_active = False
        
        # Auto-detect TTS backend
        if tts_backend is None:
            if os.getenv("ELEVENLABS_API_KEY") and os.getenv("ELEVENLABS_VOICE_ID"):
                tts_backend = "elevenlabs"
                logger.info("Auto-detected ElevenLabs configuration - using voice clone")
            else:
                tts_backend = "piper"
                logger.info("Using Piper TTS (local)")
        
        self.tts_backend = tts_backend
        
        # Initialize STT (speech-to-text) - always use local Whisper
        self.stt = STTEngine(model_size=stt_model)
        
        # Initialize TTS (text-to-speech) - based on backend choice
        if tts_backend == "elevenlabs":
            from .elevenlabs_tts import ElevenLabsTTS
            self.tts = ElevenLabsTTS(sample_rate=sample_rate)
            logger.info("Using ElevenLabs TTS with your voice clone")
        else:
            self.tts = TTSEngine(voice=tts_voice, sample_rate=sample_rate)
            logger.info(f"Using Piper TTS with voice: {tts_voice}")
        
        # Initialize VAD and wake word (always local)
        self.vad = VADDetector(threshold=vad_threshold, sample_rate=sample_rate)
        self.wake_word_detector = WakeWordDetector(
            wake_word=wake_word,
            access_key=wake_word_key
        )
        
        # Task executor callback
        self.task_executor: Optional[Callable[[str], str]] = None
        
        logger.info(f"Conversation manager initialized (TTS: {tts_backend})")
    
    def initialize(self):
        """Initialize all speech components"""
        logger.info("Initializing speech components...")
        
        try:
            self.stt.initialize()
            self.tts.initialize()
            self.vad.initialize()
            self.wake_word_detector.initialize()
            
            logger.info("All speech components initialized")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize speech components: {e}")
            return False
    
    def set_task_executor(self, executor: Callable[[str], str]):
        """
        Set the task executor callback
        
        Args:
            executor: Function that takes text input and returns text output
        """
        self.task_executor = executor
    
    def start_listening(self):
        """Start listening for audio input"""
        if not self.stt.is_initialized():
            logger.error("STT not initialized")
            return False
        
        self.is_listening = True
        
        # Start audio input thread
        threading.Thread(
            target=self._audio_input_thread,
            daemon=True
        ).start()
        
        # Start processing thread
        threading.Thread(
            target=self._processing_thread,
            daemon=True
        ).start()
        
        logger.info("Started listening for audio input")
        return True
    
    def stop_listening(self):
        """Stop listening for audio input"""
        self.is_listening = False
        logger.info("Stopped listening")
    
    def _audio_input_thread(self):
        """Thread for capturing audio input"""
        if not SOUNDDEVICE_AVAILABLE:
            logger.error("sounddevice not available. Cannot capture audio.")
            self.is_listening = False
            return
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                callback=self._audio_callback
            ):
                while self.is_listening:
                    sd.sleep(100)
        
        except Exception as e:
            logger.error(f"Audio input error: {e}")
            self.is_listening = False
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio input stream"""
        if status:
            logger.warning(f"Audio status: {status}")
        
        # Make a copy to ensure data integrity (flatten returns a view)
        audio_data = indata.flatten().copy()
        self.audio_queue.put(audio_data)
    
    def _processing_thread(self):
        """Thread for processing audio and handling conversation"""
        # Pre-allocate buffer with reasonable max size (10 seconds)
        max_buffer_size = self.sample_rate * 10
        audio_buffer = []
        
        while self.is_listening:
            try:
                # Get audio chunk from queue
                audio_chunk = self.audio_queue.get(timeout=1)
                
                # Check for wake word if not already active
                with self._state_lock:
                    is_active = self._wake_word_active
                
                if not is_active:
                    if self.wake_word_detector.detect(audio_chunk):
                        logger.info("Wake word detected!")
                        with self._state_lock:
                            self._wake_word_active = True
                        self._speak("Yes, how can I help you?")
                        audio_buffer.clear()
                    continue
                
                # Detect voice activity
                if self.vad.detect(audio_chunk):
                    audio_buffer.append(audio_chunk)
                    # Prevent unbounded growth
                    if sum(len(chunk) for chunk in audio_buffer) > max_buffer_size:
                        logger.warning("Audio buffer overflow, truncating")
                        audio_buffer = audio_buffer[-5:]  # Keep last 5 chunks
                
                else:
                    # Silence detected - process accumulated audio
                    if len(audio_buffer) > 0:
                        # Concatenate once
                        full_audio = np.concatenate(audio_buffer)
                        
                        # Transcribe
                        text = self.stt.transcribe(full_audio)
                        
                        if text:
                            logger.info(f"User said: {text}")
                            
                            # Execute task
                            response = self._execute_task(text)
                            
                            # Speak response
                            if response:
                                logger.info(f"Response: {response}")
                                self._speak(response)
                        
                        # Reset buffer and wake word state
                        audio_buffer.clear()
                        with self._state_lock:
                            self._wake_word_active = False
            
            except queue.Empty:
                continue
            
            except Exception as e:
                logger.error(f"Processing error: {e}")
    
    def _execute_task(self, text: str) -> str:
        """
        Execute task using the task executor
        
        Args:
            text: User input text
            
        Returns:
            Response text from executor, error message if execution fails,
            or "No task executor configured." if no executor is set
        """
        if self.task_executor:
            try:
                return self.task_executor(text)
            except Exception as e:
                logger.error(f"Task execution error: {e}")
                return "I'm sorry, I encountered an error processing your request."
        else:
            return "No task executor configured."
    
    def _speak(self, text: str):
        """
        Speak text using TTS
        
        Args:
            text: Text to speak
        """
        if not SOUNDDEVICE_AVAILABLE:
            # Fallback: print text
            print(f"Abby: {text}")
            return
        
        try:
            audio = self.tts.synthesize(text)
            
            if audio is not None:
                # Play audio
                sd.play(audio, self.sample_rate)
                sd.wait()
            else:
                # Fallback: print text
                print(f"Abby: {text}")
        
        except Exception as e:
            logger.error(f"Speech synthesis error: {e}")
            print(f"Abby: {text}")
    
    def process_text(self, text: str) -> str:
        """
        Process text input (bypass speech recognition)
        
        Args:
            text: Input text
            
        Returns:
            Response text
        """
        response = self._execute_task(text)
        return response
    
    def speak(self, text: str):
        """
        Speak text (public method)
        
        Args:
            text: Text to speak
        """
        self._speak(text)
    
    def cleanup(self):
        """Cleanup all resources"""
        self.stop_listening()
        
        self.stt.cleanup()
        self.tts.cleanup()
        self.vad.cleanup()
        self.wake_word_detector.cleanup()
        
        logger.info("Conversation manager cleaned up")
