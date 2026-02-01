"""
Base Agent class for all agents in the system
"""
from typing import Dict, Any, Optional, List
import logging
import os
import yaml
from agents.agent_dna import AgentDNA
from agents.research_toolkit import get_research_toolkit, KnowledgeAcquisition


logger = logging.getLogger(__name__)


# Load all coding knowledge bases
CODING_KNOWLEDGE = None

def load_all_coding_knowledge() -> Dict[str, Any]:
    """
    Load ALL coding knowledge bases that make agents super experts
    
    Includes:
    - Coding foundations (vibe coding awareness)
    - Python mastery
    - Docker mastery
    - Kotlin mastery
    - JavaScript/TypeScript mastery
    - General programming (SOLID, Clean Code)
    - Security practices (OWASP)
    - Database mastery
    - API design
    - Git mastery
    - Testing mastery
    - Performance optimization
    - DevOps/CI-CD
    - Error handling
    """
    global CODING_KNOWLEDGE
    
    if CODING_KNOWLEDGE is not None:
        return CODING_KNOWLEDGE
    
    knowledge_dir = os.path.join(os.path.dirname(__file__), "knowledge")
    CODING_KNOWLEDGE = {}
    
    # List of knowledge files to load
    knowledge_files = [
        "coding_foundations.yaml",       # AI coding awareness
        "python_mastery.yaml",           # Python expertise
        "docker_mastery.yaml",           # Docker/containers
        "kotlin_mastery.yaml",           # Kotlin
        "javascript_typescript_mastery.yaml",  # JS/TS
        "general_programming.yaml",      # SOLID, Clean Code
        "security_practices.yaml",       # OWASP, security
        "database_mastery.yaml",         # SQL, NoSQL
        "api_design_mastery.yaml",       # REST APIs
        "git_mastery.yaml",              # Version control
        "testing_mastery.yaml",          # Testing patterns
        "performance_mastery.yaml",      # Optimization
        "devops_mastery.yaml",           # CI/CD, infra
        "error_handling_mastery.yaml",   # Error handling
    ]
    
    loaded_count = 0
    for filename in knowledge_files:
        filepath = os.path.join(knowledge_dir, filename)
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    # Store with filename as key (without .yaml)
                    key = filename.replace('.yaml', '')
                    CODING_KNOWLEDGE[key] = yaml.safe_load(f)
                    loaded_count += 1
        except Exception as e:
            logger.warning(f"Could not load {filename}: {e}")
    
    logger.info(f"Loaded {loaded_count} coding knowledge bases")
    return CODING_KNOWLEDGE


def load_coding_foundations() -> Dict[str, Any]:
    """Legacy function - loads just coding foundations"""
    all_knowledge = load_all_coding_knowledge()
    return all_knowledge.get('coding_foundations', {})


