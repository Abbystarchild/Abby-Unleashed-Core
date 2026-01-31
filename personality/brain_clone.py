"""
Brain Clone - Loads and applies personality configuration

Supports both traditional YAML config and advanced Engram-based personalities.
The Engram system provides a more accurate representation of human personality
based on psychological research (Big Five OCEAN traits, HEXACO model, etc.)
"""
import yaml
import os
import logging
from typing import Dict, Any, Optional

from .engram_builder import EngramBuilder, Engram, create_engram_interactive


logger = logging.getLogger(__name__)


class BrainClone:
    """
    Manages personality configuration for Abby.
    
    Supports two modes:
    1. Traditional YAML config (simple, manual configuration)
    2. Engram-based personality (comprehensive, scientifically-grounded)
    """
    
    def __init__(self, config_path: str = "config/brain_clone.yaml", engram_path: Optional[str] = None):
        """
        Initialize brain clone
        
        Args:
            config_path: Path to traditional personality configuration
            engram_path: Path to engram file (if using advanced personality)
        """
        self.config_path = config_path
        self.engram_path = engram_path
        self.personality: Dict[str, Any] = {}
        self.engram: Optional[Engram] = None
        self.engram_builder = EngramBuilder()
        
        # Load personality (prefer engram if available)
        self.load()
    
    def load(self):
        """Load personality from configuration file or engram"""
        # Try to load engram first if path provided
        if self.engram_path and os.path.exists(self.engram_path):
            try:
                self.engram = self.engram_builder.load_engram(self.engram_path)
                self.personality = self.engram_builder.export_for_brain_clone(self.engram)
                logger.info(f"Loaded engram personality: {self.engram.subject_name}")
                return
            except Exception as e:
                logger.warning(f"Failed to load engram, falling back to YAML: {e}")
        
        # Check for engram embedded in config
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.personality = yaml.safe_load(f)
                
                # Check if config has embedded engram
                if "engram" in self.personality:
                    try:
                        self.engram = Engram.from_dict(self.personality["engram"])
                        logger.info(f"Loaded embedded engram for: {self.engram.subject_name}")
                    except Exception as e:
                        logger.warning(f"Failed to parse embedded engram: {e}")
                
                logger.info(f"Loaded personality: {self.personality.get('identity', {}).get('name', 'Unknown')}")
                return
            
            except Exception as e:
                logger.error(f"Error loading personality: {e}")
        
        logger.warning(f"Personality config not found: {self.config_path}")
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
        Build system prompt from personality.
        
        If an engram is loaded, uses the advanced engram-based prompt.
        Otherwise falls back to traditional YAML-based prompt.
        
        Returns:
            System prompt string
        """
        # Use engram-based prompt if available (more accurate personality modeling)
        if self.engram is not None:
            return self.engram_builder.generate_system_prompt(self.engram)
        
        # Traditional YAML-based prompt
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
    
    def get_engram(self) -> Optional[Engram]:
        """
        Get the loaded engram if available.
        
        Returns:
            Engram object or None
        """
        return self.engram
    
    def has_engram(self) -> bool:
        """Check if an engram is loaded"""
        return self.engram is not None
    
    def create_engram_questionnaire(self) -> str:
        """
        Get the questionnaire for creating a new engram.
        
        Returns:
            Formatted questionnaire string
        """
        return create_engram_interactive(self.personality.get("identity", {}).get("name", "User"))
    
    def save_engram(self, engram: Engram, filepath: Optional[str] = None) -> str:
        """
        Save an engram to file.
        
        Args:
            engram: The engram to save
            filepath: Optional custom filepath
        
        Returns:
            Path where engram was saved
        """
        self.engram_builder.current_engram = engram
        saved_path = self.engram_builder.save_engram(filepath)
        self.engram = engram
        self.personality = self.engram_builder.export_for_brain_clone(engram)
        return saved_path
    
    def analyze_writing(self, text: str) -> Dict[str, Any]:
        """
        Analyze a writing sample to extract linguistic patterns.
        
        Args:
            text: Sample text written by the person
        
        Returns:
            Dictionary of extracted patterns
        """
        patterns = self.engram_builder.analyze_writing_sample(text)
        return {
            "vocabulary_complexity": patterns.vocabulary_complexity,
            "sentence_style": patterns.sentence_length_preference,
            "common_words": patterns.common_words[:10],
            "phrase_patterns": patterns.phrase_patterns[:5],
            "contraction_usage": patterns.contraction_usage,
            "active_voice_tendency": patterns.active_vs_passive
        }
