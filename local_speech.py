#!/usr/bin/env python3
"""
Local Speech Recognition Service for Abby

Uses Vosk for completely offline, privacy-respecting speech recognition.
No data sent to Google, Microsoft, or anyone else!

Integrates with PersonaPlex for natural conversation flow:
- VAD (Voice Activity Detection)
- Real-time streaming transcription
- Natural interrupts

This runs as part of the API server and provides:
- WebSocket endpoint for real-time streaming STT
- REST endpoint for audio file transcription
- Integration with PersonaPlex conversation manager
"""

import os
import json
import queue
import threading
import logging
import time
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# Vosk model path
MODEL_PATH = Path(__file__).parent / "models" / "vosk" / "vosk-model-small-en-us-0.15"

# Global instances
_recognizer = None
_model = None
_conversation_bridge = None


def get_vosk_model():
    """Get or initialize the Vosk model (lazy loading)"""
    global _model
    
    if _model is not None:
        return _model
    
    try:
        from vosk import Model, SetLogLevel
        
        # Reduce Vosk logging noise
        SetLogLevel(-1)
        
        if not MODEL_PATH.exists():
            logger.error(f"Vosk model not found at {MODEL_PATH}")
            logger.info("Download from: https://alphacephei.com/vosk/models")
            return None
        
        logger.info(f"Loading Vosk model from {MODEL_PATH}...")
        _model = Model(str(MODEL_PATH))
        logger.info("Vosk model loaded successfully!")
        return _model
        
    except ImportError:
        logger.error("Vosk not installed. Run: pip install vosk")
        return None
    except Exception as e:
        logger.error(f"Failed to load Vosk model: {e}")
        return None


