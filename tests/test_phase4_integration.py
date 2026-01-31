"""
Integration tests for Phase 4 systems
Tests the integration of memory and learning systems with the orchestrator
"""
import pytest
from coordination.orchestrator import Orchestrator
from agents.agent_factory import AgentFactory
from persona_library.library_manager import PersonaLibrary
from personality.brain_clone import BrainClone


class TestPhase4Integration:
    """Test Phase 4 memory and learning integration"""
    
    def setup_method(self):
        """Setup test dependencies"""
        # Initialize components needed for orchestrator
        self.persona_library = PersonaLibrary()
        self.brain_clone = BrainClone()
        self.agent_factory = AgentFactory(
            persona_library=self.persona_library,
            personality=self.brain_clone.get_personality()
        )
    
    def test_orchestrator_with_memory_enabled(self):
        """Test orchestrator with memory systems enabled"""
        orchestrator = Orchestrator(
            agent_factory=self.agent_factory,
            enable_memory=True,
            enable_learning=False
        )
        orchestrator.start()
        
        # Verify memory systems are initialized
        assert orchestrator.enable_memory is True
        assert orchestrator.short_term_memory is not None
        assert orchestrator.working_memory is not None
        assert orchestrator.long_term_memory is not None
        
        # Get progress with memory stats
        progress = orchestrator.get_progress()
        assert "memory_stats" in progress
        assert "short_term" in progress["memory_stats"]
        assert "working" in progress["memory_stats"]
        assert "long_term" in progress["memory_stats"]
        
        orchestrator.stop()
        orchestrator.cleanup()
    
    def test_orchestrator_with_learning_enabled(self):
        """Test orchestrator with learning systems enabled"""
        orchestrator = Orchestrator(
            agent_factory=self.agent_factory,
            enable_memory=False,
            enable_learning=True
        )
        orchestrator.start()
        
        # Verify learning systems are initialized
        assert orchestrator.enable_learning is True
        assert orchestrator.outcome_evaluator is not None
        assert orchestrator.delegation_optimizer is not None
        
        # Get progress with learning stats
        progress = orchestrator.get_progress()
        assert "learning_stats" in progress
        
        orchestrator.stop()
        orchestrator.cleanup()
    
    def test_orchestrator_with_full_phase4(self):
        """Test orchestrator with all Phase 4 systems enabled"""
        orchestrator = Orchestrator(
            agent_factory=self.agent_factory,
            enable_memory=True,
            enable_learning=True
        )
        orchestrator.start()
        
        # Verify both systems are initialized
        assert orchestrator.enable_memory is True
        assert orchestrator.enable_learning is True
        assert orchestrator.short_term_memory is not None
        assert orchestrator.working_memory is not None
        assert orchestrator.long_term_memory is not None
        assert orchestrator.outcome_evaluator is not None
        assert orchestrator.delegation_optimizer is not None
        
        # Get complete progress with all stats
        progress = orchestrator.get_progress()
        assert "memory_stats" in progress
        assert "learning_stats" in progress
        
        # Get learning insights
        insights = orchestrator.get_learning_insights()
        assert insights is not None
        
        orchestrator.stop()
        orchestrator.cleanup()
    
    def test_memory_systems_independent(self):
        """Test that memory systems work independently"""
        from memory.short_term import ShortTermMemory
        from memory.working_memory import WorkingMemory
        from memory.long_term import LongTermMemory
        
        # Test short-term memory
        stm = ShortTermMemory(max_turns=5)
        stm.add_turn("user", "Hello")
        stm.add_turn("assistant", "Hi there")
        assert len(stm.turns) == 2
        
        # Test working memory
        wm = WorkingMemory()
        wm.register_task("task1", "Test task", "agent1")
        assert "task1" in wm.active_tasks
        
        # Test long-term memory
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            ltm = LongTermMemory(storage_path=temp_dir)
            ltm.store_task_outcome("task1", "Test", {}, "agent1", True)
            assert len(ltm.tasks) == 1
    
    def test_learning_systems_independent(self):
        """Test that learning systems work independently"""
        from learning.outcome_evaluator import OutcomeEvaluator
        from learning.delegation_optimizer import DelegationOptimizer
        
        # Test outcome evaluator
        evaluator = OutcomeEvaluator()
        result = {"status": "completed", "output": "Result"}
        evaluation = evaluator.evaluate_task_outcome(
            "task1", "Test", result, "agent1"
        )
        assert "success" in evaluation
        assert "overall_score" in evaluation
        
        # Test delegation optimizer
        optimizer = DelegationOptimizer()
        optimizer.record_delegation(
            "task1", "Test", "agent1", "development", 0.9
        )
        assert len(optimizer.delegation_history) == 1
    
    def test_orchestrator_memory_disabled(self):
        """Test orchestrator with memory disabled"""
        orchestrator = Orchestrator(
            agent_factory=self.agent_factory,
            enable_memory=False,
            enable_learning=False
        )
        orchestrator.start()
        
        assert orchestrator.enable_memory is False
        assert orchestrator.enable_learning is False
        
        progress = orchestrator.get_progress()
        assert "memory_stats" not in progress
        assert "learning_stats" not in progress
        
        orchestrator.stop()
        orchestrator.cleanup()
