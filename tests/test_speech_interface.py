"""
Tests for PersonaPlex Speech Interface Integration
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from speech_interface import (
    STTEngine,
    TTSEngine,
    VADDetector,
    WakeWordDetector,
    ConversationManager
)


class TestSTTEngine:
    """Test Speech-to-Text Engine"""
    
    def test_initialization(self):
        """Test STT engine initialization"""
        engine = STTEngine(model_size="base.en")
        assert engine.model_size == "base.en"
        assert engine.device == "cpu"
        assert not engine.is_initialized()
    
    @patch('speech_interface.stt_engine.WhisperModel')
    def test_initialize(self, mock_whisper):
        """Test STT engine model loading"""
        engine = STTEngine()
        engine.initialize()
        assert engine.is_initialized()
        mock_whisper.assert_called_once()
    
    def test_transcribe_not_initialized(self):
        """Test transcription fails when not initialized"""
        engine = STTEngine()
        audio = np.random.randn(16000).astype(np.float32)
        
        with pytest.raises(RuntimeError):
            engine.transcribe(audio)
    
    @patch('speech_interface.stt_engine.WhisperModel')
    def test_transcribe(self, mock_whisper):
        """Test audio transcription"""
        # Setup mock
        mock_model = MagicMock()
        mock_segment = Mock()
        mock_segment.text = "Hello world"
        mock_model.transcribe.return_value = ([mock_segment], None)
        mock_whisper.return_value = mock_model
        
        # Test
        engine = STTEngine()
        engine.initialize()
        
        audio = np.random.randn(16000).astype(np.float32)
        text = engine.transcribe(audio)
        
        assert text == "Hello world"
        mock_model.transcribe.assert_called_once()
    
    def test_cleanup(self):
        """Test cleanup"""
        engine = STTEngine()
        engine.model = Mock()
        engine.cleanup()
        assert engine.model is None


class TestTTSEngine:
    """Test Text-to-Speech Engine"""
    
    def test_initialization(self):
        """Test TTS engine initialization"""
        engine = TTSEngine(voice="en_US-amy-medium")
        assert engine.voice == "en_US-amy-medium"
        assert not engine.is_initialized()
    
    @patch('subprocess.run')
    def test_initialize_success(self, mock_run):
        """Test TTS engine initialization success"""
        mock_run.return_value = Mock(returncode=0)
        
        engine = TTSEngine()
        engine.initialize()
        
        assert engine.is_initialized()
    
    @patch('subprocess.run')
    def test_initialize_failure(self, mock_run):
        """Test TTS engine initialization failure"""
        mock_run.side_effect = FileNotFoundError()
        
        engine = TTSEngine()
        engine.initialize()
        
        assert not engine.is_initialized()
    
    def test_synthesize_empty_text(self):
        """Test synthesis with empty text"""
        engine = TTSEngine()
        result = engine.synthesize("")
        assert result is None
    
    def test_cleanup(self):
        """Test cleanup"""
        engine = TTSEngine()
        engine.initialized = True
        engine.cleanup()
        assert not engine.initialized


class TestVADDetector:
    """Test Voice Activity Detection"""
    
    def test_initialization(self):
        """Test VAD detector initialization"""
        detector = VADDetector(threshold=0.5)
        assert detector.threshold == 0.5
        assert detector.sample_rate == 16000
        assert not detector.is_initialized()
    
    @patch('torch.hub.load')
    def test_initialize(self, mock_torch_load):
        """Test VAD initialization"""
        mock_model = Mock()
        mock_torch_load.return_value = (mock_model, None)
        
        detector = VADDetector()
        detector.initialize()
        
        assert detector.is_initialized()
    
    def test_fallback_detection(self):
        """Test fallback energy-based detection"""
        detector = VADDetector()
        
        # Silent audio
        silent_audio = np.zeros(1600, dtype=np.float32)
        assert not detector.detect(silent_audio)
        
        # Loud audio
        loud_audio = np.random.randn(1600).astype(np.float32) * 0.5
        # May or may not detect depending on random values
        result = detector.detect(loud_audio)
        assert isinstance(result, bool)
    
    def test_cleanup(self):
        """Test cleanup"""
        detector = VADDetector()
        detector.model = Mock()
        detector.cleanup()
        assert detector.model is None


class TestWakeWordDetector:
    """Test Wake Word Detection"""
    
    def test_initialization(self):
        """Test wake word detector initialization"""
        detector = WakeWordDetector(wake_word="hey abby")
        assert detector.wake_word == "hey abby"
        assert not detector.is_initialized()
    
    def test_initialize_without_key(self):
        """Test initialization without access key"""
        detector = WakeWordDetector()
        detector.initialize()
        assert detector.is_initialized()
    
    def test_detect_in_text(self):
        """Test wake word detection in text"""
        detector = WakeWordDetector(wake_word="hey abby")
        
        assert detector.detect_in_text("Hey Abby, how are you?")
        assert detector.detect_in_text("hey abby help me")
        assert not detector.detect_in_text("Hello there")
    
    def test_get_frame_length(self):
        """Test frame length getter"""
        detector = WakeWordDetector()
        frame_length = detector.get_frame_length()
        assert frame_length == 512
    
    def test_get_sample_rate(self):
        """Test sample rate getter"""
        detector = WakeWordDetector()
        sample_rate = detector.get_sample_rate()
        assert sample_rate == 16000
    
    def test_cleanup(self):
        """Test cleanup"""
        detector = WakeWordDetector()
        detector.initialized = True
        detector.cleanup()
        assert not detector.initialized


class TestConversationManager:
    """Test Conversation Manager"""
    
    def test_initialization(self):
        """Test conversation manager initialization"""
        manager = ConversationManager()
        assert manager.sample_rate == 16000
        assert not manager.is_listening
        assert manager.stt is not None
        assert manager.tts is not None
        assert manager.vad is not None
        assert manager.wake_word_detector is not None
    
    @patch('speech_interface.conversation_manager.STTEngine')
    @patch('speech_interface.conversation_manager.TTSEngine')
    @patch('speech_interface.conversation_manager.VADDetector')
    @patch('speech_interface.conversation_manager.WakeWordDetector')
    def test_initialize_all_components(self, mock_wake, mock_vad, mock_tts, mock_stt):
        """Test initialization of all components"""
        # Setup mocks
        for mock in [mock_stt, mock_tts, mock_vad, mock_wake]:
            mock.return_value.initialize.return_value = None
        
        manager = ConversationManager()
        result = manager.initialize()
        
        assert result is True
    
    def test_set_task_executor(self):
        """Test setting task executor"""
        manager = ConversationManager()
        
        def dummy_executor(text: str) -> str:
            return f"Response to: {text}"
        
        manager.set_task_executor(dummy_executor)
        assert manager.task_executor is not None
    
    def test_process_text(self):
        """Test text processing"""
        manager = ConversationManager()
        
        def dummy_executor(text: str) -> str:
            return f"Processed: {text}"
        
        manager.set_task_executor(dummy_executor)
        
        result = manager.process_text("Hello")
        assert result == "Processed: Hello"
    
    def test_process_text_no_executor(self):
        """Test text processing without executor"""
        manager = ConversationManager()
        result = manager.process_text("Hello")
        assert "No task executor" in result
    
    def test_cleanup(self):
        """Test cleanup"""
        manager = ConversationManager()
        manager.is_listening = True
        manager.cleanup()
        assert not manager.is_listening


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