class Agent:
    """
    Base Agent class that all specialized agents inherit from
    
    Agents acquire real expertise through internet research, not just
    by claiming to know things. When an agent is created with a domain,
    it researches that domain to build actual knowledge.
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
        
        # Research toolkit for acquiring knowledge
        self.research = get_research_toolkit()
        
        # Knowledge acquired through research
        self.acquired_knowledge: Dict[str, KnowledgeAcquisition] = {}
        
        # ALL coding knowledge (comprehensive expertise)
        self.all_knowledge = None
        self.coding_foundations = None
        
        if self._is_coding_related():
            # Load ALL knowledge bases - makes agent a super expert
            self.all_knowledge = load_all_coding_knowledge()
            self.coding_foundations = self.all_knowledge.get('coding_foundations', {})
            logger.info(f"Agent {dna.role} loaded {len(self.all_knowledge)} knowledge bases")
        
        # Acquire initial domain expertise
        self._acquire_initial_expertise()
        
        logger.info(f"Initialized agent: {self.dna}")
    
    def _is_coding_related(self) -> bool:
        """Check if this agent deals with coding/programming tasks"""
        coding_indicators = [
            'code', 'coding', 'programming', 'developer', 'software',
            'engineer', 'python', 'javascript', 'java', 'rust', 'go',
            'backend', 'frontend', 'fullstack', 'devops', 'api',
            'database', 'web', 'mobile', 'app', 'architect', 'tech'
        ]
        
        # Check role and domain
        check_text = f"{self.dna.role} {self.dna.domain}".lower()
        return any(indicator in check_text for indicator in coding_indicators)
    
    def _acquire_initial_expertise(self):
        """
        Acquire initial expertise in the agent's domain
        
        An agent claiming to be an expert should actually research
        and learn about their domain, not just pretend to know it.
        """
        try:
            # Build search topics from DNA
            domain = self.dna.domain
            subtopics = list(self.dna.industry_knowledge)[:3]  # Top 3 knowledge areas
            
            # Add methodologies as subtopics
            subtopics.extend([m for m in self.dna.methodologies[:2]])
            
            logger.info(f"Agent {self.dna.role} acquiring expertise in {domain}...")
            
            # Research the domain (quick for initial load, can deepen later)
            self.acquired_knowledge = self.research.acquire_domain_expertise(
                domain=domain,
                subtopics=subtopics
            )
            
            logger.info(f"Agent {self.dna.role} acquired knowledge from {len(self.acquired_knowledge)} topics")
            
        except Exception as e:
            logger.warning(f"Could not acquire initial expertise: {e}")
            # Agent can still function, just without research-backed knowledge
    
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
        Actual task execution using LLM with research-backed knowledge
        
        Args:
            task: Task description
            context: Task context
            
        Returns:
            Result dictionary
        """
        from ollama_integration.client import OllamaClient
        
        try:
            # Get Ollama client
            client = OllamaClient()
            model = os.getenv("DEFAULT_MODEL", "qwen2.5:latest")
            
            # Build system prompt from agent DNA and acquired knowledge
            system_prompt = self.get_system_prompt()
            
            # Research for this specific task if needed
            task_research = ""
            if self._should_research_task(task):
                task_research = self.research.lookup_for_task(task, self.dna.domain)
                if task_research:
                    logger.info(f"Agent {self.dna.role} found relevant research for task")
            
            # Build the task prompt with context and research
            context_str = ""
            if context:
                context_items = [f"- {k}: {v}" for k, v in context.items()]
                context_str = f"\n\nContext:\n" + "\n".join(context_items)
            
            # Add acquired knowledge summary to prompt
            knowledge_str = self._format_knowledge_for_prompt()
            
            full_prompt = f"{task}{context_str}{task_research}"
            
            # Call LLM
            response = client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                model=model
            )
            
            # Extract response
            if "error" in response:
                logger.error(f"LLM error: {response['error']}")
                return {
                    "status": "error",
                    "output": f"Error: {response['error']}",
                    "agent": str(self.dna)
                }
            
            output = response.get("message", {}).get("content", "")
            if not output:
                output = response.get("response", "Task completed but no output generated.")
            
            return {
                "status": "completed",
                "output": output,
                "agent": str(self.dna),
                "model": model
            }
            
        except Exception as e:
            logger.error(f"Error in perform_task: {e}")
            return {
                "status": "error",
                "output": f"Error executing task: {str(e)}",
                "agent": str(self.dna)
            }
    
    def get_system_prompt(self) -> str:
        """
        Build system prompt from DNA, personality, and ACQUIRED KNOWLEDGE
        
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
        
        # Add FOUNDATIONAL CODING KNOWLEDGE (critical for AI-assisted coding)
        if self.coding_foundations:
            coding_guidance = self._format_coding_foundations()
            if coding_guidance:
                prompt_parts.append(f"\n\n=== CRITICAL: AI Coding Best Practices ===\n{coding_guidance}")
        
        # Add EXPERT KNOWLEDGE from knowledge bases
        if self.all_knowledge:
            expert_knowledge = self._format_expert_knowledge()
            if expert_knowledge:
                prompt_parts.append(f"\n\n=== Your Expert Knowledge Base ===\n{expert_knowledge}")
        
        # Add REAL knowledge acquired from research
        knowledge_section = self._format_knowledge_for_prompt()
        if knowledge_section:
            prompt_parts.append(f"\n\n=== Your Expert Knowledge (from research) ===\n{knowledge_section}")
        
        # Add personality traits if available
        if self.personality:
            if "communication_style" in self.personality:
                style = self.personality["communication_style"]
                prompt_parts.append(f"\nCommunication Style: {style.get('tone', '')}")
        
        # Add behavior guardrails
        prompt_parts.append("\n\n=== BEHAVIOR GUARDRAILS ===")
        prompt_parts.append("- NEVER create files, run commands, or make changes without being explicitly asked")
        prompt_parts.append("- Before creating any file or running any code, ASK FOR PERMISSION first")
        prompt_parts.append("- Test files, demos, and examples should only be created when the user requests them")
        prompt_parts.append("- If you want to demonstrate something, DESCRIBE what you would create and ask if they want you to proceed")
        prompt_parts.append("- Only take action when given a clear task or explicit permission")
        
        prompt_parts.append("\n\nIMPORTANT: Base your responses on the expert knowledge you have acquired through research. Cite sources when relevant.")
        
        return "\n".join(prompt_parts)
    
    def _format_coding_foundations(self) -> str:
        """Format foundational coding knowledge for the system prompt"""
        if not self.coding_foundations:
            return ""
        
        vibe = self.coding_foundations.get('vibe_coding_awareness', {})
        parts = []
        
        # Add awareness of AI coding limitations
        parts.append("UNDERSTAND THESE AI-CODING LIMITATIONS:")
        limitations = vibe.get('limitations', [])
        for lim in limitations:
            parts.append(f"\n• {lim.get('name', 'Unknown')}: {lim.get('issue', '')[:150]}...")
            parts.append(f"  → Mitigation: {lim.get('mitigation', '')[:200]}...")
        
        # Add best practices
        practices = vibe.get('best_practices', {})
        if practices.get('always_do'):
            parts.append("\n\nALWAYS DO:")
            for item in practices['always_do'][:5]:
                parts.append(f"  ✓ {item}")
        
        if practices.get('never_do'):
            parts.append("\nNEVER DO:")
            for item in practices['never_do'][:5]:
                parts.append(f"  ✗ {item}")
        
        # Add checklist reminder
        checklist = vibe.get('coding_checklist', {})
        if checklist.get('after_coding'):
            parts.append("\n\nAFTER CODING - ALWAYS:")
            for item in checklist['after_coding']:
                parts.append(f"  □ {item}")
        
        return '\n'.join(parts)
    
    def _format_expert_knowledge(self) -> str:
        """Format expert knowledge from all loaded knowledge bases"""
        if not self.all_knowledge:
            return ""
        
        parts = []
        parts.append("You have comprehensive expertise in:")
        
        # Summarize available knowledge areas
        knowledge_areas = {
            'python_mastery': 'Python (best practices, performance, async, testing)',
            'docker_mastery': 'Docker (multi-stage builds, security, compose)',
            'kotlin_mastery': 'Kotlin (coroutines, null safety, idioms)',
            'javascript_typescript_mastery': 'JS/TS (types, React, Node.js)',
            'general_programming': 'Clean Code, SOLID, design patterns',
            'security_practices': 'Security (OWASP Top 10, input validation)',
            'database_mastery': 'Databases (SQL optimization, NoSQL, indexing)',
            'api_design_mastery': 'API Design (REST, versioning, caching)',
            'git_mastery': 'Git (branching, rebasing, workflows)',
            'testing_mastery': 'Testing (TDD, mocking, coverage)',
            'performance_mastery': 'Performance (profiling, caching, async)',
            'devops_mastery': 'DevOps (CI/CD, Kubernetes, monitoring)',
            'error_handling_mastery': 'Error Handling (exceptions, debugging)',
        }
        
        available = []
        for key, desc in knowledge_areas.items():
            if key in self.all_knowledge:
                available.append(f"  • {desc}")
        
        parts.extend(available)
        
        parts.append("\n\nYou KNOW:")
        parts.append("  • Common anti-patterns and how to avoid them")
        parts.append("  • Best practices with concrete code examples")
        parts.append("  • Performance optimizations with measured improvements")
        parts.append("  • Security vulnerabilities and how to prevent them")
        parts.append("  • Testing strategies for reliable code")
        
        parts.append("\n\nWhen coding, ALWAYS:")
        parts.append("  1. Consider security implications")
        parts.append("  2. Handle errors properly")
        parts.append("  3. Write testable code")
        parts.append("  4. Avoid known anti-patterns")
        parts.append("  5. Follow language-specific idioms")
        
        return '\n'.join(parts)
    
    def _format_knowledge_for_prompt(self) -> str:
        """Format acquired knowledge for inclusion in prompt"""
        if not self.acquired_knowledge:
            return ""
        
        parts = []
        for topic, knowledge in self.acquired_knowledge.items():
            parts.append(f"\n### {topic}")
            
            # Add key facts
            if knowledge.key_facts:
                parts.append("Key facts:")
                for fact in knowledge.key_facts[:5]:  # Limit per topic
                    parts.append(f"  • {fact}")
            
            # Add summary
            if knowledge.summary:
                parts.append(f"Summary: {knowledge.summary[:300]}...")
            
            # Note sources
            if knowledge.sources:
                sources = [s.source for s in knowledge.sources[:3]]
                parts.append(f"Sources: {', '.join(sources)}")
        
        return '\n'.join(parts)
    
    def _should_research_task(self, task: str) -> bool:
        """Determine if task requires additional research"""
        # Research for tasks that seem to need current/specific info
        research_indicators = [
            'latest', 'current', 'recent', 'new', 'updated',
            'how to', 'what is', 'explain', 'best practice',
            'documentation', 'guide', 'tutorial', 'example',
            'compare', 'difference', 'versus', 'vs',
            'research', 'find', 'look up', 'search'
        ]
        task_lower = task.lower()
        return any(indicator in task_lower for indicator in research_indicators)
    
    def research_topic(self, topic: str, depth: str = "standard") -> str:
        """
        Perform additional research on a topic during task execution
        
        Args:
            topic: Topic to research
            depth: Research depth (quick/standard/deep)
            
        Returns:
            Summary of findings
        """
        knowledge = self.research.research_topic(topic, depth)
        
        # Store in acquired knowledge
        self.acquired_knowledge[topic] = knowledge
        
        return knowledge.summary
    
    def deep_dive(self, topic: str) -> KnowledgeAcquisition:
        """
        Perform deep research into a specific topic
        
        Args:
            topic: Topic for deep research
            
        Returns:
            KnowledgeAcquisition with detailed findings
        """
        logger.info(f"Agent {self.dna.role} performing deep dive on: {topic}")
        knowledge = self.research.research_topic(topic, depth="deep")
        self.acquired_knowledge[topic] = knowledge
        return knowledge
    
    def _format_constraints(self) -> str:
        """Format constraints for prompt"""
        return ", ".join([f"{k}: {v}" for k, v in self.dna.constraints.items()])
    
    def _format_output_format(self) -> str:
        """Format output format for prompt"""
        return ", ".join([f"{k}: {v}" for k, v in self.dna.output_format.items()])
    
    def get_knowledge_for_topic(self, topic: str) -> Dict[str, Any]:
        """
        Get relevant knowledge for a specific topic
        
        Args:
            topic: Topic to get knowledge for (e.g., 'python', 'docker', 'testing')
            
        Returns:
            Relevant knowledge dictionary
        """
        if not self.all_knowledge:
            return {}
        
        topic_lower = topic.lower()
        
        # Map topics to knowledge bases
        topic_mappings = {
            'python': 'python_mastery',
            'docker': 'docker_mastery',
            'container': 'docker_mastery',
            'kotlin': 'kotlin_mastery',
            'android': 'kotlin_mastery',
            'javascript': 'javascript_typescript_mastery',
            'typescript': 'javascript_typescript_mastery',
            'js': 'javascript_typescript_mastery',
            'ts': 'javascript_typescript_mastery',
            'react': 'javascript_typescript_mastery',
            'node': 'javascript_typescript_mastery',
            'security': 'security_practices',
            'owasp': 'security_practices',
            'database': 'database_mastery',
            'sql': 'database_mastery',
            'nosql': 'database_mastery',
            'mongodb': 'database_mastery',
            'redis': 'database_mastery',
            'api': 'api_design_mastery',
            'rest': 'api_design_mastery',
            'git': 'git_mastery',
            'version control': 'git_mastery',
            'test': 'testing_mastery',
            'testing': 'testing_mastery',
            'tdd': 'testing_mastery',
            'performance': 'performance_mastery',
            'optimization': 'performance_mastery',
            'cache': 'performance_mastery',
            'devops': 'devops_mastery',
            'ci': 'devops_mastery',
            'cd': 'devops_mastery',
            'kubernetes': 'devops_mastery',
            'k8s': 'devops_mastery',
            'error': 'error_handling_mastery',
            'exception': 'error_handling_mastery',
            'debug': 'error_handling_mastery',
            'clean code': 'general_programming',
            'solid': 'general_programming',
            'design pattern': 'general_programming',
        }
        
        # Find matching knowledge base
        for key, knowledge_key in topic_mappings.items():
            if key in topic_lower:
                return self.all_knowledge.get(knowledge_key, {})
        
        return {}
    
    def get_anti_patterns_for(self, language: str) -> List[Dict[str, Any]]:
        """
        Get anti-patterns for a specific language/technology
        
        Args:
            language: Language or technology (e.g., 'python', 'javascript')
            
        Returns:
            List of anti-patterns with examples
        """
        knowledge = self.get_knowledge_for_topic(language)
        if not knowledge:
            return []
        
        # Look for anti_patterns in the knowledge
        anti_patterns = []
        
        def find_anti_patterns(d, path=""):
            if isinstance(d, dict):
                if 'anti_patterns' in d:
                    anti_patterns.extend(d['anti_patterns'])
                for key, value in d.items():
                    if key == 'bad' or key == 'dont' or 'anti' in key.lower():
                        anti_patterns.append({key: value})
                    find_anti_patterns(value, f"{path}.{key}")
            elif isinstance(d, list):
                for item in d:
                    find_anti_patterns(item, path)
        
        find_anti_patterns(knowledge)
        return anti_patterns[:20]  # Limit to 20 most relevant
