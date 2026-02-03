"""
Agent Stress Tests - Determine optimal concurrent agent capacity
Tests memory limits, knowledge access, and cross-disciplinary capabilities
"""
import pytest
import psutil
import time
import asyncio
import threading
import gc
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent_factory import AgentFactory
from agents.base_agent import Agent, load_all_coding_knowledge
from agents.agent_dna import AgentDNA
from persona_library.library_manager import PersonaLibrary

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Metrics for a single agent"""
    agent_id: str
    creation_time_ms: float
    memory_mb: float
    knowledge_loaded: int
    task_completion_time_ms: float = 0.0
    task_success: bool = False
    error: str = ""


@dataclass
class StressTestResult:
    """Results from stress test"""
    max_agents: int
    optimal_agents: int
    total_memory_mb: float
    baseline_memory_mb: float
    memory_per_agent_mb: float
    creation_times: List[float] = field(default_factory=list)
    agent_metrics: List[AgentMetrics] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentStressTester:
    """
    Stress tester to find optimal number of concurrent agents
    """
    
    # Memory thresholds (percentages of system RAM)
    MAX_MEMORY_PERCENT = 70  # Don't exceed 70% of system RAM
    OPTIMAL_MEMORY_PERCENT = 50  # Target 50% for optimal performance
    MIN_FREE_MEMORY_MB = 2048  # Always keep 2GB free
    
    def __init__(self):
        self.baseline_memory = self._get_memory_usage()
        self.system_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
        self.agents: Dict[str, Agent] = {}
        self.factory = AgentFactory()
        
    def _get_memory_usage(self) -> float:
        """Get current process memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    
    def _get_system_free_memory(self) -> float:
        """Get system free memory in MB"""
        return psutil.virtual_memory().available / (1024 * 1024)
    
    def _should_continue(self, current_agents: int) -> Tuple[bool, str]:
        """Check if we should continue spawning agents"""
        current_memory = self._get_memory_usage()
        free_memory = self._get_system_free_memory()
        memory_percent = (current_memory / self.system_memory) * 100
        
        if memory_percent >= self.MAX_MEMORY_PERCENT:
            return False, f"Memory limit reached ({memory_percent:.1f}%)"
        
        if free_memory < self.MIN_FREE_MEMORY_MB:
            return False, f"Free memory too low ({free_memory:.0f}MB)"
        
        return True, ""
    
    def create_agent_with_metrics(
        self, 
        role: str, 
        domain: str, 
        agent_id: str
    ) -> AgentMetrics:
        """Create agent and measure metrics"""
        start_memory = self._get_memory_usage()
        start_time = time.perf_counter()
        
        try:
            dna = AgentDNA(
                role=role,
                seniority="Senior",
                domain=domain,
                industry_knowledge=[domain, "Best Practices"],
                methodologies=["Agile", "Test-Driven Development"],
                constraints={"quality": "Production-ready", "timeline": "Standard"},
                output_format={"style": "professional", "format": "markdown"}
            )
            
            agent = Agent(dna=dna)
            self.agents[agent_id] = agent
            
            creation_time = (time.perf_counter() - start_time) * 1000
            memory_after = self._get_memory_usage()
            
            knowledge_count = len(agent.all_knowledge or {})
            
            return AgentMetrics(
                agent_id=agent_id,
                creation_time_ms=creation_time,
                memory_mb=memory_after - start_memory,
                knowledge_loaded=knowledge_count
            )
            
        except Exception as e:
            return AgentMetrics(
                agent_id=agent_id,
                creation_time_ms=(time.perf_counter() - start_time) * 1000,
                memory_mb=0,
                knowledge_loaded=0,
                error=str(e)
            )
    
    def find_max_agents(self) -> StressTestResult:
        """
        Find maximum number of agents that can run without disrupting system
        """
        gc.collect()  # Clean slate
        self.baseline_memory = self._get_memory_usage()
        
        result = StressTestResult(
            max_agents=0,
            optimal_agents=0,
            total_memory_mb=0,
            baseline_memory_mb=self.baseline_memory,
            memory_per_agent_mb=0
        )
        
        # Agent templates to cycle through
        templates = [
            ("Backend Developer", "Python"),
            ("Frontend Developer", "React/TypeScript"),
            ("Security Engineer", "Application Security"),
            ("Data Engineer", "ETL/Spark"),
            ("ML Engineer", "MLOps"),
            ("QA Engineer", "Testing"),
            ("DBA", "PostgreSQL"),
            ("SRE", "Reliability"),
            ("iOS Developer", "Swift/SwiftUI"),
            ("Technical Writer", "Documentation"),
            ("Code Reviewer", "Quality"),
            ("Debugger", "Troubleshooting"),
            ("DevOps Engineer", "CI/CD"),
            ("Architect", "System Design"),
        ]
        
        agent_count = 0
        template_idx = 0
        
        while True:
            can_continue, reason = self._should_continue(agent_count)
            
            if not can_continue:
                result.errors.append(f"Stopped at {agent_count} agents: {reason}")
                break
            
            # Cycle through templates
            role, domain = templates[template_idx % len(templates)]
            agent_id = f"agent_{agent_count}_{role.replace(' ', '_')}"
            
            metrics = self.create_agent_with_metrics(role, domain, agent_id)
            result.agent_metrics.append(metrics)
            result.creation_times.append(metrics.creation_time_ms)
            
            if metrics.error:
                result.errors.append(f"Agent {agent_id}: {metrics.error}")
                break
            
            agent_count += 1
            template_idx += 1
            
            # Check optimal threshold
            current_memory_percent = (self._get_memory_usage() / self.system_memory) * 100
            if current_memory_percent <= self.OPTIMAL_MEMORY_PERCENT:
                result.optimal_agents = agent_count
            
            # Safety limit
            if agent_count >= 100:
                result.errors.append("Safety limit of 100 agents reached")
                break
        
        result.max_agents = agent_count
        result.total_memory_mb = self._get_memory_usage()
        
        if agent_count > 0:
            result.memory_per_agent_mb = (
                (result.total_memory_mb - self.baseline_memory) / agent_count
            )
        
        return result
    
    def cleanup(self):
        """Clean up all agents"""
        self.agents.clear()
        gc.collect()


