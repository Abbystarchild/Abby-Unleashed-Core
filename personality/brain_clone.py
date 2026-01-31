"""
Brain Clone - Loads and applies personality configuration
"""
import yaml
import os
import logging
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class BrainClone:
    """
    Manages personality configuration for Abby
    """
    
    def __init__(self, config_path: str = "config/brain_clone.yaml"):
        """
        Initialize brain clone
        
        Args:
            config_path: Path to personality configuration
        """
        self.config_path = config_path
        self.personality: Dict[str, Any] = {}
        
        # Load personality
        self.load()
    
    def load(self):
        """Load personality from configuration file"""
        if not os.path.exists(self.config_path):
            logger.warning(f"Personality config not found: {self.config_path}")
            self._use_defaults()
            return
        
        try:
            with open(self.config_path, 'r') as f:
                self.personality = yaml.safe_load(f)
            
            logger.info(f"Loaded personality: {self.personality.get('identity', {}).get('name', 'Unknown')}")
        
        except Exception as e:
            logger.error(f"Error loading personality: {e}")
            self._use_defaults()
    
    def _use_defaults(self):
        """Use default personality"""
        self.personality = {
            "identity": {
                "name": "Abby",
                "role": "Digital Assistant",
                "voice_description": "Friendly and helpful"
            },
            "communication_style": {
                "tone": "professional",
                "verbosity": "concise",
                "clarification_behavior": "always ask when uncertain"
            }
        }
    
    def get_greeting(self) -> str:
        """
        Get greeting message
        
        Returns:
            Greeting string
        """
        patterns = self.personality.get("conversation_patterns", {})
        return patterns.get("greeting", "Hello! How can I help you?")
    
    def get_task_received(self) -> str:
        """Get task received acknowledgment"""
        patterns = self.personality.get("conversation_patterns", {})
        return patterns.get("task_received", "Got it! Let me work on that...")
    
    def get_clarification_needed(self) -> str:
        """Get clarification needed message"""
        patterns = self.personality.get("conversation_patterns", {})
        return patterns.get("clarification_needed", "Before I proceed, I need to know...")
    
    def get_working(self) -> str:
        """Get working message"""
        patterns = self.personality.get("conversation_patterns", {})
        return patterns.get("working", "I'm working on this...")
    
    def get_completed(self) -> str:
        """Get completion message"""
        patterns = self.personality.get("conversation_patterns", {})
        return patterns.get("completed", "Done!")
    
    def get_error_handling(self) -> str:
        """Get error handling message"""
        patterns = self.personality.get("conversation_patterns", {})
        return patterns.get("error_handling", "I encountered an issue...")
    
    def get_system_prompt(self) -> str:
        """
        Build system prompt from personality
        
        Returns:
            System prompt string
        """
        identity = self.personality.get("identity", {})
        comm_style = self.personality.get("communication_style", {})
        decision_making = self.personality.get("decision_making", {})
        values = self.personality.get("values", {})
        
        prompt_parts = [
            f"You are {identity.get('name', 'Abby')}, a {identity.get('role', 'digital assistant')}.",
            "",
            "Communication Style:",
        ]
        
        if comm_style:
            prompt_parts.append(f"- Tone: {comm_style.get('tone', 'professional')}")
            prompt_parts.append(f"- Verbosity: {comm_style.get('verbosity', 'concise')}")
            prompt_parts.append(f"- {comm_style.get('clarification_behavior', 'Ask when uncertain')}")
        
        if decision_making:
            prompt_parts.extend([
                "",
                "Decision Making:",
                f"- {decision_making.get('when_stuck', 'Research and ask questions')}",
                f"- {decision_making.get('prioritization', 'Impact-first approach')}"
            ])
        
        if values and "top_priorities" in values:
            prompt_parts.extend([
                "",
                "Top Priorities:",
            ])
            for priority in values["top_priorities"]:
                prompt_parts.append(f"- {priority}")
        
        return "\n".join(prompt_parts)
    
    def get_personality(self) -> Dict[str, Any]:
        """
        Get full personality dictionary
        
        Returns:
            Personality configuration
        """
        return self.personality
