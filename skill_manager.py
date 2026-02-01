"""
Modular Skills System for Abby

Manages loading/unloading of skills to keep active resources minimal
while having all abilities available on-demand.

Key Principles:
- Only active skills consume resources
- Skills can be hot-swapped without conversation interruption
- Abby can request skills she needs
- Frequently used skills stay loaded (smart caching)

Skill Categories:
- CORE: Always loaded (conversation, memory)
- ON_DEMAND: Loaded when needed, unloaded after use
- CACHED: Loaded and kept if recently used
"""
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Set
from enum import Enum
from threading import Lock


logger = logging.getLogger(__name__)


class SkillCategory(Enum):
    """How a skill is managed"""
    CORE = "core"           # Always loaded
    ON_DEMAND = "on_demand" # Load when needed, unload after
    CACHED = "cached"       # Keep loaded if recently used


class SkillStatus(Enum):
    """Current state of a skill"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


@dataclass
class SkillDefinition:
    """Definition of a skill"""
    name: str
    description: str
    category: SkillCategory
    module_path: str                    # e.g., "agents.action_executor"
    class_name: Optional[str] = None    # e.g., "ActionExecutor"
    factory_func: Optional[str] = None  # e.g., "get_executor"
    dependencies: List[str] = field(default_factory=list)  # Other skills needed
    keywords: List[str] = field(default_factory=list)      # Trigger words
    memory_estimate_mb: float = 0.0     # Rough memory usage
    
    def __hash__(self):
        return hash(self.name)


@dataclass
class LoadedSkill:
    """A skill that's currently loaded"""
    definition: SkillDefinition
    instance: Any
    loaded_at: float
    last_used: float
    use_count: int = 0
    status: SkillStatus = SkillStatus.LOADED


# ============== SKILL DEFINITIONS ==============

