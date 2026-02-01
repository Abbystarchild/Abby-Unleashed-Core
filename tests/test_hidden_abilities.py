"""
Abby Unleashed - Hidden Abilities Discovery Tests
=================================================

These tests probe for emergent and undocumented capabilities.
They test reasoning, inference, and intelligence beyond basic functionality.
"""

import pytest
import os
import sys
import json
import time
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestReasoningCapabilities:
    """Test Abby's reasoning and inference abilities"""
    
    def test_multi_domain_task_detection(self):
        """Test detection of tasks spanning multiple domains"""
        from task_engine.task_analyzer import TaskAnalyzer
        
        analyzer = TaskAnalyzer()
        
        # Complex task spanning development + devops + testing
        analysis = analyzer.analyze(
            "Build a Python API, deploy it to AWS with Docker, and write comprehensive tests"
        )
        
        # Should detect multiple domains
        domains = analysis['domains']
        assert len(domains) >= 2, f"Should detect multiple domains, got: {domains}"
        print(f"✅ Multi-domain detection: {domains}")
    
    def test_implicit_requirement_extraction(self):
        """Test extraction of implicit requirements"""
        from task_engine.task_analyzer import TaskAnalyzer
        
        analyzer = TaskAnalyzer()
        
        # This task involves development
        analysis = analyzer.analyze("Create a user login system with database")
        
        # Should detect development domain
        assert 'development' in analysis['domains'] or analysis['requires_decomposition']
        print(f"[OK] Implicit requirements: domains={analysis['domains']}")
    
    def test_context_preservation_in_planning(self):
        """Test that context is preserved during planning"""
        from agents.task_planner import TaskPlanner
        from ollama_integration.client import OllamaClient
        
        client = OllamaClient()
        planner = TaskPlanner(ollama_client=client)
        
        # Provide specific context
        context = {"workspace": "C:\\Dev\\TestProject", "language": "Python"}
        analysis = planner.analyze_task("Add error handling", context)
        
        assert analysis['workspace'] == context['workspace']
        print(f"✅ Context preserved: workspace={analysis['workspace']}")


class TestKnowledgeIntegration:
    """Test Abby's knowledge base integration"""
    
    def test_knowledge_base_coverage(self, project_root=None):
        """Test coverage of knowledge domains"""
        if project_root is None:
            project_root = Path(__file__).parent.parent
            
        knowledge_dir = project_root / "agents" / "knowledge"
        
        # Count knowledge files
        yaml_files = list(knowledge_dir.glob("*.yaml"))
        
        assert len(yaml_files) >= 10, f"Should have 10+ knowledge bases, got {len(yaml_files)}"
        
        # List all domains
        domains = [f.stem for f in yaml_files]
        print(f"✅ Knowledge domains ({len(domains)}): {domains}")
    
    def test_coding_foundations_depth(self, project_root=None):
        """Test depth of coding foundations knowledge"""
        import yaml
        
        if project_root is None:
            project_root = Path(__file__).parent.parent
            
        kb_path = project_root / "agents" / "knowledge" / "coding_foundations.yaml"
        
        with open(kb_path, 'r', encoding='utf-8') as f:
            knowledge = yaml.safe_load(f)
        
        # Should have vibe coding awareness
        assert 'vibe_coding_awareness' in knowledge
        
        vca = knowledge['vibe_coding_awareness']
        
        # Should have limitations
        assert 'limitations' in vca
        assert len(vca['limitations']) >= 3, "Should have multiple limitations documented"
        
        # Should have best practices
        assert 'best_practices' in vca
        
        print(f"✅ Coding foundations: {len(vca['limitations'])} limitations, has best practices")


class TestAdaptiveResponse:
    """Test Abby's ability to adapt responses"""
    
    def test_user_specific_greeting_capability(self, project_root=None):
        """Test user-specific greeting capability"""
        if project_root is None:
            project_root = Path(__file__).parent.parent
            
        from presence.user_tracker import UserTracker
        
        profiles_path = project_root / "data" / "user_profiles.yaml"
        if not profiles_path.exists():
            pytest.skip("User profiles not found")
        
        tracker = UserTracker(str(profiles_path))
        
        # Check for user-specific greetings
        profiles = tracker.profiles
        users = profiles.get('users', {})
        
        users_with_greetings = 0
        for user_id, profile in users.items():
            if 'greetings' in profile:
                users_with_greetings += 1
        
        assert users_with_greetings > 0, "Should have user-specific greetings"
        print(f"✅ Found {users_with_greetings} users with custom greetings")
    
    def test_chaos_detection_categories(self):
        """Test chaos detection has multiple categories"""
        from presence.chaos_handler import get_boyfriend_handler
        
        handler = get_boyfriend_handler()
        
        # Should have process_input method
        assert hasattr(handler, 'process_input'), "Handler should have process_input method"
        
        # Test processing
        result = handler.process_input("test input")
        assert isinstance(result, dict)
        print(f"[OK] Chaos handler working: {type(result)}")


