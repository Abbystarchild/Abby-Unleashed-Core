"""
Agent Factory - Creates agents with 5-element DNA
Always checks persona library FIRST before creating new
"""
import logging
from typing import Dict, Any, Optional
from agents.agent_dna import AgentDNA
from agents.base_agent import Agent


logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Creates agents with 5-element DNA.
    Always checks persona library FIRST before creating new.
    """
    
    def __init__(self, persona_library=None, personality: Optional[Dict[str, Any]] = None):
        """
        Initialize factory
        
        Args:
            persona_library: PersonaLibrary instance
            personality: Brain clone personality
        """
        self.persona_library = persona_library
        self.personality = personality or {}
    
    def create_agent(self, task: str, context: Dict[str, Any]) -> Agent:
        """
        Create an agent for the given task
        
        Args:
            task: Task description
            context: Task context
            
        Returns:
            Agent instance
        """
        # 1. Analyze task requirements
        requirements = self.analyze_task(task, context)
        
        # 2. Check if persona exists in library
        existing_persona = None
        if self.persona_library:
            existing_persona = self.persona_library.find_match(requirements)
        
        if existing_persona:
            # Use existing persona
            agent = self.instantiate_from_persona(existing_persona, context)
            logger.info(f"Using existing persona: {existing_persona.role}")
        else:
            # Generate new persona DNA
            dna = self.generate_agent_dna(requirements)
            
            # Validate all 5 elements present
            self.validate_dna(dna)
            
            # Create agent
            agent = Agent(dna=dna, personality=self.personality)
            
            # Save to library for future use
            if self.persona_library:
                self.persona_library.save(dna)
            
            logger.info(f"Created new persona: {dna.role}")
        
        return agent
    
    def analyze_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze task to determine requirements
        
        Args:
            task: Task description
            context: Task context
            
        Returns:
            Requirements dictionary
        """
        # Simple analysis - real implementation would use LLM
        requirements = {
            "task": task,
            "context": context,
            "role": self._extract_role(task),
            "domain": context.get("domain", "General"),
            "seniority": context.get("seniority", "Senior"),
        }
        
        return requirements
    
    def _extract_role(self, task: str) -> str:
        """Extract role from task description"""
        task_lower = task.lower()
        
        # Simple keyword matching - real implementation would use LLM
        if "code" in task_lower or "develop" in task_lower or "program" in task_lower:
            return "Software Developer"
        elif "design" in task_lower and "system" in task_lower:
            return "System Architect"
        elif "data" in task_lower and "analyze" in task_lower:
            return "Data Analyst"
        elif "devops" in task_lower or "deploy" in task_lower:
            return "DevOps Engineer"
        elif "test" in task_lower:
            return "QA Engineer"
        else:
            return "General Agent"
    
    def generate_agent_dna(self, requirements: Dict[str, Any]) -> AgentDNA:
        """
        Generate new agent DNA from requirements
        
        Args:
            requirements: Requirements dictionary
            
        Returns:
            AgentDNA instance
        """
        # Extract or generate DNA elements
        role = requirements.get("role", "General Agent")
        domain = requirements.get("domain", "General")
        seniority = requirements.get("seniority", "Senior")
        
        # Generate DNA with sensible defaults
        dna = AgentDNA(
            role=role,
            seniority=seniority,
            domain=domain,
            industry_knowledge=[
                f"{domain} best practices",
                "Industry standards",
                "Quality assurance"
            ],
            methodologies=[
                "Agile development",
                "Iterative improvement",
                "Continuous learning"
            ],
            constraints={
                "quality": "High quality required",
                "timeline": "Reasonable timeline",
                "resources": "Standard resources"
            },
            output_format={
                "documentation": "Clear documentation",
                "code": "Well-structured and commented",
                "deliverable": "Production-ready"
            }
        )
        
        return dna
    
    def instantiate_from_persona(self, dna: AgentDNA, context: Dict[str, Any]) -> Agent:
        """
        Create agent from existing persona
        
        Args:
            dna: Existing AgentDNA
            context: Task context
            
        Returns:
            Agent instance
        """
        # Increment usage counter
        dna.times_used += 1
        
        # Create agent
        agent = Agent(dna=dna, personality=self.personality)
        
        return agent
    
    def validate_dna(self, dna: AgentDNA):
        """
        Ensure all 5 DNA elements are properly defined
        
        Args:
            dna: AgentDNA to validate
            
        Raises:
            ValueError: If DNA is invalid
        """
        dna.validate()
