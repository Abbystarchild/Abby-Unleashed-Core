"""
Speech Interface Module - PersonaPlex Integration
Real-time speech-to-speech AI interaction
"""

from .stt_engine import STTEngine
from .tts_engine import TTSEngine
from .vad_detector import VADDetector
from .wake_word import WakeWordDetector
from .conversation_manager import ConversationManager

__all__ = [
    'STTEngine',
    'TTSEngine',
    'VADDetector',
    'WakeWordDetector',
    'ConversationManager'
]
