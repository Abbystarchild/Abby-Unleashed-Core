"""
Tests for memory and learning systems (Phase 4)
"""
import pytest
import os
import tempfile
import shutil
from memory.short_term import ShortTermMemory
from memory.working_memory import WorkingMemory
from memory.long_term import LongTermMemory
from learning.outcome_evaluator import OutcomeEvaluator
from learning.delegation_optimizer import DelegationOptimizer


class TestShortTermMemory:
    """Test short-term memory"""
    
    def test_init(self):
        """Test initialization"""
        memory = ShortTermMemory(max_turns=5)
        assert memory.max_turns == 5
        assert len(memory.turns) == 0
    
    def test_add_turn(self):
        """Test adding conversation turns"""
        memory = ShortTermMemory()
        memory.add_turn("user", "Hello")
        memory.add_turn("assistant", "Hi there!")
        
        assert len(memory.turns) == 2
        assert memory.turns[0].role == "user"
        assert memory.turns[0].content == "Hello"
    
    def test_max_turns_limit(self):
        """Test maximum turns limit"""
        memory = ShortTermMemory(max_turns=3)
        
        for i in range(5):
            memory.add_turn("user", f"Message {i}")
        
        assert len(memory.turns) == 3
        # Should keep only last 3
        assert memory.turns[0].content == "Message 2"
    
    def test_get_recent_turns(self):
        """Test getting recent turns"""
        memory = ShortTermMemory()
        memory.add_turn("user", "Message 1")
        memory.add_turn("assistant", "Reply 1")
        memory.add_turn("user", "Message 2")
        
        recent = memory.get_recent_turns(2)
        assert len(recent) == 2
        assert recent[0].content == "Reply 1"
    
    def test_get_context_string(self):
        """Test formatted context string"""
        memory = ShortTermMemory()
        memory.add_turn("user", "Hello")
        memory.add_turn("assistant", "Hi")
        
        context = memory.get_context_string()
        assert "USER: Hello" in context
        assert "ASSISTANT: Hi" in context
    
    def test_get_messages_for_llm(self):
        """Test LLM message format"""
        memory = ShortTermMemory()
        memory.add_turn("user", "Hello")
        memory.add_turn("assistant", "Hi")
        
        messages = memory.get_messages_for_llm()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
    
    def test_clear(self):
        """Test clearing memory"""
        memory = ShortTermMemory()
        memory.add_turn("user", "Hello")
        memory.clear()
        
        assert len(memory.turns) == 0


class TestWorkingMemory:
    """Test working memory"""
    
    def test_init(self):
        """Test initialization"""
        memory = WorkingMemory()
        assert len(memory.active_tasks) == 0
        assert len(memory.scratch_pad) == 0
    
    def test_register_task(self):
        """Test registering tasks"""
        memory = WorkingMemory()
        memory.register_task("task1", "Do something", "agent1")
        
        assert "task1" in memory.active_tasks
        assert "agent1" in memory.active_agents
    
    def test_task_lifecycle(self):
        """Test task lifecycle"""
        memory = WorkingMemory()
        memory.register_task("task1", "Test", "agent1")
        memory.update_task_status("task1", "in_progress")
        
        task = memory.get_task("task1")
        assert task["status"] == "in_progress"
        
        memory.complete_task("task1")
        assert "task1" not in memory.active_tasks
    
    def test_intermediate_results(self):
        """Test intermediate results"""
        memory = WorkingMemory()
        memory.store_intermediate_result("key1", {"data": "value"}, "task1")
        
        result = memory.get_intermediate_result("key1")
        assert result["data"] == "value"
    
    def test_scratch_pad(self):
        """Test scratch pad"""
        memory = WorkingMemory()
        memory.set_scratch("temp", "data")
        
        assert memory.get_scratch("temp") == "data"
        
        memory.clear_scratch()
        assert memory.get_scratch("temp") is None
    
    def test_get_tasks_by_agent(self):
        """Test filtering tasks by agent"""
        memory = WorkingMemory()
        memory.register_task("task1", "Task 1", "agent1")
        memory.register_task("task2", "Task 2", "agent2")
        memory.register_task("task3", "Task 3", "agent1")
        
        agent1_tasks = memory.get_tasks_by_agent("agent1")
        assert len(agent1_tasks) == 2


