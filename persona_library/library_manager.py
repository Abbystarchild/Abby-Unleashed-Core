"""
Persona Library Manager - CRUD operations for persona library
"""
import yaml
import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from agents.agent_dna import AgentDNA


logger = logging.getLogger(__name__)


class PersonaLibrary:
    """
    Manages persistent storage and retrieval of agent personas
    """
    
    def __init__(self, library_path: str = "persona_library/personas/personas.yaml"):
        """
        Initialize persona library
        
        Args:
            library_path: Path to personas YAML file
        """
        self.library_path = library_path
        self.personas: Dict[str, AgentDNA] = {}
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(library_path), exist_ok=True)
        
        # Load existing personas
        self.load()
    
    def load(self):
        """Load personas from file"""
        if not os.path.exists(self.library_path):
            logger.info(f"No existing persona library at {self.library_path}")
            self.personas = {}
            return
        
        try:
            with open(self.library_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if data and 'personas' in data:
                for persona_data in data['personas']:
                    dna = AgentDNA.from_dict(persona_data)
                    self.personas[dna.persona_id] = dna
            
            logger.info(f"Loaded {len(self.personas)} personas from library")
        
        except Exception as e:
            logger.error(f"Error loading persona library: {e}")
            self.personas = {}
    
    def save(self, dna: AgentDNA):
        """
        Save a persona to the library
        
        Args:
            dna: AgentDNA to save
        """
        # Add to in-memory library
        self.personas[dna.persona_id] = dna
        
        # Persist to file
        self._persist()
        
        logger.info(f"Saved persona {dna.persona_id}: {dna.role}")
    
    def _persist(self):
        """Persist library to file"""
        try:
            data = {
                'personas': [dna.to_dict() for dna in self.personas.values()]
            }
            
            with open(self.library_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            
            logger.debug(f"Persisted {len(self.personas)} personas to {self.library_path}")
        
        except Exception as e:
            logger.error(f"Error persisting persona library: {e}")
    
    def find_match(self, requirements: Dict[str, Any]) -> Optional[AgentDNA]:
        """
        Find existing persona that matches requirements
        
        Args:
            requirements: Task requirements
            
        Returns:
            Matching AgentDNA or None
        """
        target_role = requirements.get("role", "").lower()
        target_domain = requirements.get("domain", "").lower()
        
        # Look for exact or close matches
        for dna in self.personas.values():
            if dna.role.lower() == target_role and dna.domain.lower() == target_domain:
                logger.info(f"Found exact match: {dna.persona_id}")
                return dna
        
        # Look for role match
        for dna in self.personas.values():
            if dna.role.lower() == target_role:
                logger.info(f"Found role match: {dna.persona_id}")
                return dna
        
        logger.info("No matching persona found in library")
        return None
    
    def get(self, persona_id: str) -> Optional[AgentDNA]:
        """
        Get persona by ID
        
        Args:
            persona_id: Persona ID
            
        Returns:
            AgentDNA or None
        """
        return self.personas.get(persona_id)
    
    def list_all(self) -> List[AgentDNA]:
        """
        Get all personas
        
        Returns:
            List of all personas
        """
        return list(self.personas.values())
    
    def delete(self, persona_id: str):
        """
        Delete a persona
        
        Args:
            persona_id: Persona ID to delete
        """
        if persona_id in self.personas:
            del self.personas[persona_id]
            self._persist()
            logger.info(f"Deleted persona {persona_id}")
    
    def update(self, dna: AgentDNA):
        """
        Update an existing persona
        
        Args:
            dna: Updated AgentDNA
        """
        if dna.persona_id in self.personas:
            self.personas[dna.persona_id] = dna
            self._persist()
            logger.info(f"Updated persona {dna.persona_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get library statistics
        
        Returns:
            Statistics dictionary
        """
        if not self.personas:
            return {
                "total_personas": 0,
                "roles": [],
                "domains": []
            }
        
        roles = list(set(dna.role for dna in self.personas.values()))
        domains = list(set(dna.domain for dna in self.personas.values()))
        
        return {
            "total_personas": len(self.personas),
            "roles": sorted(roles),
            "domains": sorted(domains),
            "most_used": self._get_most_used()
        }
    
    def _get_most_used(self) -> Optional[Dict[str, Any]]:
        """Get most used persona"""
        if not self.personas:
            return None
        
        most_used = max(self.personas.values(), key=lambda x: x.times_used)
        
        return {
            "persona_id": most_used.persona_id,
            "role": most_used.role,
            "times_used": most_used.times_used
        }
