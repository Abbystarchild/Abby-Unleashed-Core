"""
PersonaPlex Speech Interface Demo
Demonstrates the integrated speech-to-speech capabilities
"""
import os
import sys
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from speech_interface import ConversationManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def simple_task_executor(text: str) -> str:
    """
    Simple task executor for demo
    
    Args:
        text: User input
        
    Returns:
        Response text
    """
    # Echo back the input with a friendly response
    return f"I heard you say: '{text}'. This is a demo response!"


def main():
    """Run PersonaPlex demo"""
    print("=" * 60)
    print("PersonaPlex Speech Interface Demo")
    print("=" * 60)
    print()
    
    # Configuration
    stt_model = os.getenv("STT_MODEL", "base.en")
    tts_voice = os.getenv("TTS_VOICE", "en_US-amy-medium")
    wake_word = os.getenv("WAKE_WORD", "hey abby")
    wake_word_key = os.getenv("PORCUPINE_ACCESS_KEY", None)
    
    print(f"STT Model: {stt_model}")
    print(f"TTS Voice: {tts_voice}")
    print(f"Wake Word: {wake_word}")
    print()
    
    # Initialize conversation manager
    print("Initializing speech components...")
    conversation_manager = ConversationManager(
        stt_model=stt_model,
        tts_voice=tts_voice,
        wake_word=wake_word,
        wake_word_key=wake_word_key
    )
    
    # Initialize components
    if not conversation_manager.initialize():
        print("ERROR: Failed to initialize speech components")
        print("Make sure you have the required models installed:")
        print("  - faster-whisper")
        print("  - piper-tts")
        print("  - silero-vad")
        return
    
    print("✓ Speech components initialized successfully")
    print()
    
    # Set task executor
    conversation_manager.set_task_executor(simple_task_executor)
    
    # Demo 1: Text processing (without speech)
    print("Demo 1: Text Processing")
    print("-" * 60)
    test_input = "Hello, how are you?"
    print(f"Input: {test_input}")
    response = conversation_manager.process_text(test_input)
    print(f"Response: {response}")
    print()
    
    # Demo 2: TTS synthesis
    print("Demo 2: Text-to-Speech Synthesis")
    print("-" * 60)
    test_speech = "Welcome to PersonaPlex, integrated with Abby Unleashed!"
    print(f"Speaking: {test_speech}")
    conversation_manager.speak(test_speech)
    print("✓ Speech synthesis completed")
    print()
    
    # Demo 3: Full voice interface (if audio available)
    print("Demo 3: Full Voice Interface")
    print("-" * 60)
    print(f"Say '{wake_word}' to activate listening")
    print("Press Ctrl+C to exit")
    print()
    
    try:
        if conversation_manager.start_listening():
            print("🎧 Listening for wake word...")
            print()
            
            import time
            while True:
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    except Exception as e:
        print(f"\nERROR: {e}")
    
    finally:
        # Cleanup
        conversation_manager.cleanup()
        print("✓ Cleanup completed")
        print()
        print("Demo finished!")


if __name__ == "__main__":
    main()