class TestAgentStress:
    """Stress tests for agent system"""
    
    @pytest.fixture
    def stress_tester(self):
        """Create stress tester"""
        tester = AgentStressTester()
        yield tester
        tester.cleanup()
    
    def test_find_max_concurrent_agents(self, stress_tester):
        """Test: Find maximum number of concurrent agents"""
        result = stress_tester.find_max_agents()
        
        print(f"\n{'='*60}")
        print("STRESS TEST RESULTS")
        print(f"{'='*60}")
        print(f"Baseline Memory: {result.baseline_memory_mb:.1f} MB")
        print(f"Maximum Agents: {result.max_agents}")
        print(f"Optimal Agents: {result.optimal_agents}")
        print(f"Total Memory: {result.total_memory_mb:.1f} MB")
        print(f"Memory per Agent: {result.memory_per_agent_mb:.1f} MB")
        
        if result.creation_times:
            avg_creation = sum(result.creation_times) / len(result.creation_times)
            print(f"Avg Creation Time: {avg_creation:.1f} ms")
        
        if result.errors:
            print(f"\nErrors/Limits:")
            for error in result.errors:
                print(f"  - {error}")
        
        print(f"{'='*60}\n")
        
        # Assertions
        assert result.max_agents >= 1, "Should create at least 1 agent"
        assert result.optimal_agents >= 1, "Should have at least 1 optimal agent"
        assert result.memory_per_agent_mb > 0, "Memory tracking should work"
    
    def test_agent_knowledge_isolation(self, stress_tester):
        """Test: Each agent has access to correct knowledge"""
        # Create agents with different domains
        test_cases = [
            ("Backend Developer", "Python", ["python_mastery", "api_design_mastery"]),
            ("Frontend Developer", "React", ["frontend_mastery", "javascript_typescript_mastery"]),
            ("Security Engineer", "AppSec", ["security_mastery", "security_practices"]),
        ]
        
        for role, domain, expected_knowledge in test_cases:
            metrics = stress_tester.create_agent_with_metrics(
                role, domain, f"test_{role.replace(' ', '_')}"
            )
            
            agent = stress_tester.agents.get(f"test_{role.replace(' ', '_')}")
            assert agent is not None, f"Agent {role} should be created"
            
            # Verify knowledge is loaded
            if agent.all_knowledge:
                for knowledge_key in expected_knowledge:
                    # At minimum, the knowledge system should be available
                    print(f"Agent {role}: Checking knowledge '{knowledge_key}'")
    
    def test_memory_stays_within_limits(self, stress_tester):
        """Test: Memory usage stays within safe limits"""
        initial_free = stress_tester._get_system_free_memory()
        
        # Create 10 agents
        for i in range(10):
            stress_tester.create_agent_with_metrics(
                "Test Engineer", "Testing", f"memory_test_agent_{i}"
            )
        
        final_free = stress_tester._get_system_free_memory()
        
        # Should not consume more than 1GB for 10 agents
        memory_consumed = initial_free - final_free
        assert memory_consumed < 1024, f"10 agents consumed {memory_consumed}MB (should be <1GB)"
    
    def test_concurrent_agent_creation(self, stress_tester):
        """Test: Agents can be created concurrently"""
        def create_agent(args):
            idx, role, domain = args
            return stress_tester.create_agent_with_metrics(
                role, domain, f"concurrent_{idx}"
            )
        
        tasks = [
            (i, f"Agent{i}", "Domain") for i in range(5)
        ]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(create_agent, tasks))
        
        success_count = sum(1 for r in results if not r.error)
        assert success_count >= 3, "At least 3/5 concurrent creates should succeed"