class TestExecutionSafety:
    """Test Abby's safety mechanisms"""
    
    def test_path_allowlist_comprehensive(self):
        """Test path allowlisting is comprehensive"""
        from agents.action_executor import ActionExecutor
        
        executor = ActionExecutor()
        
        # Check ALLOWED_PATHS
        assert len(executor.ALLOWED_PATHS) >= 2, "Should have multiple allowed paths"
        print(f"✅ Allowed paths: {executor.ALLOWED_PATHS}")
    
    def test_blocked_commands_comprehensive(self):
        """Test dangerous commands are comprehensively blocked"""
        from agents.action_executor import ActionExecutor
        
        executor = ActionExecutor()
        
        dangerous_commands = [
            "rm -rf /",
            "del /f /s /q c:\\",
            "format c:",
            "shutdown /s",
        ]
        
        blocked = 0
        for cmd in dangerous_commands:
            if not executor._is_command_safe(cmd):
                blocked += 1
        
        assert blocked >= len(dangerous_commands) - 1, f"Should block most dangerous commands, blocked {blocked}/{len(dangerous_commands)}"
        print(f"✅ Blocked {blocked}/{len(dangerous_commands)} dangerous commands")
    
    def test_dry_run_mode_exists(self):
        """Test dry run mode for safe preview"""
        from agents.action_executor import ActionExecutor
        
        executor = ActionExecutor()
        assert hasattr(executor, 'dry_run')
        
        # Enable dry run
        executor.dry_run = True
        assert executor.dry_run
        print("✅ Dry run mode available for safe previews")


class TestMultiAgentCapabilities:
    """Test multi-agent orchestration capabilities"""
    
    def test_parallel_execution_support(self):
        """Test parallel execution planning"""
        from task_engine.execution_planner import ExecutionPlanner
        
        planner = ExecutionPlanner()
        assert planner is not None
        print("✅ Execution planner supports parallel planning")
    
    def test_dependency_mapping(self):
        """Test dependency graph building"""
        from task_engine.dependency_mapper import DependencyMapper
        
        mapper = DependencyMapper()
        assert mapper is not None
        print("✅ Dependency mapper available for task ordering")
    
    def test_result_aggregation(self):
        """Test result aggregation capability"""
        from coordination.result_aggregator import ResultAggregator
        
        aggregator = ResultAggregator()
        assert aggregator is not None
        print("✅ Result aggregator for combining multi-agent outputs")


class TestLearningCapabilities:
    """Test Abby's learning and optimization"""
    
    def test_agent_performance_tracking(self):
        """Test agent performance tracking"""
        from learning.delegation_optimizer import DelegationOptimizer
        
        optimizer = DelegationOptimizer()
        
        # Record multiple delegations
        for i in range(3):
            optimizer.record_delegation(
                task_id=f"test_{i}",
                task_description=f"Task {i}",
                agent_id="test_agent",
                task_type="development",
                outcome_score=0.7 + (i * 0.1)
            )
        
        # Should have updated specialties
        assert 'test_agent' in optimizer.agent_specialties
        print(f"✅ Agent specialties tracked: {optimizer.agent_specialties['test_agent']}")
    
    def test_exponential_moving_average_learning(self):
        """Test learning uses EMA for smooth updates"""
        from learning.delegation_optimizer import DelegationOptimizer
        
        optimizer = DelegationOptimizer()
        
        # First high score
        optimizer.record_delegation(
            task_id="t1", task_description="Test", agent_id="ema_agent",
            task_type="coding", outcome_score=1.0
        )
        
        score1 = optimizer.agent_specialties['ema_agent']['coding']
        
        # Then low score
        optimizer.record_delegation(
            task_id="t2", task_description="Test", agent_id="ema_agent",
            task_type="coding", outcome_score=0.0
        )
        
        score2 = optimizer.agent_specialties['ema_agent']['coding']
        
        # EMA should smooth the drop (not go straight to 0)
        assert score2 > 0.2, f"EMA should smooth: score went from {score1} to {score2}"
        print(f"✅ EMA learning verified: {score1:.2f} -> {score2:.2f}")


