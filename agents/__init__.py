"""
Agents package - Core agent system with DNA framework

Agents are intelligent entities that:
1. Have a DNA defining their role, domain, and capabilities
2. ACQUIRE real expertise through internet research
3. Use acquired knowledge to perform tasks accurately
4. Can do additional research during task execution
"""
from agents.agent_dna import AgentDNA
from agents.base_agent import Agent
from agents.clarification_protocol import ClarificationProtocol
from agents.research_toolkit import ResearchToolkit, get_research_toolkit, KnowledgeAcquisition

__all__ = [
    'AgentDNA', 
    'Agent', 
    'ClarificationProtocol',
    'ResearchToolkit',
    'get_research_toolkit',
    'KnowledgeAcquisition'
]
