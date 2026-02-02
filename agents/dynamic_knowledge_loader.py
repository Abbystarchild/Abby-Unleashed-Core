"""
Dynamic Knowledge Loader - On-demand skill loading for agents
Enables cross-disciplinary mastery while keeping memory usage low
"""
import os
import sys
import yaml
import logging
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeModule:
    """A loadable knowledge module"""
    name: str
    filename: str
    categories: List[str]
    loaded: bool = False
    content: Dict[str, Any] = field(default_factory=dict)
    memory_estimate_kb: int = 0


class DynamicKnowledgeLoader:
    """
    Loads knowledge on-demand to minimize memory usage
    while allowing cross-disciplinary access
    """
    
    # Mapping of agent roles to their primary knowledge domains
    ROLE_KNOWLEDGE_MAP = {
        "backend": ["backend_mastery", "api_design_mastery", "database_mastery", "python_mastery"],
        "frontend": ["frontend_mastery", "javascript_typescript_mastery", "performance_mastery"],
        "security": ["security_mastery", "security_practices", "hacking_penetration_testing_mastery"],
        "data": ["data_engineering_mastery", "database_mastery", "python_mastery"],
        "ml": ["ml_engineering_mastery", "python_mastery", "data_engineering_mastery"],
        "qa": ["qa_mastery", "testing_mastery", "python_mastery"],
        "dba": ["postgresql_mastery", "database_mastery", "performance_mastery"],
        "sre": ["sre_mastery", "devops_mastery", "performance_mastery"],
        "ios": ["ios_mastery", "kotlin_mastery"],
        "devops": ["devops_mastery", "docker_mastery", "sre_mastery"],
        "writer": ["technical_writing_mastery"],
        "reviewer": ["code_review_mastery", "python_mastery", "general_programming"],
        "debugger": ["debugging_mastery", "python_mastery", "performance_mastery"],
        "architect": ["api_design_mastery", "database_mastery", "performance_mastery", "security_mastery"],
    }
    
    # Knowledge that's always available (core foundations)
    CORE_KNOWLEDGE = ["coding_foundations", "general_programming", "error_handling_mastery"]
    
    # Cross-domain triggers - when these topics are mentioned, load related knowledge
    TOPIC_TRIGGERS = {
        "security": ["security_mastery", "security_practices"],
        "authentication": ["security_mastery", "api_design_mastery"],
        "database": ["database_mastery", "postgresql_mastery"],
        "sql": ["database_mastery", "postgresql_mastery"],
        "api": ["api_design_mastery", "backend_mastery"],
        "rest": ["api_design_mastery", "backend_mastery"],
        "testing": ["testing_mastery", "qa_mastery"],
        "test": ["testing_mastery", "qa_mastery"],
        "performance": ["performance_mastery", "database_mastery"],
        "docker": ["docker_mastery", "devops_mastery"],
        "kubernetes": ["devops_mastery", "sre_mastery"],
        "ci/cd": ["devops_mastery"],
        "git": ["git_mastery"],
        "react": ["frontend_mastery", "javascript_typescript_mastery"],
        "typescript": ["javascript_typescript_mastery", "frontend_mastery"],
        "python": ["python_mastery"],
        "machine learning": ["ml_engineering_mastery"],
        "ml": ["ml_engineering_mastery"],
        "data pipeline": ["data_engineering_mastery"],
        "etl": ["data_engineering_mastery"],
    }
    
    def __init__(self, knowledge_dir: str = None):
        """
        Initialize dynamic knowledge loader
        
        Args:
            knowledge_dir: Path to knowledge directory
        """
        if knowledge_dir is None:
            knowledge_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "agents", "knowledge"
            )
        
        self.knowledge_dir = Path(knowledge_dir)
        self.modules: Dict[str, KnowledgeModule] = {}
        self._loaded_modules: Set[str] = set()
        self._index_available_modules()
    
    def _index_available_modules(self):
        """Index all available knowledge modules without loading them"""
        for filepath in self.knowledge_dir.glob("*.yaml"):
            name = filepath.stem
            if name.startswith('_'):
                continue
            
            # Estimate memory from file size (rough approximation)
            size_kb = filepath.stat().st_size // 1024
            
            # Extract categories from filename
            categories = self._infer_categories(name)
            
            self.modules[name] = KnowledgeModule(
                name=name,
                filename=filepath.name,
                categories=categories,
                memory_estimate_kb=size_kb
            )
        
        logger.info(f"Indexed {len(self.modules)} knowledge modules")
    
    def _infer_categories(self, name: str) -> List[str]:
        """Infer categories from module name"""
        categories = []
        
        if 'python' in name:
            categories.append('python')
        if 'javascript' in name or 'typescript' in name:
            categories.append('javascript')
        if 'security' in name or 'hacking' in name:
            categories.append('security')
        if 'database' in name or 'postgresql' in name:
            categories.append('database')
        if 'api' in name:
            categories.append('api')
        if 'test' in name or 'qa' in name:
            categories.append('testing')
        if 'frontend' in name:
            categories.append('frontend')
        if 'backend' in name:
            categories.append('backend')
        if 'devops' in name or 'docker' in name or 'sre' in name:
            categories.append('infrastructure')
        if 'ml' in name or 'data_engineering' in name:
            categories.append('data')
        
        return categories or ['general']
    
    def load_module(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a specific knowledge module
        
        Args:
            name: Module name (without .yaml)
            
        Returns:
            Module content or None
        """
        if name not in self.modules:
            logger.warning(f"Unknown module: {name}")
            return None
        
        module = self.modules[name]
        
        if module.loaded:
            return module.content
        
        # Load from file
        filepath = self.knowledge_dir / module.filename
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                module.content = yaml.safe_load(f) or {}
            module.loaded = True
            self._loaded_modules.add(name)
            logger.debug(f"Loaded knowledge module: {name}")
            return module.content
        except Exception as e:
            logger.error(f"Failed to load {name}: {e}")
            return None
    
    def unload_module(self, name: str):
        """
        Unload a knowledge module to free memory
        
        Args:
            name: Module name
        """
        if name in self.modules and self.modules[name].loaded:
            self.modules[name].content = {}
            self.modules[name].loaded = False
            self._loaded_modules.discard(name)
            logger.debug(f"Unloaded knowledge module: {name}")
    
    def get_knowledge_for_role(self, role: str) -> Dict[str, Any]:
        """
        Get knowledge appropriate for an agent role
        
        Args:
            role: Agent role (e.g., "backend", "frontend")
            
        Returns:
            Combined knowledge dictionary
        """
        # Normalize role
        role_lower = role.lower()
        role_key = None
        
        for key in self.ROLE_KNOWLEDGE_MAP:
            if key in role_lower:
                role_key = key
                break
        
        if not role_key:
            role_key = "backend"  # Default
        
        # Load core knowledge
        knowledge = {}
        for core in self.CORE_KNOWLEDGE:
            content = self.load_module(core)
            if content:
                knowledge[core] = content
        
        # Load role-specific knowledge
        for module_name in self.ROLE_KNOWLEDGE_MAP.get(role_key, []):
            content = self.load_module(module_name)
            if content:
                knowledge[module_name] = content
        
        logger.info(f"Loaded {len(knowledge)} modules for role: {role}")
        return knowledge
    
    def load_for_task(self, task: str, existing_knowledge: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Dynamically load knowledge needed for a specific task
        
        Args:
            task: Task description
            existing_knowledge: Already loaded knowledge
            
        Returns:
            Additional knowledge needed
        """
        task_lower = task.lower()
        additional = existing_knowledge.copy() if existing_knowledge else {}
        
        # Check triggers
        for trigger, modules in self.TOPIC_TRIGGERS.items():
            if trigger in task_lower:
                for module_name in modules:
                    if module_name not in additional:
                        content = self.load_module(module_name)
                        if content:
                            additional[module_name] = content
                            logger.info(f"Loaded {module_name} for task (trigger: {trigger})")
        
        return additional
    
    def get_memory_estimate(self) -> Dict[str, Any]:
        """
        Estimate memory usage
        
        Returns:
            Memory statistics
        """
        loaded_size = sum(
            self.modules[name].memory_estimate_kb 
            for name in self._loaded_modules
        )
        
        total_size = sum(m.memory_estimate_kb for m in self.modules.values())
        
        return {
            "loaded_modules": len(self._loaded_modules),
            "total_modules": len(self.modules),
            "loaded_size_kb": loaded_size,
            "total_size_kb": total_size,
            "efficiency": f"{(1 - loaded_size/total_size)*100:.1f}% memory saved" if total_size > 0 else "N/A"
        }
    
    def optimize_memory(self, max_modules: int = 10):
        """
        Unload least-used modules to optimize memory
        
        Args:
            max_modules: Maximum modules to keep loaded
        """
        if len(self._loaded_modules) <= max_modules:
            return
        
        # Keep core modules, unload others
        to_unload = [
            name for name in self._loaded_modules 
            if name not in self.CORE_KNOWLEDGE
        ]
        
        for name in to_unload[:(len(self._loaded_modules) - max_modules)]:
            self.unload_module(name)
        
        logger.info(f"Optimized memory: now {len(self._loaded_modules)} modules loaded")
    
    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """
        Search across all knowledge for a query
        
        Args:
            query: Search query
            
        Returns:
            Matching results
        """
        results = []
        query_lower = query.lower()
        
        for name, module in self.modules.items():
            # Load if needed for search
            content = self.load_module(name)
            if not content:
                continue
            
            # Simple search in content
            content_str = str(content).lower()
            if query_lower in content_str:
                results.append({
                    "module": name,
                    "categories": module.categories,
                    "match_type": "content"
                })
        
        return results


# Global instance for shared use
_loader_instance: Optional[DynamicKnowledgeLoader] = None

def get_knowledge_loader() -> DynamicKnowledgeLoader:
    """Get or create the global knowledge loader"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = DynamicKnowledgeLoader()
    return _loader_instance


def reset_knowledge_loader():
    """Reset the global loader (for testing)"""
    global _loader_instance
    _loader_instance = None


if __name__ == "__main__":
    # Demo
    loader = get_knowledge_loader()
    
    print("Available modules:")
    for name, module in loader.modules.items():
        print(f"  - {name}: {module.categories}")
    
    print("\nLoading for backend role:")
    knowledge = loader.get_knowledge_for_role("backend developer")
    print(f"Loaded: {list(knowledge.keys())}")
    
    print("\nMemory estimate:")
    print(loader.get_memory_estimate())
    
    print("\nLoading additional for security task:")
    knowledge = loader.load_for_task("implement JWT authentication with OWASP guidelines", knowledge)
    print(f"Now loaded: {list(knowledge.keys())}")
    
    print("\nFinal memory estimate:")
    print(loader.get_memory_estimate())
