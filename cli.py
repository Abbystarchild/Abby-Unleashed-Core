"""
Main Abby Unleashed Orchestrator
"""
import logging
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from personality.brain_clone import BrainClone
from persona_library.library_manager import PersonaLibrary
from agents.agent_factory import AgentFactory
from ollama_integration.client import OllamaClient
from ollama_integration.model_selector import ModelSelector
from coordination.orchestrator import Orchestrator
from config.validators import validate_task_input, validate_ollama_config, EnvironmentConfig


# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AbbyUnleashed:
    """
    Main orchestrator for Abby Unleashed digital clone system
    """
    
    def __init__(
        self,
        personality_config: str = "config/brain_clone.yaml",
        persona_library_path: str = "persona_library/personas/personas.yaml",
        verbose: bool = False
    ):
        """
        Initialize Abby Unleashed
        
        Args:
            personality_config: Path to personality configuration
            persona_library_path: Path to persona library
            verbose: Enable verbose logging
        """
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        logger.info("Initializing Abby Unleashed...")
        
        # Validate environment configuration
        try:
            env_config = EnvironmentConfig.from_env()
            logger.debug(f"Loaded environment configuration: {env_config.model_dump()}")
        except Exception as e:
            logger.error(f"Invalid environment configuration: {e}")
            raise
        
        # Load brain clone (personality)
        self.brain_clone = BrainClone(personality_config)
        logger.info(f"Loaded personality: {self.brain_clone.personality.get('identity', {}).get('name')}")
        
        # Initialize persona library
        self.persona_library = PersonaLibrary(persona_library_path)
        logger.info(f"Loaded {len(self.persona_library.personas)} personas")
        
        # Initialize Ollama client
        self.ollama_client = OllamaClient()
        
        # Initialize model selector
        self.model_selector = ModelSelector(ollama_client=self.ollama_client)
        
        # Initialize agent factory
        self.agent_factory = AgentFactory(
            persona_library=self.persona_library,
            personality=self.brain_clone.get_personality()
        )
        
        # Initialize orchestrator (Phase 3)
        self.orchestrator = Orchestrator(agent_factory=self.agent_factory)
        self.orchestrator.start()
        
        logger.info("Abby Unleashed initialized successfully!")
    
    def execute_task(self, task: str, context: Optional[Dict[str, Any]] = None, use_orchestrator: bool = True) -> Dict[str, Any]:
        """
        Execute a task
        
        Args:
            task: Task description
            context: Optional task context
            use_orchestrator: Use orchestrator for complex tasks (Phase 3)
            
        Returns:
            Result dictionary
        """
        context = context or {}
        
        logger.info(f"Executing task: {task[:100]}...")
        
        # Validate task input
        try:
            validated_input = validate_task_input(task, context)
            task = validated_input.description
            context = validated_input.context or {}
        except ValueError as e:
            logger.error(f"Invalid task input: {e}")
            return {
                "status": "error",
                "error": f"Invalid task input: {str(e)}"
            }
        
        try:
            # Use orchestrator for complex tasks (Phase 3)
            if use_orchestrator:
                return self.orchestrator.execute_task(task, context)
            
            # Legacy single-agent execution (Phase 1)
            # Create agent for task
            agent = self.agent_factory.create_agent(task, context)
            
            # Get appropriate model
            model = self.model_selector.select_model(
                agent_role=agent.dna.role,
                task_type=task
            )
            
            # Execute task with agent
            result = agent.execute_task(task, context)
            
            # If clarification needed, return questions
            if result.get("status") == "clarification_needed":
                return result
            
            # Task completed
            logger.info(f"Task completed by {agent.dna.role}")
            return result
        
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def start_text_interface(self):
        """Start interactive text interface"""
        from rich.console import Console
        from rich.markdown import Markdown
        
        console = Console()
        
        console.print(f"\n[bold green]{self.brain_clone.get_greeting()}[/bold green]\n")
        console.print("[dim]Type 'exit' to quit[/dim]\n")
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    console.print(f"\n[bold green]{self.brain_clone.get_completed()} Goodbye![/bold green]\n")
                    break
                
                # Process task
                console.print(f"\n[bold blue]{self.brain_clone.get_task_received()}[/bold blue]\n")
                
                result = self.execute_task(user_input)
                
                # Display result
                if result.get("status") == "clarification_needed":
                    console.print("[yellow]" + "\n".join(result["questions"]) + "[/yellow]\n")
                elif result.get("status") == "error":
                    console.print(f"[red]Error: {result.get('error')}[/red]\n")
                else:
                    console.print(f"[green]{result.get('output', 'Task completed!')}[/green]\n")
            
            except KeyboardInterrupt:
                console.print(f"\n\n[bold green]{self.brain_clone.get_completed()} Goodbye![/bold green]\n")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]\n")
    
    def start_voice_interface(self):
        """Start PersonaPlex-inspired voice interface"""
        from rich.console import Console
        from speech_interface import ConversationManager
        import os
        
        console = Console()
        
        console.print(f"\n[bold green]🎙️  {self.brain_clone.get_greeting()}[/bold green]")
        console.print("[bold cyan]PersonaPlex Voice Mode Activated[/bold cyan]\n")
        
        try:
            # Get configuration
            stt_model = os.getenv("STT_MODEL", "base.en")
            tts_voice = os.getenv("TTS_VOICE", "en_US-amy-medium")
            wake_word = os.getenv("WAKE_WORD", "hey abby")
            wake_word_key = os.getenv("PORCUPINE_ACCESS_KEY", None)
            
            # Initialize conversation manager
            console.print("[dim]Initializing speech components...[/dim]")
            conversation_manager = ConversationManager(
                stt_model=stt_model,
                tts_voice=tts_voice,
                wake_word=wake_word,
                wake_word_key=wake_word_key
            )
            
            # Initialize components
            if not conversation_manager.initialize():
                console.print("[yellow]Some speech components unavailable.[/yellow]")
                console.print("[yellow]Falling back to text interface...[/yellow]\n")
                self.start_text_interface()
                return
            
            # Set task executor
            def task_executor(text: str) -> str:
                result = self.execute_task(text)
                if result.get("status") == "clarification_needed":
                    return "\n".join(result["questions"])
                elif result.get("status") == "error":
                    return f"Error: {result.get('error')}"
                else:
                    return result.get('output', 'Task completed!')
            
            conversation_manager.set_task_executor(task_executor)
            
            # Start listening
            console.print(f"[green]✓[/green] Speech components initialized")
            console.print(f"[dim]Wake word: '{wake_word}'[/dim]")
            console.print("[dim]Press Ctrl+C to exit[/dim]\n")
            
            if conversation_manager.start_listening():
                console.print("[bold green]🎧 Listening...[/bold green]\n")
                
                # Keep running
                try:
                    import time
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            
            # Cleanup
            conversation_manager.cleanup()
            console.print(f"\n[bold green]{self.brain_clone.get_completed()} Goodbye![/bold green]\n")
        
        except Exception as e:
            console.print(f"[red]Voice interface error: {e}[/red]")
            console.print("[yellow]Falling back to text interface...[/yellow]\n")
            self.start_text_interface()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get system statistics
        
        Returns:
            Statistics dictionary
        """
        return {
            "persona_library": self.persona_library.get_stats(),
            "ollama_models": self.model_selector.get_available_models(),
            "orchestrator": self.orchestrator.get_progress()
        }
    
    def get_orchestrator_progress(self) -> Dict[str, Any]:
        """
        Get orchestrator progress
        
        Returns:
            Progress dictionary
        """
        return self.orchestrator.get_progress()
    
    def cleanup(self):
        """Cleanup resources"""
        self.orchestrator.stop()
        self.orchestrator.cleanup()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Abby Unleashed - Digital Clone System")
    parser.add_argument(
        "mode",
        nargs='?',
        choices=["voice", "text", "task"],
        default="text",
        help="Interface mode"
    )
    parser.add_argument(
        "--personality",
        default="config/brain_clone.yaml",
        help="Path to personality configuration"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--task",
        help="Direct task execution (for 'task' mode)"
    )
    
    args = parser.parse_args()
    
    # Initialize Abby
    abby = AbbyUnleashed(
        personality_config=args.personality,
        verbose=args.verbose
    )
    
    # Run appropriate interface
    if args.mode == "voice":
        abby.start_voice_interface()
    elif args.mode == "text":
        abby.start_text_interface()
    else:  # task mode
        if args.task:
            result = abby.execute_task(args.task)
            print(result)
        else:
            print("Error: --task argument required for task mode")


if __name__ == "__main__":
    main()