SKILL_DEFINITIONS: Dict[str, SkillDefinition] = {
    # CORE - Always loaded
    "conversation": SkillDefinition(
        name="conversation",
        description="Basic conversation and response generation",
        category=SkillCategory.CORE,
        module_path="parallel_thinker",
        class_name="ParallelThinker",
        keywords=["chat", "talk", "say", "respond"],
        memory_estimate_mb=50.0
    ),
    "memory": SkillDefinition(
        name="memory",
        description="Short-term and working memory",
        category=SkillCategory.CORE,
        module_path="memory.working_memory",
        class_name="WorkingMemory",
        keywords=["remember", "recall", "context"],
        memory_estimate_mb=20.0
    ),
    
    # CACHED - Keep loaded if recently used
    "code_execution": SkillDefinition(
        name="code_execution",
        description="Execute Python code and shell commands",
        category=SkillCategory.CACHED,
        module_path="agents.action_executor",
        factory_func="get_executor",
        keywords=["run", "execute", "code", "python", "script", "command"],
        memory_estimate_mb=30.0
    ),
    "file_operations": SkillDefinition(
        name="file_operations",
        description="Create, read, edit, delete files",
        category=SkillCategory.CACHED,
        module_path="agents.action_executor",
        factory_func="get_executor",
        keywords=["file", "create", "read", "write", "edit", "delete", "save"],
        memory_estimate_mb=10.0
    ),
    "task_planning": SkillDefinition(
        name="task_planning",
        description="Plan multi-step tasks",
        category=SkillCategory.CACHED,
        module_path="agents.task_planner",
        class_name="TaskPlanner",
        dependencies=["code_execution"],
        keywords=["plan", "steps", "task", "break down", "how to"],
        memory_estimate_mb=40.0
    ),
    
    # ON_DEMAND - Load only when needed
    "web_research": SkillDefinition(
        name="web_research",
        description="Search the web and fetch pages",
        category=SkillCategory.ON_DEMAND,
        module_path="agents.research_toolkit",
        class_name="ResearchToolkit",
        keywords=["search", "web", "google", "find online", "research", "look up"],
        memory_estimate_mb=25.0
    ),
    "face_recognition": SkillDefinition(
        name="face_recognition",
        description="Recognize faces in images/video",
        category=SkillCategory.ON_DEMAND,
        module_path="presence.face_recognition",
        class_name="FaceRecognitionEngine",
        keywords=["face", "recognize", "who is", "identify person"],
        memory_estimate_mb=200.0  # ML models are heavy
    ),
    "visual_awareness": SkillDefinition(
        name="visual_awareness",
        description="See through webcam, track presence",
        category=SkillCategory.ON_DEMAND,
        module_path="presence.visual_awareness",
        class_name="VisualAwareness",
        dependencies=["face_recognition"],
        keywords=["see", "look", "camera", "webcam", "watch", "visual"],
        memory_estimate_mb=150.0
    ),
    "tts": SkillDefinition(
        name="tts",
        description="Text-to-speech synthesis",
        category=SkillCategory.CACHED,
        module_path="speech_interface.elevenlabs_tts",
        class_name="ElevenLabsTTS",
        keywords=["speak", "say", "voice", "audio", "read aloud"],
        memory_estimate_mb=50.0
    ),
    "stt": SkillDefinition(
        name="stt",
        description="Speech-to-text recognition",
        category=SkillCategory.ON_DEMAND,
        module_path="speech_interface.stt_engine",
        class_name="STTEngine",
        keywords=["listen", "hear", "transcribe", "speech"],
        memory_estimate_mb=100.0
    ),
    "agent_factory": SkillDefinition(
        name="agent_factory",
        description="Create specialized agents",
        category=SkillCategory.ON_DEMAND,
        module_path="agents.agent_factory",
        class_name="AgentFactory",
        keywords=["agent", "specialist", "expert", "delegate"],
        memory_estimate_mb=30.0
    ),
    "git_operations": SkillDefinition(
        name="git_operations",
        description="Git version control operations",
        category=SkillCategory.ON_DEMAND,
        module_path="agents.action_executor",
        factory_func="get_executor",
        keywords=["git", "commit", "push", "pull", "branch", "merge"],
        memory_estimate_mb=10.0
    ),
    "knowledge_base": SkillDefinition(
        name="knowledge_base",
        description="Access domain-specific knowledge",
        category=SkillCategory.CACHED,
        module_path="agents.knowledge",
        keywords=["knowledge", "best practice", "how should", "pattern"],
        memory_estimate_mb=20.0
    ),
}


