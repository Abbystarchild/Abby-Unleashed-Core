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
    CRITICAL: Agents MUST ask clarifying questions instead of making assumptions.
    """
    
    def __init__(self):
        self.questions: List[str] = []
    
    def check_completeness(self, task: str, context: Dict[str, Any], dna: AgentDNA) -> bool:
        """
        Returns True if sufficient info to proceed.
        Returns False if clarification needed.
        
        Args:
            task: Task description
            context: Task context
            dna: Agent DNA
            
        Returns:
            True if complete, False if clarification needed
        """
        self.questions = []
        
        # Check for missing requirements
        if not self.has_clear_objective(task):
            self.questions.append("What is the specific goal/outcome?")
        
        if not self.has_constraints(context, dna):
            self.questions.append("Are there any constraints (budget, time, security)?")
        
        if not self.has_output_requirements(context, dna):
            self.questions.append("What format should the deliverable be in?")
        
        if not self.has_domain_specifics(task, context, dna):
            self.questions.append(f"Any specific {dna.domain} requirements I should know?")
        
        # If we have questions, clarification is needed
        if self.questions:
            logger.info(f"Clarification needed: {len(self.questions)} questions")
            return False
        
        logger.info("Task information is complete")
        return True
    
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
