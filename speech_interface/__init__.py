"""
Speech Interface Module - PersonaPlex Integration
Real-time speech-to-speech AI interaction

Supports multiple TTS backends:
- Piper TTS (local, free)
- ElevenLabs (cloud, voice cloning)
"""

from .stt_engine import STTEngine
from .tts_engine import TTSEngine
from .vad_detector import VADDetector
from .wake_word import WakeWordDetector
from .conversation_manager import ConversationManager
from .elevenlabs_tts import ElevenLabsTTS, get_tts

__all__ = [
    'STTEngine',
    'TTSEngine',
    'ElevenLabsTTS',
    'get_tts',
    'VADDetector',
    'WakeWordDetector',
    'ConversationManager'
]
