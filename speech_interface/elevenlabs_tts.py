"""
ElevenLabs Text-to-Speech Integration for PersonaPlex

Uses your ElevenLabs voice clone to give Abby your voice!
Designed to integrate with PersonaPlex conversation flow while
using ElevenLabs for high-quality voice output.

Architecture:
- PersonaPlex handles: STT (speech-to-text), wake word, conversation flow
- ElevenLabs handles: TTS (text-to-speech) with your cloned voice

Setup:
1. Get your API key from https://elevenlabs.io/
2. Find your voice ID (from My Voices > Voice ID)
3. Add to .env:
   ELEVENLABS_API_KEY=your_api_key_here
   ELEVENLABS_VOICE_ID=your_voice_id_here
"""
import os
import io
import logging
import hashlib
import time
import asyncio
import json
import base64
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Generator, Callable, TYPE_CHECKING

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if TYPE_CHECKING:
    import numpy as np

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    websockets = None
    WEBSOCKETS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ElevenLabsTTS:
    """
    ElevenLabs Text-to-Speech client for PersonaPlex integration
    
    Features:
    - High quality voice cloning (your voice!)
    - Real-time WebSocket streaming for low latency
    - Standard REST API for reliable synthesis  
    - Audio caching to reduce API calls and costs
    - Numpy array output for PersonaPlex compatibility
    - Multiple voice settings (stability, similarity, style)
    """
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    WS_URL = "wss://api.elevenlabs.io/v1"
    
    def __init__(
        self,
        api_key: str = None,
        voice_id: str = None,
        model_id: str = "eleven_flash_v2_5",  # Flash for low latency
        cache_dir: str = None,
        sample_rate: int = 22050
    ):
        """
        Initialize ElevenLabs TTS
        
        Args:
            api_key: ElevenLabs API key (or from ELEVENLABS_API_KEY env var)
            voice_id: Voice ID to use (or from ELEVENLABS_VOICE_ID env var)
            model_id: Model to use:
                      - eleven_flash_v2_5: Low latency, good quality (recommended for real-time)
                      - eleven_multilingual_v2: Best quality, higher latency
                      - eleven_turbo_v2_5: Balance of speed and quality
            cache_dir: Directory for caching audio files
            sample_rate: Output sample rate for numpy arrays
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID")
        self.model_id = model_id
        self.sample_rate = sample_rate
        self.initialized = False
        
        # Cache setup
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent / "data" / "voice_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Voice settings optimized for conversational AI
        self.default_settings = {
            "stability": 0.5,           # 0-1: Lower = more expressive
            "similarity_boost": 0.75,   # 0-1: Higher = closer to original voice
            "style": 0.0,               # 0-1: Style exaggeration  
            "use_speaker_boost": True   # Enhances voice clarity
        }
        
        # WebSocket streaming config
        self.chunk_length_schedule = [50, 120, 160, 250]  # Optimized for real-time
        
        # Validate configuration
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured - TTS disabled")
        if not self.voice_id:
            logger.warning("ElevenLabs voice ID not configured - TTS disabled")
    
    # ==================== PersonaPlex Compatibility ====================
    
    def initialize(self) -> bool:
        """
        Initialize the TTS engine (PersonaPlex compatibility)
        
        Returns:
            True if configured and ready
        """
        if not REQUESTS_AVAILABLE:
            logger.error("requests library not available")
            return False
        
        if self.is_configured:
            # Test the connection
            try:
                user_info = self.get_user_info()
                if "subscription" in user_info:
                    chars = user_info["subscription"].get("character_count", 0)
                    limit = user_info["subscription"].get("character_limit", 0)
                    logger.info(f"ElevenLabs initialized - {chars}/{limit} characters used")
                    self.initialized = True
                    return True
            except Exception as e:
                logger.warning(f"ElevenLabs connection test failed: {e}")
        
        self.initialized = self.is_configured
        return self.initialized
    
    def is_initialized(self) -> bool:
        """Check if engine is initialized (PersonaPlex compatibility)"""
        return self.initialized
    
    def cleanup(self):
        """Cleanup resources (PersonaPlex compatibility)"""
        # Clear old cache files
        self.clear_cache(max_age_hours=168)  # 1 week
        logger.info("ElevenLabs TTS cleaned up")
    
    @property
    def is_configured(self) -> bool:
        """Check if ElevenLabs is properly configured"""
        return bool(self.api_key and self.voice_id)
    
    # ==================== API Helpers ====================
    
    def _get_headers(self, accept: str = "audio/mpeg") -> Dict[str, str]:
        """Get API request headers"""
        return {
            "Accept": accept,
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
    
    def _get_cache_path(self, text: str, settings: dict) -> Path:
        """Generate cache file path for text"""
        cache_key = f"{text}_{self.voice_id}_{str(settings)}"
        text_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return self.cache_dir / f"{text_hash}.mp3"
    
    # ==================== Account Info ====================
    
    def get_voices(self) -> Dict[str, Any]:
        """
        List all available voices in your ElevenLabs account
        
        Returns:
            Dict with 'voices' list containing voice info
        """
        if not self.api_key:
            return {"error": "API key not configured", "voices": []}
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/voices",
                headers={"xi-api-key": self.api_key},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return {"error": str(e), "voices": []}
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get user subscription info including remaining characters
        
        Returns:
            Dict with subscription info
        """
        if not self.api_key:
            return {"error": "API key not configured"}
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/user",
                headers={"xi-api-key": self.api_key},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {"error": str(e)}
    
    # ==================== Core Synthesis Methods ====================
    
    def synthesize(
        self,
        text: str,
        voice_id: str = None,
        settings: Dict[str, float] = None,
        use_cache: bool = True
    ) -> Optional["np.ndarray"]:
        """
        Synthesize speech from text - PersonaPlex compatible
        
        Returns numpy array for direct playback with sounddevice.
        
        Args:
            text: Text to convert to speech
            voice_id: Override default voice ID
            settings: Voice settings (stability, similarity_boost, etc.)
            use_cache: Whether to use cached audio if available
            
        Returns:
            Audio data as numpy array (float32), or None on error
        """
        if not self.is_configured:
            logger.error("ElevenLabs not configured")
            return None
        
        if not text or not text.strip():
            return None
        
        # Get raw audio bytes
        audio_bytes = self.synthesize_bytes(text, voice_id, settings, use_cache)
        
        if audio_bytes is None:
            return None
        
        # Convert to numpy array for PersonaPlex
        return self._bytes_to_numpy(audio_bytes)
    
    def synthesize_bytes(
        self,
        text: str,
        voice_id: str = None,
        settings: Dict[str, float] = None,
        use_cache: bool = True
    ) -> Optional[bytes]:
        """
        Synthesize speech from text - returns raw bytes
        
        Args:
            text: Text to convert to speech
            voice_id: Override default voice ID
            settings: Voice settings (stability, similarity_boost, etc.)
            use_cache: Whether to use cached audio if available
            
        Returns:
            Audio data as bytes (MP3 format), or None on error
        """
        if not self.is_configured:
            logger.error("ElevenLabs not configured")
            return None
        
        if not text or not text.strip():
            return None
        
        # Merge settings with defaults
        voice_settings = {**self.default_settings, **(settings or {})}
        voice = voice_id or self.voice_id
        
        # Check cache
        cache_path = self._get_cache_path(text, voice_settings)
        if use_cache and cache_path.exists():
            logger.debug(f"Using cached audio: {cache_path}")
            return cache_path.read_bytes()
        
        # Make API request
        url = f"{self.BASE_URL}/text-to-speech/{voice}"
        
        # Use PCM format for better numpy conversion
        params = {"output_format": "mp3_22050_32"}
        
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": voice_settings
        }
        
        try:
            logger.info(f"Synthesizing {len(text)} characters with ElevenLabs")
            start_time = time.time()
            
            response = requests.post(
                url,
                params=params,
                json=payload,
                headers=self._get_headers(),
                timeout=60
            )
            response.raise_for_status()
            
            audio_data = response.content
            elapsed = time.time() - start_time
            logger.info(f"Synthesis completed in {elapsed:.2f}s ({len(audio_data)} bytes)")
            
            # Cache the result
            if use_cache:
                cache_path.write_bytes(audio_data)
                logger.debug(f"Cached audio to: {cache_path}")
            
            return audio_data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"ElevenLabs API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return None
    
    def _bytes_to_numpy(self, audio_bytes: bytes) -> Optional["np.ndarray"]:
        """
        Convert MP3 bytes to numpy array for PersonaPlex playback
        
        Args:
            audio_bytes: MP3 audio data
            
        Returns:
            Numpy array (float32) suitable for sounddevice playback
        """
        if not NUMPY_AVAILABLE:
            logger.error("numpy not available")
            return None
        
        try:
            # Try using pydub if available
            try:
                from pydub import AudioSegment
                
                audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
                audio = audio.set_frame_rate(self.sample_rate).set_channels(1)
                
                # Convert to numpy array
                samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
                samples = samples / 32768.0  # Normalize to -1.0 to 1.0
                
                return samples
                
            except ImportError:
                pass
            
            # Fallback: use ffmpeg via subprocess
            try:
                import subprocess
                
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_in:
                    tmp_in.write(audio_bytes)
                    tmp_in_path = tmp_in.name
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_out:
                    tmp_out_path = tmp_out.name
                
                # Convert MP3 to WAV using ffmpeg
                subprocess.run([
                    "ffmpeg", "-y", "-i", tmp_in_path,
                    "-ar", str(self.sample_rate),
                    "-ac", "1",
                    "-f", "wav",
                    tmp_out_path
                ], capture_output=True, check=True)
                
                # Read WAV file
                import wave
                with wave.open(tmp_out_path, 'rb') as wav:
                    frames = wav.readframes(wav.getnframes())
                    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
                    samples = samples / 32768.0
                
                # Cleanup
                os.unlink(tmp_in_path)
                os.unlink(tmp_out_path)
                
                return samples
                
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.warning(f"ffmpeg conversion failed: {e}")
            
            # Last resort: return None and let caller handle bytes directly
            logger.warning("Could not convert audio to numpy - install pydub or ffmpeg")
            return None
            
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            return None
    
    # ==================== Streaming Methods ====================
    
    def synthesize_stream(
        self,
        text: str,
        voice_id: str = None,
        settings: Dict[str, float] = None
    ) -> Generator[bytes, None, None]:
        """
        Synthesize speech with streaming response (HTTP)
        
        Yields chunks of audio data as they're generated.
        Better for long text - reduces time to first audio.
        
        Args:
            text: Text to convert
            voice_id: Override voice ID
            settings: Voice settings
            
        Yields:
            Chunks of audio data (MP3)
        """
        if not self.is_configured:
            logger.error("ElevenLabs not configured")
            return
        
        voice_settings = {**self.default_settings, **(settings or {})}
        voice = voice_id or self.voice_id
        
        url = f"{self.BASE_URL}/text-to-speech/{voice}/stream"
        
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": voice_settings
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                stream=True,
                timeout=60
            )
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Streaming synthesis error: {e}")
    
    async def synthesize_websocket(
        self,
        text: str,
        voice_id: str = None,
        settings: Dict[str, float] = None,
        on_audio_chunk: Callable[[bytes], None] = None
    ) -> Optional[bytes]:
        """
        Synthesize speech via WebSocket for lowest latency
        
        This is the fastest method - audio starts streaming before
        the full text is processed. Ideal for real-time conversation.
        
        Args:
            text: Text to convert
            voice_id: Override voice ID  
            settings: Voice settings
            on_audio_chunk: Callback for each audio chunk (for streaming playback)
            
        Returns:
            Complete audio as bytes, or None on error
        """
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("websockets library not available, falling back to HTTP")
            return self.synthesize_bytes(text, voice_id, settings, use_cache=False)
        
        if not self.is_configured:
            logger.error("ElevenLabs not configured")
            return None
        
        voice_settings = {**self.default_settings, **(settings or {})}
        voice = voice_id or self.voice_id
        
        uri = f"{self.WS_URL}/text-to-speech/{voice}/stream-input?model_id={self.model_id}"
        
        audio_chunks = []
        
        try:
            async with websockets.connect(uri) as ws:
                # Initialize connection with settings
                await ws.send(json.dumps({
                    "text": " ",  # Initial space to prime
                    "voice_settings": voice_settings,
                    "generation_config": {
                        "chunk_length_schedule": self.chunk_length_schedule
                    },
                    "xi_api_key": self.api_key
                }))
                
                # Send the actual text
                await ws.send(json.dumps({"text": text}))
                
                # Signal end of text and flush
                await ws.send(json.dumps({"text": "", "flush": True}))
                
                # Receive audio chunks
                while True:
                    try:
                        message = await ws.recv()
                        data = json.loads(message)
                        
                        if data.get("audio"):
                            chunk = base64.b64decode(data["audio"])
                            audio_chunks.append(chunk)
                            
                            if on_audio_chunk:
                                on_audio_chunk(chunk)
                        
                        if data.get("isFinal"):
                            break
                            
                    except websockets.exceptions.ConnectionClosed:
                        break
            
            if audio_chunks:
                return b"".join(audio_chunks)
            return None
            
        except Exception as e:
            logger.error(f"WebSocket synthesis error: {e}")
            return None
    
    def synthesize_realtime(
        self,
        text: str,
        voice_id: str = None,
        settings: Dict[str, float] = None
    ) -> Optional[bytes]:
        """
        Synthesize with WebSocket (sync wrapper for async method)
        
        Args:
            text: Text to convert
            voice_id: Override voice ID
            settings: Voice settings
            
        Returns:
            Audio bytes or None
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.synthesize_websocket(text, voice_id, settings)
        )
    
    # ==================== Cache Management ====================
    
    def clear_cache(self, max_age_hours: int = 24):
        """
        Clear old cached audio files
        
        Args:
            max_age_hours: Delete files older than this
        """
        if not self.cache_dir.exists():
            return
        
        now = time.time()
        max_age_seconds = max_age_hours * 3600
        
        cleared = 0
        for file in self.cache_dir.glob("*.mp3"):
            if now - file.stat().st_mtime > max_age_seconds:
                file.unlink()
                cleared += 1
        
        if cleared:
            logger.info(f"Cleared {cleared} cached audio files")


# ==================== Singleton Instance ====================

_tts_instance: Optional[ElevenLabsTTS] = None


def get_tts() -> ElevenLabsTTS:
    """Get the ElevenLabs TTS instance"""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = ElevenLabsTTS()
    return _tts_instance


# ==================== Quick Test ====================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    tts = get_tts()
    
    if tts.is_configured:
        print("ElevenLabs configured!")
        
        # Get user info
        info = tts.get_user_info()
        if "subscription" in info:
            chars = info["subscription"].get("character_count", 0)
            limit = info["subscription"].get("character_limit", 0)
            print(f"Characters used: {chars}/{limit}")
        
        # List voices
        voices = tts.get_voices()
        print(f"\nAvailable voices ({len(voices.get('voices', []))}):")
        for v in voices.get("voices", [])[:5]:
            print(f"  - {v['name']}: {v['voice_id']}")
        
        # Test synthesis
        print("\nTesting synthesis...")
        audio = tts.synthesize("Hello! This is a test of the ElevenLabs voice synthesis.")
        if audio is not None:
            print(f"✅ Generated numpy array: shape={audio.shape}, dtype={audio.dtype}")
        else:
            print("❌ Synthesis failed (may need pydub or ffmpeg for numpy conversion)")
            
            # Try bytes version
            audio_bytes = tts.synthesize_bytes("Hello! This is a test.")
            if audio_bytes:
                print(f"✅ Generated {len(audio_bytes)} bytes of audio (MP3)")
    else:
        print("ElevenLabs not configured. Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in .env")