class LocalSpeechRecognizer:
    """
    Real-time speech recognition using Vosk.
    Completely offline - no internet required!
    
    Features:
    - Noise reduction (filters out TV, background chatter)
    - Voice Activity Detection (only processes when you're speaking)
    - Works in noisy environments
    """
    
    def __init__(self, sample_rate=16000, noise_reduce=True, vad_enabled=True, vad_aggressiveness=2):
        """
        Initialize speech recognizer with noise reduction.
        
        Args:
            sample_rate: Audio sample rate (16000 recommended)
            noise_reduce: Enable background noise reduction
            vad_enabled: Enable Voice Activity Detection
            vad_aggressiveness: VAD aggressiveness (0-3, higher = more aggressive filtering)
        """
        self.sample_rate = sample_rate
        self.model = get_vosk_model()
        self.recognizer = None
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.result_callback = None
        self.partial_callback = None
        self._listen_thread = None
        
        # Noise reduction settings
        self.noise_reduce = noise_reduce
        self.noise_profile = None  # Will be learned from initial silence
        self._noise_samples = []
        self._noise_profile_ready = False
        
        # VAD settings
        self.vad_enabled = vad_enabled
        self.vad = None
        self.vad_aggressiveness = vad_aggressiveness
        self._speech_frames = []
        self._silence_frames = 0
        self._is_speaking = False
        self._min_speech_frames = 3  # Minimum frames to consider as speech
        self._max_silence_frames = 15  # Frames of silence before ending utterance
        
        # Initialize VAD
        if vad_enabled:
            try:
                import webrtcvad
                self.vad = webrtcvad.Vad(vad_aggressiveness)
                logger.info(f"VAD enabled (aggressiveness: {vad_aggressiveness})")
            except ImportError:
                logger.warning("webrtcvad not available - VAD disabled")
                self.vad_enabled = False
        
        if self.model:
            from vosk import KaldiRecognizer
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)
        
        logger.info(f"Speech recognizer initialized (noise_reduce={noise_reduce}, vad={vad_enabled})")
    
    @property
    def is_available(self):
        return self.model is not None and self.recognizer is not None
    
    def _reduce_noise(self, audio_data):
        """Apply noise reduction to audio"""
        if not self.noise_reduce:
            return audio_data
        
        try:
            import numpy as np
            import noisereduce as nr
            
            # Convert bytes to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Build noise profile from first few chunks (assumed to be ambient noise)
            if not self._noise_profile_ready:
                self._noise_samples.append(audio_np)
                if len(self._noise_samples) >= 5:  # ~0.5 seconds of noise profile
                    self.noise_profile = np.concatenate(self._noise_samples)
                    self._noise_profile_ready = True
                    logger.info("Noise profile captured - noise reduction active")
                return audio_data  # Return original until profile is ready
            
            # Apply noise reduction
            reduced = nr.reduce_noise(
                y=audio_np, 
                sr=self.sample_rate,
                y_noise=self.noise_profile,
                prop_decrease=0.8,  # Reduce noise by 80%
                stationary=True  # TV/constant noise is stationary
            )
            
            # Convert back to int16 bytes
            reduced_int16 = (reduced * 32768).astype(np.int16)
            return reduced_int16.tobytes()
            
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}")
            return audio_data
    
    def _is_speech(self, audio_chunk):
        """Check if audio chunk contains speech using VAD"""
        if not self.vad_enabled or self.vad is None:
            return True  # Assume speech if VAD disabled
        
        try:
            # VAD requires 10, 20, or 30ms frames at specific sample rates
            # For 16kHz, 20ms = 320 samples = 640 bytes
            frame_duration_ms = 20
            frame_size = int(self.sample_rate * frame_duration_ms / 1000) * 2  # *2 for int16
            
            # Check each frame in the chunk
            speech_frames = 0
            total_frames = 0
            
            for i in range(0, len(audio_chunk) - frame_size, frame_size):
                frame = audio_chunk[i:i + frame_size]
                if len(frame) == frame_size:
                    try:
                        if self.vad.is_speech(frame, self.sample_rate):
                            speech_frames += 1
                        total_frames += 1
                    except:
                        pass
            
            # Consider it speech if more than 30% of frames contain speech
            if total_frames > 0:
                speech_ratio = speech_frames / total_frames
                return speech_ratio > 0.3
            
            return False
            
        except Exception as e:
            logger.warning(f"VAD check failed: {e}")
            return True  # Assume speech on error
    
    def start_listening(self, on_result=None, on_partial=None):
        """Start listening to microphone"""
        if not self.is_available:
            logger.error("Speech recognizer not available")
            return False
        
        if self.is_listening:
            return True
        
        self.result_callback = on_result
        self.partial_callback = on_partial
        self.is_listening = True
        
        # Start audio capture thread
        self._listen_thread = threading.Thread(target=self._audio_capture_loop, daemon=True)
        self._listen_thread.start()
        
        # Start processing thread
        threading.Thread(target=self._process_audio_loop, daemon=True).start()
        
        logger.info("Started listening...")
        return True
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        logger.info("Stopped listening")
    
    def _audio_capture_loop(self):
        """Capture audio from microphone"""
        try:
            import sounddevice as sd
            
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio status: {status}")
                if self.is_listening:
                    self.audio_queue.put(bytes(indata))
            
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=4000,
                dtype='int16',
                channels=1,
                callback=audio_callback
            ):
                while self.is_listening:
                    threading.Event().wait(0.1)
                    
        except Exception as e:
            logger.error(f"Audio capture error: {e}")
            self.is_listening = False
    
    def _process_audio_loop(self):
        """Process audio queue with noise reduction and VAD"""
        while self.is_listening:
            try:
                data = self.audio_queue.get(timeout=0.5)
                
                # Apply noise reduction
                if self.noise_reduce:
                    data = self._reduce_noise(data)
                
                # Check for speech using VAD
                is_speech = self._is_speech(data)
                
                if is_speech:
                    self._silence_frames = 0
                    if not self._is_speaking:
                        self._is_speaking = True
                        logger.debug("Speech started")
                    
                    # Process with Vosk
                    if self.recognizer.AcceptWaveform(data):
                        # Final result
                        result = json.loads(self.recognizer.Result())
                        text = result.get('text', '').strip()
                        if text and self.result_callback:
                            self.result_callback(text)
                    else:
                        # Partial result
                        partial = json.loads(self.recognizer.PartialResult())
                        text = partial.get('partial', '').strip()
                        if text and self.partial_callback:
                            self.partial_callback(text)
                else:
                    # Silence detected
                    if self._is_speaking:
                        self._silence_frames += 1
                        
                        # Still process to catch trailing words
                        self.recognizer.AcceptWaveform(data)
                        
                        if self._silence_frames >= self._max_silence_frames:
                            # End of utterance
                            self._is_speaking = False
                            logger.debug("Speech ended")
                            
                            # Get final result
                            result = json.loads(self.recognizer.FinalResult())
                            text = result.get('text', '').strip()
                            if text and self.result_callback:
                                self.result_callback(text)
                        
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Recognition error: {e}")
    
    def recognize_audio(self, audio_data: bytes) -> str:
        """Recognize speech from audio bytes (WAV format, 16kHz mono)"""
        if not self.is_available:
            return ""
        
        from vosk import KaldiRecognizer
        
        rec = KaldiRecognizer(self.model, self.sample_rate)
        rec.AcceptWaveform(audio_data)
        result = json.loads(rec.FinalResult())
        return result.get('text', '').strip()