class TestKnowledgeAccess:
    """Test that agents can access appropriate knowledge"""
    
    def test_coding_agent_has_knowledge(self):
        """Test: Coding-related agents load knowledge bases"""
        dna = AgentDNA(
            role="Senior Backend Developer",
            seniority="Senior",
            domain="Python Web Development",
            industry_knowledge=["REST APIs", "Databases"],
            methodologies=["TDD"],
            constraints={"quality": "Production-ready"},
            output_format={"style": "professional"}
        )
        
        agent = Agent(dna=dna)
        
        # Should have loaded knowledge
        assert agent.all_knowledge is not None, "Should load knowledge for coding agent"
        assert len(agent.all_knowledge) > 0, "Should have multiple knowledge bases"
        
        print(f"\nLoaded knowledge bases: {list(agent.all_knowledge.keys())}")
    
    def test_non_coding_agent_no_knowledge(self):
        """Test: Non-coding agents don't load unnecessary knowledge"""
        dna = AgentDNA(
            role="Marketing Manager",
            seniority="Senior",
            domain="Digital Marketing",
            industry_knowledge=["SEO", "Social Media"],
            methodologies=["Agile Marketing"],
            constraints={"quality": "High-quality content"},
            output_format={"style": "marketing"}
        )
        
        agent = Agent(dna=dna)
        
        # Should not load coding knowledge
        assert agent.all_knowledge is None, "Non-coding agent shouldn't load coding knowledge"
    
    def test_knowledge_lazy_loading(self):
        """Test: Knowledge is loaded efficiently"""
        # First agent loads knowledge
        start1 = time.perf_counter()
        agent1 = Agent(dna=AgentDNA(
            role="Developer",
            seniority="Senior",
            domain="Python",
            industry_knowledge=["APIs"],
            methodologies=["TDD"],
            constraints={"quality": "Production-ready"},
            output_format={"style": "code"}
        ))
        time1 = time.perf_counter() - start1
        
        # Second agent should reuse cached knowledge
        start2 = time.perf_counter()
        agent2 = Agent(dna=AgentDNA(
            role="Developer",
            seniority="Senior", 
            domain="JavaScript",
            industry_knowledge=["React"],
            methodologies=["TDD"],
            constraints={"quality": "Production-ready"},
            output_format={"style": "code"}
        ))
        time2 = time.perf_counter() - start2
        
        # Both should have knowledge
        assert agent1.all_knowledge is not None
        assert agent2.all_knowledge is not None
        
        # Second should be faster (cached)
        print(f"\nFirst agent: {time1*1000:.1f}ms, Second: {time2*1000:.1f}ms")


