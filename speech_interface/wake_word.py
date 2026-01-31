"""
Wake Word Detection using pvporcupine
Detects "Hey Abby" or custom wake phrases
"""
import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Wake word detector using Porcupine
    Detects custom wake words like "Hey Abby"
    """
    
    def __init__(
        self,
        wake_word: str = "hey abby",
        access_key: Optional[str] = None,
        sensitivity: float = 0.5
    ):
        """
        Initialize wake word detector
        
        Args:
            wake_word: Wake word phrase
            access_key: Porcupine access key (required for custom words)
            sensitivity: Detection sensitivity (0-1)
        """
        self.wake_word = wake_word.lower()
        self.access_key = access_key
        self.sensitivity = sensitivity
        self.porcupine = None
        self.initialized = False
        
        logger.info(f"Initializing wake word detector for: '{wake_word}'")
    
    def initialize(self):
        """Initialize the wake word detector"""
        try:
            # Try to import pvporcupine
            import pvporcupine
            
            # For now, we'll use a simple implementation
            # In production, you'd need a Porcupine access key
            if self.access_key:
                # Initialize with custom keyword
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keywords=[self.wake_word],
                    sensitivities=[self.sensitivity]
                )
                self.initialized = True
                logger.info("Wake word detector initialized with Porcupine")
            else:
                logger.warning("No Porcupine access key provided, using fallback detection")
                self.initialized = True
        
        except ImportError:
            logger.warning("pvporcupine not available, using fallback detection")
            self.initialized = True
        
        except Exception as e:
            logger.error(f"Failed to initialize wake word detector: {e}")
            self.initialized = True  # Use fallback
    
    def detect(self, audio_chunk: np.ndarray) -> bool:
        """
        Detect wake word in audio chunk
        
        Args:
            audio_chunk: Audio data as numpy array
            
        Returns:
            True if wake word detected, False otherwise
        """
        if not self.initialized:
            return False
        
        try:
            if self.porcupine is not None:
                # Use Porcupine
                # Convert to 16-bit PCM
                pcm = (audio_chunk * 32767).astype(np.int16)
                
                keyword_index = self.porcupine.process(pcm)
                return keyword_index >= 0
            else:
                # Fallback: always return False
                # In a real implementation, you might use a simple keyword spotting
                return False
        
        except Exception as e:
            logger.error(f"Wake word detection error: {e}")
            return False
    
    def detect_in_text(self, text: str) -> bool:
        """
        Simple fallback: detect wake word in transcribed text
        
        Args:
            text: Transcribed text
            
        Returns:
            True if wake word found in text
        """
        return self.wake_word in text.lower()
    
    def get_frame_length(self) -> int:
        """
        Get required audio frame length for processing
        
        Returns:
            Frame length in samples
        """
        if self.porcupine is not None:
            return self.porcupine.frame_length
        return 512  # Default frame length
    
    def get_sample_rate(self) -> int:
        """
        Get required sample rate
        
        Returns:
            Sample rate in Hz
        """
        if self.porcupine is not None:
            return self.porcupine.sample_rate
        return 16000  # Default sample rate
    
    def is_initialized(self) -> bool:
        """Check if detector is initialized"""
        return self.initialized
    
    def cleanup(self):
        """Cleanup resources"""
        if self.porcupine is not None:
            self.porcupine.delete()
            self.porcupine = None
        
        self.initialized = False
        logger.info("Wake word detector cleaned up")