# Global recognizer instance for the API
_speech_recognizer = None


def get_speech_recognizer() -> LocalSpeechRecognizer:
    """Get the global speech recognizer instance"""
    global _speech_recognizer
    
    if _speech_recognizer is None:
        # Create with noise reduction and VAD enabled by default
        _speech_recognizer = LocalSpeechRecognizer(
            noise_reduce=True,
            vad_enabled=True,
            vad_aggressiveness=2  # 0-3, higher = more aggressive filtering
        )
    
    return _speech_recognizer


# Flask routes for speech recognition
def register_speech_routes(app):
    """Register speech recognition routes with Flask app"""
    from flask import request, jsonify, Response
    import base64
    import wave
    import io
    
    @app.route('/api/speech/status', methods=['GET'])
    def speech_status():
        """Check if local speech recognition is available"""
        recognizer = get_speech_recognizer()
        return jsonify({
            'available': recognizer.is_available,
            'listening': recognizer.is_listening,
            'noise_reduce': recognizer.noise_reduce,
            'vad_enabled': recognizer.vad_enabled,
            'noise_profile_ready': recognizer._noise_profile_ready,
            'model': str(MODEL_PATH) if MODEL_PATH.exists() else None
        })
    
    @app.route('/api/speech/settings', methods=['POST'])
    def speech_settings():
        """
        Update speech recognition settings.
        
        JSON body:
        - noise_reduce: bool - Enable/disable noise reduction
        - vad_aggressiveness: int (0-3) - VAD sensitivity (higher = filters more)
        - reset_noise_profile: bool - Reset and recapture noise profile
        """
        recognizer = get_speech_recognizer()
        data = request.get_json() or {}
        
        if 'noise_reduce' in data:
            recognizer.noise_reduce = bool(data['noise_reduce'])
            logger.info(f"Noise reduction: {recognizer.noise_reduce}")
        
        if 'vad_aggressiveness' in data:
            agg = max(0, min(3, int(data['vad_aggressiveness'])))
            if recognizer.vad:
                import webrtcvad
                recognizer.vad = webrtcvad.Vad(agg)
                recognizer.vad_aggressiveness = agg
                logger.info(f"VAD aggressiveness: {agg}")
        
        if data.get('reset_noise_profile'):
            recognizer._noise_samples = []
            recognizer._noise_profile_ready = False
            recognizer.noise_profile = None
            logger.info("Noise profile reset - will recapture from ambient sound")
        
        return jsonify({
            'success': True,
            'noise_reduce': recognizer.noise_reduce,
            'vad_enabled': recognizer.vad_enabled,
            'vad_aggressiveness': recognizer.vad_aggressiveness,
            'noise_profile_ready': recognizer._noise_profile_ready
        })
    
    @app.route('/api/speech/recognize', methods=['POST'])
    def recognize_speech():
        """
        Recognize speech from uploaded audio.
        
        Accepts:
        - audio/wav file upload
        - Base64 encoded audio in JSON body
        """
        recognizer = get_speech_recognizer()
        
        if not recognizer.is_available:
            return jsonify({'error': 'Speech recognition not available'}), 503
        
        try:
            # Handle file upload
            if 'audio' in request.files:
                audio_file = request.files['audio']
                audio_data = audio_file.read()
            
            # Handle base64 JSON
            elif request.is_json:
                data = request.get_json()
                audio_b64 = data.get('audio', '')
                audio_data = base64.b64decode(audio_b64)
            
            else:
                return jsonify({'error': 'No audio provided'}), 400
            
            # Convert to raw PCM if needed (skip WAV header)
            if audio_data[:4] == b'RIFF':
                # Parse WAV file
                with io.BytesIO(audio_data) as wav_io:
                    with wave.open(wav_io, 'rb') as wav:
                        audio_data = wav.readframes(wav.getnframes())
            
            # Recognize
            text = recognizer.recognize_audio(audio_data)
            
            return jsonify({
                'text': text,
                'success': True
            })
            
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/speech/start', methods=['POST'])
    def start_listening():
        """Start real-time speech recognition"""
        recognizer = get_speech_recognizer()
        
        if not recognizer.is_available:
            return jsonify({'error': 'Speech recognition not available'}), 503
        
        # Results will be sent via SSE or WebSocket
        success = recognizer.start_listening()
        
        return jsonify({
            'success': success,
            'listening': recognizer.is_listening
        })
    
    @app.route('/api/speech/stop', methods=['POST'])
    def stop_listening():
        """Stop real-time speech recognition"""
        recognizer = get_speech_recognizer()
        recognizer.stop_listening()
        
        return jsonify({
            'success': True,
            'listening': False
        })
    
    @app.route('/api/speech/stream', methods=['GET'])
    def local_speech_stream():
        """SSE stream for real-time speech recognition results"""
        recognizer = get_speech_recognizer()
        
        if not recognizer.is_available:
            return jsonify({'error': 'Speech recognition not available'}), 503
        
        result_queue = queue.Queue()
        
        def on_result(text):
            result_queue.put(('final', text))
        
        def on_partial(text):
            result_queue.put(('partial', text))
        
        def generate():
            recognizer.start_listening(on_result=on_result, on_partial=on_partial)
            
            try:
                while recognizer.is_listening:
                    try:
                        result_type, text = result_queue.get(timeout=0.5)
                        yield f"data: {json.dumps({'type': result_type, 'text': text})}\n\n"
                    except queue.Empty:
                        # Send keepalive
                        yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
            finally:
                recognizer.stop_listening()
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
    
    logger.info("Local speech recognition routes registered")


if __name__ == "__main__":
    # Test the speech recognizer
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Local Speech Recognition...")
    print("=" * 50)
    
    recognizer = get_speech_recognizer()
    
    if not recognizer.is_available:
        print("ERROR: Speech recognition not available!")
        print(f"Make sure Vosk model exists at: {MODEL_PATH}")
        exit(1)
    
    print("Speech recognizer is ready!")
    print("Speak into your microphone (Ctrl+C to stop)...")
    print()
    
    def on_result(text):
        print(f">>> {text}")
    
    def on_partial(text):
        print(f"... {text}", end='\r')
    
    try:
        recognizer.start_listening(on_result=on_result, on_partial=on_partial)
        
        # Keep running
        while True:
            threading.Event().wait(1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
        recognizer.stop_listening()