class SkillManager:
    """
    Manages Abby's modular skill system.
    
    - Loads skills on-demand
    - Keeps frequently used skills cached
    - Unloads unused skills to save resources
    - Tracks skill usage for smart caching
    """
    
    def __init__(
        self,
        cache_timeout_seconds: float = 300.0,  # Unload cached skills after 5 min
        max_memory_mb: float = 1000.0,         # Max memory for skills
    ):
        self.cache_timeout = cache_timeout_seconds
        self.max_memory_mb = max_memory_mb
        
        self._loaded_skills: Dict[str, LoadedSkill] = {}
        self._lock = Lock()
        self._skill_defs = SKILL_DEFINITIONS.copy()
        
        # Stats
        self._total_loads = 0
        self._total_unloads = 0
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info(f"SkillManager initialized with {len(self._skill_defs)} skills defined")
        
        # Load core skills immediately
        self._load_core_skills()
    
    def _load_core_skills(self):
        """Load skills marked as CORE"""
        for name, skill_def in self._skill_defs.items():
            if skill_def.category == SkillCategory.CORE:
                self.load_skill(name)
    
    def _import_skill(self, skill_def: SkillDefinition) -> Any:
        """Import and instantiate a skill"""
        import importlib
        
        try:
            module = importlib.import_module(skill_def.module_path)
            
            if skill_def.factory_func:
                factory = getattr(module, skill_def.factory_func)
                return factory()
            elif skill_def.class_name:
                cls = getattr(module, skill_def.class_name)
                return cls()
            else:
                return module
                
        except Exception as e:
            logger.error(f"Failed to import skill {skill_def.name}: {e}")
            raise
    
    def load_skill(self, name: str) -> Optional[Any]:
        """
        Load a skill and return its instance.
        If already loaded, returns cached instance.
        """
        with self._lock:
            # Check if already loaded
            if name in self._loaded_skills:
                skill = self._loaded_skills[name]
                skill.last_used = time.time()
                skill.use_count += 1
                self._cache_hits += 1
                logger.debug(f"Skill '{name}' cache hit (uses: {skill.use_count})")
                return skill.instance
            
            # Get definition
            if name not in self._skill_defs:
                logger.error(f"Unknown skill: {name}")
                return None
            
            skill_def = self._skill_defs[name]
            self._cache_misses += 1
            
            # Load dependencies first
            for dep in skill_def.dependencies:
                if dep not in self._loaded_skills:
                    self.load_skill(dep)
            
            # Check memory budget
            self._check_memory_budget(skill_def.memory_estimate_mb)
            
            # Import and instantiate
            try:
                logger.info(f"Loading skill: {name}")
                instance = self._import_skill(skill_def)
                
                now = time.time()
                self._loaded_skills[name] = LoadedSkill(
                    definition=skill_def,
                    instance=instance,
                    loaded_at=now,
                    last_used=now,
                    use_count=1,
                    status=SkillStatus.LOADED
                )
                
                self._total_loads += 1
                logger.info(f"Skill '{name}' loaded successfully")
                return instance
                
            except Exception as e:
                logger.error(f"Failed to load skill {name}: {e}")
                return None
    
    def unload_skill(self, name: str) -> bool:
        """Unload a skill to free resources"""
        with self._lock:
            if name not in self._loaded_skills:
                return False
            
            skill = self._loaded_skills[name]
            
            # Don't unload core skills
            if skill.definition.category == SkillCategory.CORE:
                logger.warning(f"Cannot unload core skill: {name}")
                return False
            
            # Cleanup if skill has cleanup method
            if hasattr(skill.instance, 'cleanup'):
                try:
                    skill.instance.cleanup()
                except Exception as e:
                    logger.warning(f"Skill cleanup error: {e}")
            
            del self._loaded_skills[name]
            self._total_unloads += 1
            logger.info(f"Skill '{name}' unloaded")
            return True
    
    def _check_memory_budget(self, needed_mb: float):
        """Unload old skills if memory budget exceeded"""
        current_usage = sum(
            s.definition.memory_estimate_mb 
            for s in self._loaded_skills.values()
        )
        
        if current_usage + needed_mb > self.max_memory_mb:
            # Find skills to unload (oldest, non-core, cached)
            candidates = [
                (name, skill) 
                for name, skill in self._loaded_skills.items()
                if skill.definition.category != SkillCategory.CORE
            ]
            
            # Sort by last used (oldest first)
            candidates.sort(key=lambda x: x[1].last_used)
            
            freed = 0.0
            for name, skill in candidates:
                if current_usage + needed_mb - freed <= self.max_memory_mb:
                    break
                self.unload_skill(name)
                freed += skill.definition.memory_estimate_mb
    
    def cleanup_stale_skills(self):
        """Unload skills that haven't been used recently"""
        now = time.time()
        to_unload = []
        
        with self._lock:
            for name, skill in self._loaded_skills.items():
                if skill.definition.category == SkillCategory.ON_DEMAND:
                    if now - skill.last_used > self.cache_timeout:
                        to_unload.append(name)
                elif skill.definition.category == SkillCategory.CACHED:
                    if now - skill.last_used > self.cache_timeout * 2:
                        to_unload.append(name)
        
        for name in to_unload:
            self.unload_skill(name)
        
        return len(to_unload)
    
    def get_skill(self, name: str) -> Optional[Any]:
        """Get a skill instance, loading if necessary"""
        return self.load_skill(name)
    
    def detect_needed_skills(self, query: str) -> Set[str]:
        """
        Analyze a query to determine which skills might be needed.
        Abby uses this to proactively load skills.
        """
        query_lower = query.lower()
        needed = set()
        
        for name, skill_def in self._skill_defs.items():
            for keyword in skill_def.keywords:
                if keyword in query_lower:
                    needed.add(name)
                    # Also add dependencies
                    needed.update(skill_def.dependencies)
                    break
        
        return needed
    
    def ensure_skills(self, skill_names: List[str]) -> Dict[str, Any]:
        """Load multiple skills and return their instances"""
        result = {}
        for name in skill_names:
            instance = self.load_skill(name)
            if instance:
                result[name] = instance
        return result
    
    def is_loaded(self, name: str) -> bool:
        """Check if a skill is currently loaded"""
        return name in self._loaded_skills
    
    def get_loaded_skills(self) -> List[str]:
        """Get list of currently loaded skills"""
        return list(self._loaded_skills.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get skill manager statistics"""
        loaded = self._loaded_skills
        return {
            "loaded_count": len(loaded),
            "loaded_skills": list(loaded.keys()),
            "total_loads": self._total_loads,
            "total_unloads": self._total_unloads,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": self._cache_hits / max(1, self._cache_hits + self._cache_misses),
            "estimated_memory_mb": sum(
                s.definition.memory_estimate_mb for s in loaded.values()
            ),
            "skills_by_category": {
                "core": [n for n, s in loaded.items() if s.definition.category == SkillCategory.CORE],
                "cached": [n for n, s in loaded.items() if s.definition.category == SkillCategory.CACHED],
                "on_demand": [n for n, s in loaded.items() if s.definition.category == SkillCategory.ON_DEMAND],
            }
        }
    
    def describe_skill(self, name: str) -> Optional[Dict[str, Any]]:
        """Get description of a skill"""
        if name not in self._skill_defs:
            return None
        
        skill_def = self._skill_defs[name]
        loaded = self._loaded_skills.get(name)
        
        return {
            "name": skill_def.name,
            "description": skill_def.description,
            "category": skill_def.category.value,
            "keywords": skill_def.keywords,
            "memory_mb": skill_def.memory_estimate_mb,
            "dependencies": skill_def.dependencies,
            "is_loaded": loaded is not None,
            "use_count": loaded.use_count if loaded else 0,
        }
    
    def list_all_skills(self) -> List[Dict[str, Any]]:
        """List all available skills with their status"""
        return [self.describe_skill(name) for name in self._skill_defs.keys()]


# Global skill manager instance
_skill_manager: Optional[SkillManager] = None


def get_skill_manager() -> SkillManager:
    """Get or create the global skill manager"""
    global _skill_manager
    if _skill_manager is None:
        _skill_manager = SkillManager()
    return _skill_manager


def get_skill(name: str) -> Any:
    """Convenience function to get a skill"""
    return get_skill_manager().get_skill(name)


if __name__ == "__main__":
    # Test the skill manager
    logging.basicConfig(level=logging.INFO)
    
    manager = SkillManager()
    
    print("\n=== Available Skills ===")
    for skill in manager.list_all_skills():
        status = "✅ LOADED" if skill["is_loaded"] else "⬜ available"
        print(f"  {skill['name']:20} [{skill['category']:10}] {status}")
        print(f"    {skill['description']}")
        print(f"    Keywords: {', '.join(skill['keywords'][:5])}")
        print()
    
    print("\n=== Skill Detection Test ===")
    test_queries = [
        "Can you search the web for Python tutorials?",
        "Create a new file called test.py",
        "Who is that person in the camera?",
        "Run this Python code",
        "What's up?",
    ]
    
    for query in test_queries:
        needed = manager.detect_needed_skills(query)
        print(f"  '{query[:40]}...' -> {needed or 'conversation only'}")
    
    print("\n=== Stats ===")
    stats = manager.get_stats()
    print(f"  Loaded: {stats['loaded_count']} skills")
    print(f"  Memory: ~{stats['estimated_memory_mb']:.0f} MB")
    print(f"  Core: {stats['skills_by_category']['core']}")
