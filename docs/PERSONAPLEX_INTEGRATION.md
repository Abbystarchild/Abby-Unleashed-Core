# PersonaPlex Integration Guide

## Overview

PersonaPlex is now fully integrated into Abby Unleashed Core, providing real-time speech-to-speech AI interaction capabilities. This integration brings natural voice conversations with wake word detection, automatic speech recognition, and text-to-speech synthesis—all running 100% offline.

## Features

### 🎙️ Speech-to-Text (STT)
- **Engine**: faster-whisper (Whisper models)
- **Models**: tiny, base, small, medium, large
- **Languages**: Multi-language support (default: English)
- **Performance**: Real-time transcription with low latency

### 🔊 Text-to-Speech (TTS)
- **Engine**: piper-tts
- **Voices**: Multiple natural-sounding voices
- **Quality**: High-quality synthesis
- **Speed**: Fast synthesis for real-time conversation

### 👂 Voice Activity Detection (VAD)
- **Engine**: silero-vad
- **Purpose**: Detects when user is speaking
- **Fallback**: Energy-based detection when PyTorch unavailable

### 🎯 Wake Word Detection
- **Engine**: pvporcupine
- **Default**: "Hey Abby"
- **Customizable**: Configure your own wake word
- **Fallback**: Text-based detection when Porcupine unavailable

### 💬 Conversation Manager
- **Flow**: Orchestrates complete speech-to-speech interaction
- **State Management**: Handles conversation state and context
- **Integration**: Seamlessly integrates with task execution engine

## Installation

### Prerequisites

```bash
# Python 3.9 or higher
python --version

# Ollama (for LLM backend)
# Download from https://ollama.ai/
```

### Install Dependencies

```bash
# Install all dependencies including speech libraries
pip install -r requirements.txt

# Or install speech components separately
pip install torch>=2.0.0
pip install faster-whisper>=0.10.0
pip install piper-tts>=1.2.0
pip install sounddevice>=0.4.6
pip install pvporcupine>=3.0.0
```

### Optional: Porcupine Access Key

