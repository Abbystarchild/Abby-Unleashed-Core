"""
Speech-to-Text Engine using faster-whisper
PersonaPlex-inspired real-time transcription
"""
import logging
from typing import Optional, Iterator
from faster_whisper import WhisperModel
import numpy as np

logger = logging.getLogger(__name__)


class STTEngine:
    """
    Speech-to-Text engine using faster-whisper
    Provides real-time transcription capabilities
    """
    
    def __init__(
        self,
        model_size: str = "base.en",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        """
        Initialize STT engine
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
            compute_type: Compute type (int8, float16, float32)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None
        
        logger.info(f"Initializing STT engine with model: {model_size}")
    
    def initialize(self):
        """Load the Whisper model"""
        try:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            logger.info("STT engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize STT engine: {e}")
            raise
    
    def transcribe(
        self,
        audio: np.ndarray,
        language: str = "en",
        beam_size: int = 5
    ) -> str:
        """
        Transcribe audio to text
        
        Args:
            audio: Audio data as numpy array
            language: Language code
            beam_size: Beam size for decoding
            
        Returns:
            Transcribed text
        """
        if self.model is None:
            raise RuntimeError("STT engine not initialized. Call initialize() first.")
        
        try:
            segments, info = self.model.transcribe(
                audio,
                language=language,
                beam_size=beam_size,
                vad_filter=True
            )
            
            # Combine all segments
            text = " ".join([segment.text for segment in segments])
            logger.debug(f"Transcribed: {text}")
            return text.strip()
        
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    def transcribe_stream(
        self,
        audio_stream: Iterator[np.ndarray],
        language: str = "en"
    ) -> Iterator[str]:
        """
        Transcribe audio stream in real-time
        
        Args:
            audio_stream: Iterator of audio chunks
            language: Language code
            
        Yields:
            Transcribed text chunks
        """
        if self.model is None:
            raise RuntimeError("STT engine not initialized. Call initialize() first.")
        
        buffer = np.array([], dtype=np.float32)
        
        for audio_chunk in audio_stream:
            buffer = np.concatenate([buffer, audio_chunk])
            
            # Process when buffer reaches certain size (e.g., 3 seconds)
            if len(buffer) >= 16000 * 3:  # 3 seconds at 16kHz
                text = self.transcribe(buffer, language=language)
                if text:
                    yield text
                buffer = np.array([], dtype=np.float32)
    
    def is_initialized(self) -> bool:
        """Check if engine is initialized"""
        return self.model is not None
    
    def cleanup(self):
        """Cleanup resources"""
        self.model = None
        logger.info("STT engine cleaned up")
