"""
Text-to-Speech Engine using piper-tts
PersonaPlex-inspired natural voice synthesis
"""
import logging
import subprocess
import tempfile
import os
from typing import Optional, TYPE_CHECKING

try:
    import numpy as np
except ImportError:
    np = None

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Text-to-Speech engine using piper-tts
    Provides natural voice synthesis
    """
    
    def __init__(
        self,
        voice: str = "en_US-amy-medium",
        sample_rate: int = 22050
    ):
        """
        Initialize TTS engine
        
        Args:
            voice: Voice model to use
            sample_rate: Audio sample rate
        """
        self.voice = voice
        self.sample_rate = sample_rate
        self.initialized = False
        
        logger.info(f"Initializing TTS engine with voice: {voice}")
    
    def initialize(self):
        """Initialize the TTS engine"""
        try:
            # Check if piper is available
            result = subprocess.run(
                ["piper", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.initialized = True
                logger.info("TTS engine initialized successfully")
            else:
                logger.warning("Piper not found, using fallback TTS")
                self.initialized = False
        
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Piper not available: {e}")
            self.initialized = False
    
    def synthesize(self, text: str) -> Optional["np.ndarray"]:
        """
        Synthesize text to speech
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio data as numpy array or None if failed
        """
        if not text.strip():
            return None
        
        try:
            if self.initialized:
                return self._synthesize_with_piper(text)
            else:
                logger.warning("TTS not available, text output only")
                return None
        
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return None
    
    def _synthesize_with_piper(self, text: str) -> Optional["np.ndarray"]:
        """
        Synthesize using piper-tts
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio data as numpy array
        """
        try:
            # Create temporary file for output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                output_path = tmp_file.name
            
            # Run piper
            process = subprocess.Popen(
                [
                    "piper",
                    "--model", self.voice,
                    "--output_file", output_path
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=text, timeout=30)
            
            if process.returncode == 0 and os.path.exists(output_path):
                # Load the audio file
                import wave
                with wave.open(output_path, 'rb') as wf:
                    audio_data = np.frombuffer(
                        wf.readframes(wf.getnframes()),
                        dtype=np.int16
                    )
                
                # Cleanup
                os.unlink(output_path)
                
                return audio_data.astype(np.float32) / 32768.0
            else:
                logger.error(f"Piper synthesis failed: {stderr}")
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return None
        
        except Exception as e:
            logger.error(f"Piper synthesis error: {e}")
            return None
    
    def synthesize_to_file(self, text: str, output_path: str) -> bool:
        """
        Synthesize text to audio file
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            logger.warning("TTS not initialized")
            return False
        
        try:
            process = subprocess.Popen(
                [
                    "piper",
                    "--model", self.voice,
                    "--output_file", output_path
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=text, timeout=30)
            
            if process.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Audio saved to {output_path}")
                return True
            else:
                logger.error(f"Failed to save audio: {stderr}")
                return False
        
        except Exception as e:
            logger.error(f"TTS file synthesis error: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """Check if engine is initialized"""
        return self.initialized
    
    def cleanup(self):
        """Cleanup resources"""
        self.initialized = False
        logger.info("TTS engine cleaned up")
