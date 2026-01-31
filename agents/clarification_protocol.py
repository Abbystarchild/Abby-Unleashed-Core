"""
Clarification Protocol - Ensures agents ask questions instead of making assumptions
"""
from typing import Dict, Any, List, Optional
import logging
from agents.agent_dna import AgentDNA


logger = logging.getLogger(__name__)


class ClarificationProtocol:
    """
    Ensures agents ask questions when information is insufficient.
    For conversational messages, allows them to proceed.
    For complex tasks, may ask clarifying questions.
    """
    
    def __init__(self):
        self.questions: List[str] = []
    
    def check_completeness(self, task: str, context: Dict[str, Any], dna: AgentDNA) -> bool:
        """
        Returns True if sufficient info to proceed.
        Returns False if clarification needed.
        
        For conversational AI, we default to proceeding and let the LLM
        ask questions naturally if needed.
        
        Args:
            task: Task description
            context: Task context
            dna: Agent DNA
            
        Returns:
            True if complete, False if clarification needed
        """
        self.questions = []
        
        # For conversational messages, always proceed - let the LLM handle it naturally
        # The LLM is smart enough to ask follow-up questions if needed
        if self._is_conversational(task):
            logger.info("Conversational message - proceeding without clarification")
            return True
        
        # For very short unclear tasks, might need clarification
        if len(task.strip()) < 5:
            self.questions.append("Could you tell me more about what you'd like me to help with?")
            logger.info("Task too short - requesting clarification")
            return False
        
        # Default: proceed and let the LLM handle naturally
        logger.info("Task information sufficient - proceeding")
        return True
    
    def _is_conversational(self, task: str) -> bool:
        """Check if this is a conversational message vs a complex task"""
        task_lower = task.lower().strip()
        
        # Greetings and simple conversation
        conversational_patterns = [
            "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
            "how are you", "what's up", "sup", "yo", "greetings",
            "thanks", "thank you", "bye", "goodbye", "see you",
            "who are you", "what are you", "what can you do",
            "help", "?",  # Questions are conversational
        ]
        
        # Check if it starts with or contains conversational patterns
        for pattern in conversational_patterns:
            if task_lower.startswith(pattern) or task_lower == pattern:
                return True
        
        # Questions are generally conversational
        if "?" in task:
            return True
            
        # Short messages are usually conversational
        if len(task.split()) <= 10:
            return True
        
        return False
    
    def has_clear_objective(self, task: str) -> bool:
        """Check if task has clear objective"""
        # Simple heuristic - real implementation would use NLP
        if len(task.strip()) < 10:
            return False
        
        # Check for action words
        action_words = ["create", "build", "develop", "design", "implement", 
                       "analyze", "research", "write", "test", "deploy"]
        task_lower = task.lower()
        
        return any(word in task_lower for word in action_words)
    
    def has_constraints(self, context: Dict[str, Any], dna: AgentDNA) -> bool:
        """Check if constraints are defined"""
        # If DNA has constraints, assume they're sufficient
        if dna.constraints and len(dna.constraints) > 0:
            return True
        
        # Check context for constraints
        constraint_keys = ["budget", "timeline", "security", "performance", 
                          "compliance", "resources"]
        
        return any(key in context for key in constraint_keys)
    
    def has_output_requirements(self, context: Dict[str, Any], dna: AgentDNA) -> bool:
        """Check if output format is clear"""
        # If DNA has output format, assume it's sufficient
        if dna.output_format and len(dna.output_format) > 0:
            return True
        
        # Check context for output requirements
        output_keys = ["output_format", "deliverable", "format"]
        
        return any(key in context for key in output_keys)
    
    def has_domain_specifics(self, task: str, context: Dict[str, Any], dna: AgentDNA) -> bool:
        """Check if domain-specific requirements are clear"""
        # Check if task or context mentions domain-specific terms
        if dna.domain.lower() in task.lower():
            return True
        
        # Check context for domain requirements
        if "domain_requirements" in context:
            return True
        
        # If industry knowledge is comprehensive, assume it's okay
        if len(dna.industry_knowledge) >= 3:
            return True
        
        return False
    
    def ask_clarifying_questions(self) -> List[str]:
        """
        Returns list of questions to ask user/parent agent.
        
        Returns:
            List of formatted questions
        """
        formatted = [
            "🤔 Before I proceed, I need to clarify a few things:",
            ""
        ]
        
        for i, q in enumerate(self.questions, 1):
            formatted.append(f"  {i}. {q}")
        
        formatted.append("")
        formatted.append("Once you provide these details, I can get started!")
        
        return formatted