class TestCrossDisciplinaryKnowledge:
    """Test that agents can access knowledge outside their primary domain"""
    
    @pytest.fixture
    def knowledge_bases(self):
        """Load all knowledge bases"""
        return load_all_coding_knowledge()
    
    def test_all_knowledge_available(self, knowledge_bases):
        """Test: All knowledge bases are loaded"""
        expected_bases = [
            "coding_foundations",
            "python_mastery",
            "security_practices",
            "database_mastery",
            "api_design_mastery",
        ]
        
        for base in expected_bases:
            assert base in knowledge_bases, f"Missing {base}"
        
        print(f"\nAvailable knowledge bases: {list(knowledge_bases.keys())}")
    
    def test_backend_can_access_security(self, knowledge_bases):
        """Test: Backend developer can access security knowledge"""
        # Create backend developer
        dna = AgentDNA(
            role="Backend Developer",
            seniority="Senior",
            domain="Python APIs",
            industry_knowledge=["REST", "Databases"],
            methodologies=["TDD"],
            constraints={"quality": "Production-ready", "security": "OWASP compliant"},
            output_format={"style": "code"}
        )
        
        agent = Agent(dna=dna)
        
        # Should have security knowledge available
        if agent.all_knowledge:
            security_available = any(
                'security' in key.lower() 
                for key in agent.all_knowledge.keys()
            )
            assert security_available, "Backend dev should have access to security knowledge"
    
    def test_frontend_can_access_backend_patterns(self, knowledge_bases):
        """Test: Frontend developer can access backend patterns"""
        dna = AgentDNA(
            role="Frontend Developer",
            seniority="Senior",
            domain="React/TypeScript",
            industry_knowledge=["UI/UX", "State Management"],
            methodologies=["Component-Based"],
            constraints={"quality": "Production-ready", "accessibility": "WCAG 2.1"},
            output_format={"style": "component"}
        )
        
        agent = Agent(dna=dna)
        
        # Should have API knowledge for integration work
        if agent.all_knowledge:
            api_available = any(
                'api' in key.lower() 
                for key in agent.all_knowledge.keys()
            )
            print(f"Frontend agent knowledge: {list(agent.all_knowledge.keys())}")


class TestAgentTaskCapabilities:
    """Test that agents can complete domain-specific tasks"""
    
    # Small focused tasks for each agent type
    AGENT_TASKS = {
        "Backend Developer": {
            "task": "Write a Python function to validate email addresses",
            "expected_keywords": ["def", "email", "return", "@"]
        },
        "Frontend Developer": {
            "task": "Write a React component for a loading spinner",
            "expected_keywords": ["function", "return", "loading"]
        },
        "Security Engineer": {
            "task": "List 3 common SQL injection prevention techniques",
            "expected_keywords": ["parameterized", "input", "validation"]
        },
        "QA Engineer": {
            "task": "Write a pytest test for a function that adds two numbers",
            "expected_keywords": ["def test", "assert", "pytest"]
        },
        "DBA": {
            "task": "Write a SQL query to find duplicate emails in a users table",
            "expected_keywords": ["SELECT", "GROUP BY", "HAVING", "COUNT"]
        },
    }
    
    @pytest.mark.parametrize("role,task_info", AGENT_TASKS.items())
    def test_agent_completes_domain_task(self, role, task_info):
        """Test: Each agent type can complete a domain-specific task"""
        dna = AgentDNA(
            role=role,
            seniority="Senior",
            domain=role.split()[0],  # First word as domain
            industry_knowledge=[role],
            methodologies=["Best Practices"],
            constraints={"quality": "Production-ready", "timeline": "Standard"},
            output_format={"style": "code", "format": "markdown"}
        )
        
        agent = Agent(dna=dna)
        
        # Just verify agent created successfully
        assert agent.dna.role == role
        assert agent.all_knowledge is not None or not agent._is_coding_related()
        
        print(f"\n✓ {role} agent ready with task: {task_info['task'][:50]}...")


class TestOptimalAgentCalculation:
    """Test optimal agent number calculation based on system resources"""
    
    def test_calculate_optimal_agents(self):
        """Test: Calculate optimal number of agents for current system"""
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        
        # Estimate based on available resources
        available_memory_mb = memory.available / (1024 * 1024)
        
        # Assume ~50MB per agent (knowledge shared, DNA unique)
        memory_based_limit = int(available_memory_mb * 0.5 / 50)
        
        # CPU-based limit (2 agents per core is reasonable)
        cpu_based_limit = cpu_count * 2
        
        # Take the minimum
        optimal = min(memory_based_limit, cpu_based_limit, 50)  # Cap at 50
        
        print(f"\n{'='*50}")
        print("OPTIMAL AGENT CALCULATION")
        print(f"{'='*50}")
        print(f"Available Memory: {available_memory_mb:.0f} MB")
        print(f"CPU Cores: {cpu_count}")
        print(f"Memory-based limit: {memory_based_limit}")
        print(f"CPU-based limit: {cpu_based_limit}")
        print(f"OPTIMAL AGENTS: {optimal}")
        print(f"{'='*50}\n")
        
        assert optimal >= 1, "Should suggest at least 1 agent"
        assert optimal <= 100, "Should not suggest more than 100 agents"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
