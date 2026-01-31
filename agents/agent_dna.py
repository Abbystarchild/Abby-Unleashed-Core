"""
Agent DNA Framework - 5-Element System
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid


@dataclass
class AgentDNA:
    """
    5-Element Agent DNA - Required for all agents
    
    Every agent MUST have these 5 elements:
    1. ROLE + SENIORITY
    2. INDUSTRY/DOMAIN CONTEXT
    3. METHODOLOGIES
    4. CONSTRAINTS
    5. OUTPUT FORMAT
    """
    
    # 1. ROLE + SENIORITY
    role: str                           # e.g., "Backend Developer"
    seniority: str                      # Junior, Mid, Senior, Staff, Principal
    
    # 2. INDUSTRY/DOMAIN CONTEXT
    domain: str                         # e.g., "E-commerce payment processing"
    industry_knowledge: List[str]       # Standards, regulations, best practices
    
    # 3. METHODOLOGIES
    methodologies: List[str]            # TDD, DDD, Agile, GitOps, etc.
    
    # 4. CONSTRAINTS
    constraints: Dict[str, Any]         # Security, performance, budget, timeline
    
    # 5. OUTPUT FORMAT
    output_format: Dict[str, str]       # Code style, docs, deliverables
    
    # Metadata
    persona_id: str = field(default_factory=lambda: f"persona-{uuid.uuid4().hex[:12]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    times_used: int = 0
    success_rate: Optional[float] = None
    last_improved: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DNA to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentDNA':
        """Create DNA from dictionary"""
        return cls(**data)
    
    def validate(self) -> bool:
        """Validate that all 5 elements are properly defined"""
        if not self.role or not self.seniority:
            raise ValueError("Missing role/seniority (Element 1)")
        
        if not self.domain or not self.industry_knowledge:
            raise ValueError("Missing domain context (Element 2)")
        
        if not self.methodologies:
            raise ValueError("Missing methodologies (Element 3)")
        
        if not self.constraints:
            raise ValueError("Missing constraints (Element 4)")
        
        if not self.output_format:
            raise ValueError("Missing output format (Element 5)")
        
        return True
    
    def __str__(self) -> str:
        """String representation"""
        return f"{self.seniority} {self.role} ({self.domain})"
