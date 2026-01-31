"""
Base Agent class for all agents in the system
"""
from typing import Dict, Any, Optional, List
import logging
from agents.agent_dna import AgentDNA


logger = logging.getLogger(__name__)


class Agent:
    """
    Base Agent class that all specialized agents inherit from
    """
    
    def __init__(self, dna: AgentDNA, personality: Optional[Dict[str, Any]] = None):
        """
        Initialize agent with DNA and personality
        
        Args:
            dna: AgentDNA with 5 required elements
            personality: Brain clone personality configuration
        """
        # Validate DNA
        dna.validate()
        
        self.dna = dna
        self.personality = personality or {}
        self.task_history: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized agent: {self.dna}")
    
    def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task with the given context
        
        Args:
            task: Task description
            context: Additional context for task execution
            
        Returns:
            Result dictionary with status and output
        """
        from agents.clarification_protocol import ClarificationProtocol
        
        # Check if we have enough information
        protocol = ClarificationProtocol()
        
        if not protocol.check_completeness(task, context, self.dna):
            # Need clarification - ASK QUESTIONS
            questions = protocol.ask_clarifying_questions()
            logger.info(f"Agent {self.dna.role} needs clarification")
            return {
                "status": "clarification_needed",
                "questions": questions,
                "agent": str(self.dna)
            }
        
        # Sufficient info - PROCEED
        logger.info(f"Agent {self.dna.role} executing task: {task[:50]}...")
        result = self.perform_task(task, context)
        
        # Track task history
        self.task_history.append({
            "task": task,
            "context": context,
            "result": result
        })
        
        return result
    
    def perform_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actual task execution - to be implemented by subclasses or used generically
        
        Args:
            task: Task description
            context: Task context
            
        Returns:
            Result dictionary
        """
        # This is a placeholder - real implementation would use LLM
        return {
            "status": "completed",
            "output": f"Task executed by {self.dna.role}",
            "agent": str(self.dna)
        }
    
    def get_system_prompt(self) -> str:
        """
        Build system prompt from DNA and personality
        
        Returns:
            Complete system prompt for the agent
        """
        prompt_parts = [
            f"You are a {self.dna.seniority} {self.dna.role}.",
            f"Domain: {self.dna.domain}",
            f"\nIndustry Knowledge: {', '.join(self.dna.industry_knowledge)}",
            f"\nMethodologies: {', '.join(self.dna.methodologies)}",
            f"\nConstraints: {self._format_constraints()}",
            f"\nOutput Format: {self._format_output_format()}",
        ]
        
        # Add personality traits if available
        if self.personality:
            if "communication_style" in self.personality:
                style = self.personality["communication_style"]
                prompt_parts.append(f"\nCommunication Style: {style.get('tone', '')}")
        
        return "\n".join(prompt_parts)
    
    def _format_constraints(self) -> str:
        """Format constraints for prompt"""
        return ", ".join([f"{k}: {v}" for k, v in self.dna.constraints.items()])
    
    def _format_output_format(self) -> str:
        """Format output format for prompt"""
        return ", ".join([f"{k}: {v}" for k, v in self.dna.output_format.items()])