class TestLongTermMemory:
    """Test long-term memory"""
    
    def setup_method(self):
        """Create temporary storage for tests"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary storage"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test initialization"""
        memory = LongTermMemory(storage_path=self.temp_dir)
        assert memory.storage_path.exists()
    
    def test_store_conversation(self):
        """Test storing conversations"""
        memory = LongTermMemory(storage_path=self.temp_dir)
        
        turns = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]
        
        memory.store_conversation("conv1", turns)
        assert len(memory.conversations) == 1
    
    def test_store_task_outcome(self):
        """Test storing task outcomes"""
        memory = LongTermMemory(storage_path=self.temp_dir)
        
        memory.store_task_outcome(
            "task1",
            "Test task",
            {"output": "result"},
            "agent1",
            success=True
        )
        
        assert len(memory.tasks) == 1
    
    def test_store_learning(self):
        """Test storing learnings"""
        memory = LongTermMemory(storage_path=self.temp_dir)
        
        memory.store_learning(
            "pattern",
            "Users often ask about X",
            "conversation_analysis"
        )
        
        assert len(memory.learnings) == 1
    
    def test_get_task_outcomes(self):
        """Test retrieving task outcomes"""
        memory = LongTermMemory(storage_path=self.temp_dir)
        
        memory.store_task_outcome("task1", "Task 1", {}, "agent1", True)
        memory.store_task_outcome("task2", "Task 2", {}, "agent2", False)
        
        outcomes = memory.get_task_outcomes(success_only=True)
        assert len(outcomes) == 1
    
    def test_persistence(self):
        """Test data persistence"""
        # Store data
        memory1 = LongTermMemory(storage_path=self.temp_dir)
        memory1.store_conversation("conv1", [{"role": "user", "content": "Hello"}])
        
        # Load data in new instance
        memory2 = LongTermMemory(storage_path=self.temp_dir)
        assert len(memory2.conversations) == 1


class TestOutcomeEvaluator:
    """Test outcome evaluator"""
    
    def test_init(self):
        """Test initialization"""
        evaluator = OutcomeEvaluator()
        assert len(evaluator.evaluation_history) == 0
    
    def test_evaluate_task_outcome(self):
        """Test task outcome evaluation"""
        evaluator = OutcomeEvaluator()
        
        result = {"status": "completed", "output": "Result data"}
        
        evaluation = evaluator.evaluate_task_outcome(
            "task1",
            "Test task",
            result,
            "agent1"
        )
        
        assert evaluation["success"] is True
        assert 0 <= evaluation["overall_score"] <= 1
    
    def test_get_agent_performance(self):
        """Test agent performance metrics"""
        evaluator = OutcomeEvaluator()
        
        # Add multiple evaluations
        for i in range(5):
            evaluator.evaluate_task_outcome(
                f"task{i}",
                "Test",
                {"status": "completed", "output": "data"},
                "agent1"
            )
        
        performance = evaluator.get_agent_performance("agent1")
        assert performance["total_tasks"] == 5
        assert "success_rate" in performance
    
    def test_identify_patterns(self):
        """Test pattern identification"""
        evaluator = OutcomeEvaluator()
        
        # Add high-performing evaluations
        for i in range(5):
            evaluator.evaluate_task_outcome(
                f"task{i}",
                "Test",
                {"status": "completed", "output": "excellent result"},
                "agent1"
            )
        
        patterns = evaluator.identify_patterns()
        assert len(patterns) > 0


class TestDelegationOptimizer:
    """Test delegation optimizer"""
    
    def test_init(self):
        """Test initialization"""
        optimizer = DelegationOptimizer()
        assert len(optimizer.delegation_history) == 0
    
    def test_record_delegation(self):
        """Test recording delegations"""
        optimizer = DelegationOptimizer()
        
        optimizer.record_delegation(
            "task1",
            "Build API",
            "agent1",
            "development",
            0.8
        )
        
        assert len(optimizer.delegation_history) == 1
        assert "agent1" in optimizer.agent_specialties
    
    def test_recommend_agent(self):
        """Test agent recommendation"""
        optimizer = DelegationOptimizer()
        
        # Record successful delegation
        optimizer.record_delegation(
            "task1",
            "Build API",
            "agent1",
            "development",
            0.9
        )
        
        # Should recommend agent1 for development
        recommended = optimizer.recommend_agent("development", ["agent1", "agent2"])
        assert recommended == "agent1"
    
    def test_get_top_performers(self):
        """Test getting top performers"""
        optimizer = DelegationOptimizer()
        
        optimizer.record_delegation("t1", "Task", "agent1", "dev", 0.9)
        optimizer.record_delegation("t2", "Task", "agent2", "dev", 0.7)
        
        top = optimizer.get_top_performers("dev", top_n=2)
        assert len(top) == 2
        assert top[0]["agent_id"] == "agent1"  # Higher score
    
    def test_analyze_delegation_patterns(self):
        """Test delegation pattern analysis"""
        optimizer = DelegationOptimizer()
        
        # Add multiple delegations
        for i in range(5):
            optimizer.record_delegation(
                f"task{i}",
                "Test",
                "agent1",
                "development",
                0.8
            )
        
        analysis = optimizer.analyze_delegation_patterns()
        assert "total_delegations" in analysis
        assert analysis["total_delegations"] == 5
    
    def test_generate_optimization_suggestions(self):
        """Test optimization suggestions"""
        optimizer = DelegationOptimizer()
        
        # Add enough data
        for i in range(10):
            optimizer.record_delegation(
                f"task{i}",
                "Test",
                "agent1",
                "development",
                0.9
            )
        
        suggestions = optimizer.generate_optimization_suggestions()
        assert len(suggestions) > 0
        assert isinstance(suggestions[0], str)
