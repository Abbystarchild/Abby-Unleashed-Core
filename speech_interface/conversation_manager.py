"""
Conversation Manager - PersonaPlex Integration
Manages the flow of speech-to-speech conversations
"""
import logging
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
    """
    
    def __init__(
        self,
        stt_model: str = "base.en",
        tts_voice: str = "en_US-amy-medium",
        wake_word: str = "hey abby",
        vad_threshold: float = 0.5,
        sample_rate: int = 16000,
        wake_word_key: Optional[str] = None
    ):
        """
        Initialize conversation manager
        
        Args:
            stt_model: Whisper model size
            tts_voice: Piper voice model
            wake_word: Wake word phrase
            vad_threshold: VAD detection threshold
            sample_rate: Audio sample rate
            wake_word_key: Porcupine access key
        """
        self.sample_rate = sample_rate
        self.is_listening = False
        self.audio_queue = queue.Queue()
        
        # Initialize components
        self.stt = STTEngine(model_size=stt_model)
        self.tts = TTSEngine(voice=tts_voice, sample_rate=sample_rate)
        self.vad = VADDetector(threshold=vad_threshold, sample_rate=sample_rate)
        self.wake_word_detector = WakeWordDetector(
            wake_word=wake_word,
            access_key=wake_word_key
        )
        
        # Task executor callback
        self.task_executor: Optional[Callable[[str], str]] = None
        
        logger.info("Conversation manager initialized")
    
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
        
        # Add audio to queue
        self.audio_queue.put(indata.copy().flatten())
    
    def _processing_thread(self):
        """Thread for processing audio and handling conversation"""
        audio_buffer = np.array([], dtype=np.float32)
        wake_word_active = False
        
        while self.is_listening:
            try:
                # Get audio chunk from queue
                audio_chunk = self.audio_queue.get(timeout=1)
                
                # Check for wake word if not already active
                if not wake_word_active:
                    if self.wake_word_detector.detect(audio_chunk):
                        logger.info("Wake word detected!")
                        wake_word_active = True
                        self._speak("Yes, how can I help you?")
                        audio_buffer = np.array([], dtype=np.float32)
                    continue
                
                # Detect voice activity
                if self.vad.detect(audio_chunk):
                    audio_buffer = np.concatenate([audio_buffer, audio_chunk])
                
                else:
                    # Silence detected - process accumulated audio
                    if len(audio_buffer) > 0:
                        # Transcribe
                        text = self.stt.transcribe(audio_buffer)
                        
                        if text:
                            logger.info(f"User said: {text}")
                            
                            # Execute task
                            response = self._execute_task(text)
                            
                            # Speak response
                            if response:
                                logger.info(f"Response: {response}")
                                self._speak(response)
                        
                        # Reset buffer and wake word state
                        audio_buffer = np.array([], dtype=np.float32)
                        wake_word_active = False
            
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
            Response text
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
