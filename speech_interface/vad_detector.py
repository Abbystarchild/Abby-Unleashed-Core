"""
Voice Activity Detection using silero-vad
Detects when speech is present in audio
"""
import logging
from typing import Optional, TYPE_CHECKING

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    import numpy as np
except ImportError:
    np = None

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)


class VADDetector:
    """
    Voice Activity Detector using Silero VAD
    Detects speech presence in audio streams
    """
    
    def __init__(
        self,
        threshold: float = 0.5,
        sample_rate: int = 16000,
        chunk_duration: float = 0.03
    ):
        """
        Initialize VAD detector
        
        Args:
            threshold: Detection threshold (0-1)
            sample_rate: Audio sample rate
            chunk_duration: Duration of each audio chunk in seconds
        """
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self.model = None
        
        logger.info(f"Initializing VAD detector (threshold: {threshold})")
    
    def initialize(self):
        """Load the Silero VAD model"""
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available. VAD will use fallback energy detection.")
            return
        
        try:
            # Load Silero VAD model
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            
            logger.info("VAD detector initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize VAD detector: {e}")
            logger.warning("VAD will be disabled")
            self.model = None
    
    def detect(self, audio: "np.ndarray") -> bool:
        """
        Detect voice activity in audio
        
        Args:
            audio: Audio data as numpy array
            
        Returns:
            True if voice detected, False otherwise
        """
        if self.model is None:
            # Fallback: assume voice if audio has sufficient energy
            return self._fallback_detection(audio)
        
        try:
            # Convert to tensor
            audio_tensor = torch.from_numpy(audio).float()
            
            # Get VAD probability
            speech_prob = self.model(audio_tensor, self.sample_rate).item()
            
            return speech_prob > self.threshold
        
        except Exception as e:
            logger.error(f"VAD detection error: {e}")
            return self._fallback_detection(audio)
    
    def _fallback_detection(self, audio: "np.ndarray") -> bool:
        """
        Fallback detection using energy threshold
        
        Args:
            audio: Audio data
            
        Returns:
            True if energy above threshold
        """
        if len(audio) == 0:
            return False
        
        # Simple energy-based detection
        energy = np.sqrt(np.mean(audio ** 2))
        return energy > 0.01  # Threshold for energy
    
    def get_speech_segments(
        self,
        audio: "np.ndarray",
        min_speech_duration: float = 0.5,
        min_silence_duration: float = 0.3
    ) -> list:
        """
        Get speech segments from audio
        
        Args:
            audio: Audio data
            min_speech_duration: Minimum speech duration in seconds
            min_silence_duration: Minimum silence duration in seconds
            
        Returns:
            List of (start, end) tuples in samples
        """
        if self.model is None:
            logger.warning("VAD not initialized, using fallback")
            return [(0, len(audio))]
        
        try:
            segments = []
            in_speech = False
            speech_start = 0
            
            # Process in chunks
            for i in range(0, len(audio), self.chunk_size):
                chunk = audio[i:i + self.chunk_size]
                
                if len(chunk) < self.chunk_size:
                    # Pad last chunk
                    chunk = np.pad(chunk, (0, self.chunk_size - len(chunk)))
                
                is_speech = self.detect(chunk)
                
                if is_speech and not in_speech:
                    # Start of speech
                    speech_start = i
                    in_speech = True
                
                elif not is_speech and in_speech:
                    # End of speech
                    speech_duration = (i - speech_start) / self.sample_rate
                    
                    if speech_duration >= min_speech_duration:
                        segments.append((speech_start, i))
                    
                    in_speech = False
            
            # Handle case where speech continues to end
            if in_speech:
                speech_duration = (len(audio) - speech_start) / self.sample_rate
                if speech_duration >= min_speech_duration:
                    segments.append((speech_start, len(audio)))
            
            return segments
        
        except Exception as e:
            logger.error(f"Error getting speech segments: {e}")
            return [(0, len(audio))]
    
    def is_initialized(self) -> bool:
        """Check if detector is initialized"""
        return self.model is not None
    
    def cleanup(self):
        """Cleanup resources"""
        self.model = None
        logger.info("VAD detector cleaned up")