For custom wake word detection, get a free API key from [Picovoice Console](https://console.picovoice.ai/):

```bash
# Add to .env file
PORCUPINE_ACCESS_KEY=your_key_here
```

## Configuration

### Environment Variables

Edit `.env` file:

```bash
# Speech Configuration (PersonaPlex Integration)
STT_MODEL=base.en              # Whisper model size
TTS_VOICE=en_US-amy-medium     # Piper voice model
WAKE_WORD=hey abby             # Wake word phrase
PORCUPINE_ACCESS_KEY=          # Optional: For custom wake words
```

### System Configuration

Edit `config/system_config.yaml`:

```yaml
speech:
  stt_model: "base.en"
  tts_voice: "en_US-amy-medium"
  wake_word: "hey abby"
  vad_threshold: 0.5
  sample_rate: 16000
  chunk_duration: 0.03  # seconds
```

## Usage

### Voice Mode CLI

Start the voice interface:

```bash
python cli.py voice
```

**Workflow:**
1. System initializes speech components
2. Listens for wake word ("Hey Abby")
3. When activated, listens for your request
4. Processes request and speaks response
5. Returns to wake word listening

### Text Mode (Default)

If speech components unavailable, automatically falls back to text:

```bash
python cli.py text
```

### Direct Task Execution

Execute tasks without interactive mode:

```bash
python cli.py task --task "Your task here"
```

## Example Usage

### Basic Demo

```python
from speech_interface import ConversationManager

# Initialize conversation manager
manager = ConversationManager(
    stt_model="base.en",
    tts_voice="en_US-amy-medium",
    wake_word="hey abby"
)

# Initialize components
if manager.initialize():
    # Set task executor
    def handle_task(text: str) -> str:
        return f"You said: {text}"
    
    manager.set_task_executor(handle_task)
    
    # Start listening
    manager.start_listening()
    
    # ... Keep running ...
    
    # Cleanup
    manager.cleanup()
```

### Text-Only Processing

```python
# Process text without speech recognition
response = manager.process_text("Hello, how are you?")
print(response)
```

### Text-to-Speech Only

```python
# Speak text without transcription
manager.speak("Welcome to PersonaPlex!")
```

## Component Architecture

```
┌─────────────────────────────────────────┐
│      Conversation Manager               │
│  (Orchestrates speech-to-speech flow)   │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌────────┐      ┌─────────┐
│  STT   │      │   TTS   │
│Engine  │      │ Engine  │
└────────┘      └─────────┘
    ▲                 │
    │                 │
┌───┴────┐       ┌────▼────┐
│  VAD   │       │ Audio   │
│Detector│       │ Output  │
└───┬────┘       └─────────┘
    │
┌───▼────────┐
│ Wake Word  │
│  Detector  │
└────────────┘
```

## API Reference

### STTEngine

```python
from speech_interface import STTEngine

# Initialize
stt = STTEngine(model_size="base.en", device="cpu")
stt.initialize()

# Transcribe audio
text = stt.transcribe(audio_data)

# Stream transcription
for text in stt.transcribe_stream(audio_stream):
    print(text)
```

### TTSEngine

```python
from speech_interface import TTSEngine

# Initialize
tts = TTSEngine(voice="en_US-amy-medium")
tts.initialize()

# Synthesize speech
audio = tts.synthesize("Hello world")

# Save to file
tts.synthesize_to_file("Hello world", "output.wav")
```

### VADDetector

```python
from speech_interface import VADDetector

# Initialize
vad = VADDetector(threshold=0.5)
vad.initialize()

# Detect speech in audio
is_speech = vad.detect(audio_chunk)

# Get speech segments
segments = vad.get_speech_segments(audio_data)
```

### WakeWordDetector

```python
from speech_interface import WakeWordDetector

# Initialize
detector = WakeWordDetector(
    wake_word="hey abby",
    access_key="your_key"  # Optional
)
detector.initialize()

# Detect wake word
detected = detector.detect(audio_chunk)

# Detect in text (fallback)
detected = detector.detect_in_text("Hey Abby, help me")
```

## Troubleshooting

### Speech Components Not Available

If you see "Speech components unavailable":

1. **Check dependencies**:
   ```bash
   pip list | grep -E "whisper|piper|torch|sounddevice"
   ```

2. **Install missing packages**:
   ```bash
   pip install faster-whisper piper-tts torch sounddevice
   ```

3. **Verify audio devices**:
   ```python
   import sounddevice as sd
   print(sd.query_devices())
   ```

### No Audio Output

1. **Check system audio**:
   - Ensure speakers/headphones are connected
   - Check system volume settings

2. **Test with simple audio**:
   ```python
   import sounddevice as sd
   import numpy as np
   
   # Play test tone
   sd.play(np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100)), 44100)
   sd.wait()
   ```

### Wake Word Not Detecting

1. **Check microphone**:
   - Ensure microphone is connected and selected
   - Check microphone permissions

2. **Adjust VAD threshold**:
   ```yaml
   # In system_config.yaml
   speech:
     vad_threshold: 0.3  # Lower for more sensitive detection
   ```

3. **Use text fallback**:
   - Wake word can be detected in transcribed text
   - Speak clearly and wait for transcription

### High Latency

1. **Use smaller STT model**:
   ```bash
   STT_MODEL=tiny.en  # or base.en instead of large
   ```

2. **Check CPU usage**:
   - Close other applications
   - Consider GPU acceleration if available

3. **Optimize chunk duration**:
   ```yaml
   speech:
     chunk_duration: 0.05  # Increase for less frequent processing
   ```

## Performance Tips

### CPU Optimization

- Use `tiny.en` or `base.en` models for faster transcription
- Set compute_type to `int8` for lower memory usage
- Reduce VAD processing frequency

### GPU Acceleration

```python
# Use CUDA if available
stt = STTEngine(model_size="base.en", device="cuda")
```

### Memory Management

- Cleanup unused components: `manager.cleanup()`
- Limit audio buffer sizes
- Use streaming transcription for long audio

## Integration with Abby Unleashed

PersonaPlex seamlessly integrates with Abby's existing features:

- **Task Engine**: Voice requests automatically processed by task decomposition
- **Persona Library**: Agents respond using configured personality
- **Brain Clone**: Voice responses reflect personality configuration
- **Ollama**: LLM backend handles all reasoning and responses

## Examples

See `examples/personaplex_demo.py` for a complete working example.

## Credits

PersonaPlex integration inspired by [NVIDIA PersonaPlex](https://github.com/NVIDIA/personaplex).

Built with:
- [faster-whisper](https://github.com/guillaumekln/faster-whisper)
- [piper-tts](https://github.com/rhasspy/piper)
- [silero-vad](https://github.com/snakers4/silero-vad)
- [pvporcupine](https://github.com/Picovoice/porcupine)

## License

MIT License - See LICENSE file for details

---

**Need Help?** Open an issue on [GitHub](https://github.com/Abbystarchild/Abby-Unleashed-Core/issues)
