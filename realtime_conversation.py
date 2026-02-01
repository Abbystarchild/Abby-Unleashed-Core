"""
Real-time Conversation System for Abby Unleashed
- Hot mic with Voice Activity Detection (VAD)
- Parallel display (rich content) + voice (summary)
- WebSocket streaming for real-time updates
- PersonaPlex-compatible audio streaming
"""

import asyncio
import json
import logging
import time
import re
import base64
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Callable
from enum import Enum
from collections import deque
import threading

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """States for the conversation flow."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    WAITING = "waiting"  # Waiting for user after speaking


class ContentType(Enum):
    """Types of rich content for display."""
    TEXT = "text"
    MARKDOWN = "markdown"
    CODE = "code"
    IMAGE = "image"
    VIDEO = "video"
    LINK = "link"
    FILE = "file"
    CHART = "chart"


@dataclass
class RichContent:
    """Rich content item for display."""
    type: ContentType
    content: str  # Text, URL, or base64 data
    title: Optional[str] = None
    language: Optional[str] = None  # For code blocks
    alt_text: Optional[str] = None  # For images
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            'type': self.type.value,
            'content': self.content,
            'title': self.title,
            'language': self.language,
            'alt_text': self.alt_text,
            'metadata': self.metadata
        }


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    id: str
    role: str  # 'user' or 'assistant'
    timestamp: float
    
    # User input
    transcript: Optional[str] = None
    audio_duration: Optional[float] = None
    
    # Assistant response
    voice_text: Optional[str] = None  # What gets spoken (summary)
    display_content: List[RichContent] = field(default_factory=list)
    full_text: Optional[str] = None  # Complete text response
    
    # Metadata
    processing_time: Optional[float] = None
    voice_duration: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'role': self.role,
            'timestamp': self.timestamp,
            'transcript': self.transcript,
            'audio_duration': self.audio_duration,
            'voice_text': self.voice_text,
            'display_content': [c.to_dict() for c in self.display_content],
            'full_text': self.full_text,
            'processing_time': self.processing_time,
            'voice_duration': self.voice_duration
        }


class VoiceActivityDetector:
    """
    Simple Voice Activity Detection.
    Detects speech vs silence to enable hot mic functionality.
    """
    
    def __init__(
        self,
        energy_threshold: float = 0.02,
        silence_duration: float = 1.5,
        min_speech_duration: float = 0.3
    ):
        self.energy_threshold = energy_threshold
        self.silence_duration = silence_duration
        self.min_speech_duration = min_speech_duration
        
        self.is_speaking = False
        self.speech_start_time: Optional[float] = None
        self.last_speech_time: Optional[float] = None
        self.energy_buffer = deque(maxlen=10)
        
    def process_audio_chunk(self, audio_data: bytes, sample_rate: int = 16000) -> dict:
        """
        Process an audio chunk and detect voice activity.
        Returns dict with speaking status and events.
        """
        import struct
        
        # Calculate RMS energy
        try:
            samples = struct.unpack(f'{len(audio_data)//2}h', audio_data)
            rms = (sum(s**2 for s in samples) / len(samples)) ** 0.5 / 32768
        except:
            rms = 0
            
        self.energy_buffer.append(rms)
        avg_energy = sum(self.energy_buffer) / len(self.energy_buffer)
        
        current_time = time.time()
        events = []
        
        # Detect speech start
        if avg_energy > self.energy_threshold and not self.is_speaking:
            self.is_speaking = True
            self.speech_start_time = current_time
            self.last_speech_time = current_time
            events.append('speech_start')
            
        # Update last speech time
        elif avg_energy > self.energy_threshold and self.is_speaking:
            self.last_speech_time = current_time
            
        # Detect speech end (silence threshold exceeded)
        elif self.is_speaking and self.last_speech_time:
            silence_time = current_time - self.last_speech_time
            if silence_time >= self.silence_duration:
                speech_duration = self.last_speech_time - self.speech_start_time
                if speech_duration >= self.min_speech_duration:
                    events.append('speech_end')
                else:
                    events.append('speech_cancelled')  # Too short, probably noise
                self.is_speaking = False
                self.speech_start_time = None
                
        return {
            'is_speaking': self.is_speaking,
            'energy': avg_energy,
            'events': events,
            'speech_duration': (current_time - self.speech_start_time) if self.speech_start_time else 0
        }
    
    def reset(self):
        """Reset VAD state."""
        self.is_speaking = False
        self.speech_start_time = None
        self.last_speech_time = None
        self.energy_buffer.clear()


class RichContentGenerator:
    """
    Generates rich display content from Abby's responses.
    Extracts images, code, links, etc. and creates display items.
    """
    
    @staticmethod
    def parse_response(full_response: str) -> List[RichContent]:
        """
        Parse a full response and extract rich content items.
        """
        content_items = []
        
        # Extract code blocks
        code_pattern = r'```(\w+)?\n(.*?)```'
        for match in re.finditer(code_pattern, full_response, re.DOTALL):
            language = match.group(1) or 'text'
            code = match.group(2).strip()
            content_items.append(RichContent(
                type=ContentType.CODE,
                content=code,
                language=language,
                title=f"{language.title()} Code"
            ))
        
        # Extract image URLs/references
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        for match in re.finditer(image_pattern, full_response):
            alt_text = match.group(1)
            url = match.group(2)
            content_items.append(RichContent(
                type=ContentType.IMAGE,
                content=url,
                alt_text=alt_text,
                title=alt_text or "Image"
            ))
        
        # Extract video URLs (YouTube, etc.)
        video_pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)'
        for match in re.finditer(video_pattern, full_response):
            video_id = match.group(1)
            content_items.append(RichContent(
                type=ContentType.VIDEO,
                content=f"https://www.youtube.com/embed/{video_id}",
                title="Video"
            ))
        
        # Extract regular links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(link_pattern, full_response):
            if not match.group(0).startswith('!'):  # Not an image
                title = match.group(1)
                url = match.group(2)
                if 'youtube' not in url.lower():  # Not already captured as video
                    content_items.append(RichContent(
                        type=ContentType.LINK,
                        content=url,
                        title=title
                    ))
        
        # Add the full text as markdown
        content_items.insert(0, RichContent(
            type=ContentType.MARKDOWN,
            content=full_response,
            title="Response"
        ))
        
        return content_items
    
    @staticmethod
    def generate_voice_summary(full_response: str, max_ratio: float = 0.35) -> str:
        """
        Generate a concise voice summary from the full response.
        Removes code blocks, URLs, emojis, and condenses for speech.
        """
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', full_response)
        
        # Remove markdown images
        text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
        
        # Convert links to just their text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove action blocks
        text = re.sub(r'```action:[\s\S]*?```', '', text)
        
        # Remove emojis and special characters that don't speak well
        # This regex removes most emojis and pictographs
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)  # Emoticons
        text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)  # Misc symbols
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)  # Transport
        text = re.sub(r'[\U0001F700-\U0001F77F]', '', text)  # Alchemical
        text = re.sub(r'[\U0001F780-\U0001F7FF]', '', text)  # Geometric
        text = re.sub(r'[\U0001F800-\U0001F8FF]', '', text)  # Arrows
        text = re.sub(r'[\U0001F900-\U0001F9FF]', '', text)  # Supplemental
        text = re.sub(r'[\U0001FA00-\U0001FA6F]', '', text)  # Chess
        text = re.sub(r'[\U0001FA70-\U0001FAFF]', '', text)  # Symbols
        text = re.sub(r'[\U00002702-\U000027B0]', '', text)  # Dingbats
        text = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', text)  # Flags
        
        # Remove markdown bold/italic markers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
        text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
        text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
        
        # Remove bullet points and list markers
        text = re.sub(r'^\s*[-*•]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # If short enough, return as-is
        if len(text) <= 300:  # About 30 seconds of speech
            return text
        
        # Otherwise, extract key sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Take first few sentences only - keep it SHORT for voice
        if len(sentences) <= 2:
            return text
        
        summary_sentences = sentences[:2]  # First two sentences max
        summary = ' '.join(summary_sentences)
        
        # Keep it short!
        if len(summary) > 300:
            summary = summary[:297] + "..."
        
        return summary


class RealtimeConversation:
    """
    Main real-time conversation manager.
    Handles hot mic, VAD, parallel processing, and rich output.
    """
    
    def __init__(self, abby_instance=None):
        self.abby = abby_instance
        self.state = ConversationState.IDLE
        self.vad = VoiceActivityDetector()
        self.content_generator = RichContentGenerator()
        
        self.conversation_history: List[ConversationTurn] = []
        self.current_turn: Optional[ConversationTurn] = None
        self.turn_counter = 0
        
        # Audio buffer for current speech
        self.audio_buffer = bytearray()
        
        # Callbacks for events
        self.on_state_change: Optional[Callable] = None
        self.on_transcript: Optional[Callable] = None
        self.on_response_start: Optional[Callable] = None
        self.on_display_content: Optional[Callable] = None
        self.on_voice_ready: Optional[Callable] = None
        self.on_turn_complete: Optional[Callable] = None
        
        # Settings
        self.hot_mic_enabled = True
        self.auto_resume_listening = True
        
        logger.info("RealtimeConversation initialized")
    
    def _generate_turn_id(self) -> str:
        self.turn_counter += 1
        return f"turn_{self.turn_counter}_{int(time.time()*1000)}"
    
    def _set_state(self, new_state: ConversationState):
        old_state = self.state
        self.state = new_state
        logger.info(f"State change: {old_state.value} -> {new_state.value}")
        if self.on_state_change:
            self.on_state_change(old_state, new_state)
    
    async def start_listening(self):
        """Start hot mic listening mode."""
        self._set_state(ConversationState.LISTENING)
        self.vad.reset()
        self.audio_buffer.clear()
        logger.info("Hot mic listening started")
    
    async def stop_listening(self):
        """Stop listening."""
        self._set_state(ConversationState.IDLE)
        self.vad.reset()
        logger.info("Listening stopped")
    
    async def process_audio_chunk(self, audio_data: bytes) -> dict:
        """
        Process incoming audio chunk.
        Returns VAD status and any events.
        """
        if self.state not in [ConversationState.LISTENING, ConversationState.WAITING]:
            return {'status': 'not_listening'}
        
        vad_result = self.vad.process_audio_chunk(audio_data)
        
        for event in vad_result['events']:
            if event == 'speech_start':
                # User started speaking
                self.audio_buffer.clear()
                logger.info("Speech detected - buffering audio")
                
            elif event == 'speech_end':
                # User stopped speaking - process the utterance
                logger.info("Speech ended - processing utterance")
                # Don't await here - let the caller handle async
                return {
                    **vad_result,
                    'action': 'process_utterance',
                    'audio_buffer_size': len(self.audio_buffer)
                }
            
            elif event == 'speech_cancelled':
                # Too short - ignore
                self.audio_buffer.clear()
                logger.debug("Speech too short - cancelled")
        
        # Buffer audio if speaking
        if vad_result['is_speaking']:
            self.audio_buffer.extend(audio_data)
        
        return vad_result
    
    async def process_transcript(self, transcript: str, user_context: dict = None, user_prompt_addition: str = "") -> dict:
        """
        Process a transcript (from STT) and generate response.
        Returns structured response with display content and voice text.
        
        Args:
            transcript: The user's transcribed speech
            user_context: Optional user presence context (who is speaking)
            user_prompt_addition: Optional prompt addition for user-specific behavior
        """
        if not transcript.strip():
            return {'error': 'Empty transcript'}
        
        start_time = time.time()
        self._set_state(ConversationState.PROCESSING)
        
        # Create turn for user input
        self.current_turn = ConversationTurn(
            id=self._generate_turn_id(),
            role='user',
            timestamp=time.time(),
            transcript=transcript
        )
        
        if self.on_transcript:
            self.on_transcript(transcript)
        
        try:
            # Get response from Abby (with user context if provided)
            if self.on_response_start:
                self.on_response_start()
            
            full_response = await self._get_abby_response(transcript, user_context, user_prompt_addition)
            
            # Generate rich display content
            display_content = self.content_generator.parse_response(full_response)
            
            # Generate voice summary
            voice_summary = self.content_generator.generate_voice_summary(full_response)
            
            # Create assistant turn
            assistant_turn = ConversationTurn(
                id=self._generate_turn_id(),
                role='assistant',
                timestamp=time.time(),
                full_text=full_response,
                voice_text=voice_summary,
                display_content=display_content,
                processing_time=time.time() - start_time
            )
            
            # Store in history
            self.conversation_history.append(self.current_turn)
            self.conversation_history.append(assistant_turn)
            
            # Notify display content ready
            if self.on_display_content:
                self.on_display_content(display_content)
            
            # Prepare voice output
            voice_audio = None
            try:
                voice_audio = await self._synthesize_voice(voice_summary)
            except Exception as e:
                logger.warning(f"Voice synthesis failed: {e}")
            
            if self.on_voice_ready:
                self.on_voice_ready(voice_summary, voice_audio)
            
            self._set_state(ConversationState.SPEAKING)
            
            response = {
                'turn_id': assistant_turn.id,
                'transcript': transcript,
                'display_content': [c.to_dict() for c in display_content],
                'voice_text': voice_summary,
                'voice_audio': base64.b64encode(voice_audio).decode() if voice_audio else None,
                'full_text': full_response,
                'processing_time': assistant_turn.processing_time
            }
            
            if self.on_turn_complete:
                self.on_turn_complete(assistant_turn)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing transcript: {e}")
            self._set_state(ConversationState.WAITING if self.hot_mic_enabled else ConversationState.IDLE)
            return {'error': str(e)}
    
    async def on_speaking_complete(self):
        """Called when TTS playback finishes."""
        if self.auto_resume_listening and self.hot_mic_enabled:
            self._set_state(ConversationState.LISTENING)
            self.vad.reset()
        else:
            self._set_state(ConversationState.WAITING)
    
    async def _get_abby_response(self, user_input: str, user_context: dict = None, user_prompt_addition: str = "") -> str:
        """
        Get response from Abby.
        
        Args:
            user_input: The user's message
            user_context: Optional user presence context for personalization
            user_prompt_addition: Optional system prompt addition for user-specific behavior
        """
        if self.abby:
            # Build context with user presence info
            context = {}
            if user_context:
                context['user_presence'] = user_context
            if user_prompt_addition:
                context['user_prompt_addition'] = user_prompt_addition
            
            # Use Abby's task execution with user context
            result = await asyncio.to_thread(
                self.abby.execute_task,
                user_input,
                context
            )
            return result.get('output', str(result))
        else:
            # Fallback - import and use directly
            try:
                from cli import Abby
                abby = Abby()
                result = abby.execute_task(user_input)
                return result.get('output', str(result))
            except Exception as e:
                logger.error(f"Could not get Abby response: {e}")
                return f"I heard you say: {user_input}. However, I couldn't process that right now."
    
    async def _synthesize_voice(self, text: str) -> Optional[bytes]:
        """Synthesize voice using ElevenLabs."""
        try:
            from speech_interface.elevenlabs_tts import get_tts
            tts = get_tts()
            if tts.is_configured:
                return tts.synthesize_bytes(text)
        except Exception as e:
            logger.warning(f"ElevenLabs synthesis failed: {e}")
        return None
    
    def get_conversation_history(self) -> List[dict]:
        """Get conversation history as dicts."""
        return [turn.to_dict() for turn in self.conversation_history]
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        self.turn_counter = 0


# Singleton instance
_realtime_conversation: Optional[RealtimeConversation] = None

def get_realtime_conversation() -> RealtimeConversation:
    """Get or create the realtime conversation instance."""
    global _realtime_conversation
    if _realtime_conversation is None:
        _realtime_conversation = RealtimeConversation()
    return _realtime_conversation
