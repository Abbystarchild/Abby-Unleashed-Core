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
        
        # Track current task progress
        self.current_task = None
        self.task_progress = {}
        
        # Conversation history for chat context
        self.conversation_history = []
        
        logger.info("Abby Unleashed initialized successfully!")
    
    def execute_task(
        self, 
        task: str, 
        context: Optional[Dict[str, Any]] = None,
        use_orchestrator: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a task or respond to user input conversationally
        
        Args:
            task: Task description or user message
            context: Optional task context
            use_orchestrator: Whether to use the orchestrator for complex tasks
            
        Returns:
            Result dictionary with response
        """
        context = context or {}
        
        logger.info(f"Processing: {task[:100]}...")
        
        # Track progress
        self.current_task = task
        self.task_progress = {
            "task": task,
            "status": "in_progress",
            "steps_completed": 0,
            "total_steps": 1
        }
        
        try:
            # Get model to use
            model = os.getenv("DEFAULT_MODEL", "qwen2.5:latest")
            
            # Build system prompt with personality
            personality = self.brain_clone.get_personality()
            identity = personality.get("identity", {})
            comm_style = personality.get("communication_style", {})
            
            system_prompt = f"""You are {identity.get('name', 'Abby')}, {identity.get('role', 'an AI assistant')}.

Your personality:
- Tone: {comm_style.get('tone', 'friendly and professional')}
- Style: {comm_style.get('style', 'conversational')}
- You are helpful, knowledgeable, and engaging

Instructions:
- Respond naturally to the user's message
- If asked to perform a task, help them with it
- If you need more information to help properly, ask clarifying questions
- Be conversational and personable, not robotic
- Keep responses concise but helpful

Remember: You are having a conversation, not just executing commands."""

            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": task
            })
            
            # Keep conversation history manageable (last 10 exchanges)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # Call Ollama for response
            response = self.ollama_client.chat(
                messages=[{"role": "system", "content": system_prompt}] + self.conversation_history,
                model=model
            )
            
            # Extract response text
            if "error" in response:
                logger.error(f"Ollama error: {response['error']}")
                return {
                    "status": "error",
                    "error": response["error"],
                    "output": f"Sorry, I encountered an error: {response['error']}"
                }
            
            # Get assistant response
            assistant_message = response.get("message", {}).get("content", "")
            
            if not assistant_message:
                assistant_message = response.get("response", "I'm not sure how to respond to that.")
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant", 
                "content": assistant_message
            })
            
            # Update progress
            self.task_progress["status"] = "completed"
            self.task_progress["steps_completed"] = 1
            
            logger.info("Response generated successfully")
            return {
                "status": "completed",
                "output": assistant_message,
                "model": model
            }
        
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            self.task_progress["status"] = "error"
            self.task_progress["error"] = str(e)
            return {
                "status": "error",
                "error": str(e),
                "output": f"Sorry, something went wrong: {str(e)}"
            }
    
    def get_orchestrator_progress(self) -> Dict[str, Any]:
        """
        Get current task/orchestrator progress
        
        Returns:
            Progress dictionary with task status
        """
        if not self.current_task:
            return {
                "status": "idle",
                "message": "No task currently in progress"
            }
        
        return self.task_progress
    
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
        """Start voice interface - placeholder for now"""
        from rich.console import Console
        console = Console()
        
        console.print("[yellow]Voice interface not yet implemented.[/yellow]")
        console.print("[dim]Falling back to text interface...[/dim]\n")
        
        self.start_text_interface()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get system statistics
        
        Returns:
            Statistics dictionary
        """
        return {
            "persona_library": self.persona_library.get_stats(),
            "ollama_models": self.model_selector.get_available_models()
        }


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