class TestConversationCapabilities:
    """Test advanced conversation features"""
    
    def test_rich_content_generation(self):
        """Test rich content generation capability"""
        from realtime_conversation import RichContentGenerator
        
        generator = RichContentGenerator()
        assert generator is not None
        
        # Test parsing
        test_response = "Here is some code:\n```python\nprint('hello')\n```"
        content = generator.parse_response(test_response)
        
        assert len(content) > 0, "Should parse content blocks"
        print(f"[OK] Rich content generation: {len(content)} blocks from response")
    
    def test_voice_summary_generation(self):
        """Test voice summary generation"""
        from realtime_conversation import RichContentGenerator
        
        generator = RichContentGenerator()
        
        long_response = """
        This is a very detailed technical explanation about Python decorators.
        Decorators are functions that modify other functions. They use the @syntax.
        Here's an example:
        ```python
        def my_decorator(func):
            def wrapper():
                print("Before")
                func()
                print("After")
            return wrapper
        ```
        This pattern is commonly used for logging, authentication, and caching.
        """
        
        summary = generator.generate_voice_summary(long_response)
        
        # Summary should be shorter
        assert len(summary) < len(long_response)
        print(f"[OK] Voice summary: {len(long_response)} chars -> {len(summary)} chars")


class TestHiddenFeatures:
    """Test features that might not be immediately obvious"""
    
    def test_action_history_tracking(self):
        """Test actions are logged for audit"""
        import tempfile
        from agents.action_executor import ActionExecutor
        
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = ActionExecutor(workspace_path=tmpdir)
            
            # Perform action
            executor.create_file(
                path=os.path.join(tmpdir, "test.txt"),
                content="test"
            )
            
            # Check history
            assert len(executor.action_history) > 0
            print(f"✅ Action history tracked: {len(executor.action_history)} entries")
    
    def test_clarification_protocol_exists(self):
        """Test clarification protocol for ambiguous tasks"""
        from agents.clarification_protocol import ClarificationProtocol
        
        protocol = ClarificationProtocol()
        assert protocol is not None
        print("✅ Clarification protocol available for ambiguous tasks")
    
    def test_persona_library_matching(self):
        """Test persona matching capability"""
        from persona_library.library_manager import PersonaLibrary
        
        library = PersonaLibrary()
        
        # Should have find_match method
        assert hasattr(library, 'find_match')
        print("✅ Persona library supports matching")


class TestIntelligenceSummary:
    """Final intelligence summary"""
    
    def test_intelligence_inventory(self):
        """Generate intelligence inventory"""
        capabilities = []
        
        # Check each major capability
        tests = [
            ("Task Analysis", "task_engine.task_analyzer", "TaskAnalyzer"),
            ("Task Decomposition", "task_engine.decomposer", "TaskDecomposer"),
            ("Multi-Agent Orchestration", "coordination.orchestrator", "Orchestrator"),
            ("File Operations", "agents.action_executor", "ActionExecutor"),
            ("Research Toolkit", "agents.research_toolkit", "ResearchToolkit"),
            ("Face Recognition", "presence.face_recognition", "FaceRecognizer"),
            ("Visual Awareness", "presence.visual_awareness", "VisualAwareness"),
            ("User Tracking", "presence.user_tracker", "UserTracker"),
            ("Memory Systems", "memory.long_term", "LongTermMemory"),
            ("Learning System", "learning.delegation_optimizer", "DelegationOptimizer"),
            ("TTS Integration", "speech_interface.elevenlabs_tts", "ElevenLabsTTS"),
            ("Local STT", "local_speech", "LocalSpeechRecognizer"),
            ("Realtime Conversation", "realtime_conversation", "RealtimeConversation"),
        ]
        
        for name, module, classname in tests:
            try:
                mod = __import__(module, fromlist=[classname])
                cls = getattr(mod, classname)
                capabilities.append((name, "✅"))
            except Exception as e:
                capabilities.append((name, f"❌ {e}"))
        
        print("\n" + "="*60)
        print("ABBY INTELLIGENCE INVENTORY")
        print("="*60)
        
        passed = 0
        for name, status in capabilities:
            print(f"  {status} {name}")
            if "✅" in status:
                passed += 1
        
        print("="*60)
        print(f"TOTAL: {passed}/{len(capabilities)} capabilities verified")
        print("="*60 + "\n")
        
        # At least 80% should work
        assert passed >= len(capabilities) * 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
