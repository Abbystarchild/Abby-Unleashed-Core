"""
Tests for Task Engine components
"""

import pytest
from task_engine.task_analyzer import TaskAnalyzer, TaskComplexity
from task_engine.decomposer import TaskDecomposer, SubTask
from task_engine.dependency_mapper import DependencyMapper
from task_engine.execution_planner import ExecutionPlanner, TaskStatus


class TestTaskAnalyzer:
    """Tests for TaskAnalyzer."""
    
    def test_simple_task_analysis(self):
        """Test analysis of a simple task."""
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("Create a simple Python function")
        
        assert result['complexity'] == TaskComplexity.SIMPLE
        assert result['requires_decomposition'] is False
        assert 'development' in result['domains']
    
    def test_medium_task_analysis(self):
        """Test analysis of a medium complexity task."""
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("Create and test multiple API endpoints")
        
        assert result['complexity'] == TaskComplexity.MEDIUM
        assert result['requires_decomposition'] is True
        assert 'development' in result['domains']
        assert result['estimated_subtasks'] >= 3
    
    def test_complex_task_analysis(self):
        """Test analysis of a complex task."""
        analyzer = TaskAnalyzer()
        result = analyzer.analyze(
            "Build a complete web application with user authentication, database, and deployment"
        )
        
        assert result['complexity'] == TaskComplexity.COMPLEX
        assert result['requires_decomposition'] is True
        assert len(result['domains']) > 1
        assert result['estimated_subtasks'] >= 5
    
    def test_domain_identification_devops(self):
        """Test identification of DevOps domain."""
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("Deploy application to Kubernetes cluster")
        
        assert 'devops' in result['domains']
    
    def test_domain_identification_data(self):
        """Test identification of data domain."""
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("Analyze sales data and create dashboard")
        
        assert 'data' in result['domains']
    
    def test_multiple_domains(self):
        """Test task with multiple domains."""
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("Build web API, test it, and deploy to cloud")
        
        assert len(result['domains']) >= 2
        assert 'development' in result['domains']
        assert 'devops' in result['domains']


class TestTaskDecomposer:
    """Tests for TaskDecomposer."""
    
    def test_no_decomposition_needed(self):
        """Test task that doesn't need decomposition."""
        decomposer = TaskDecomposer()
        analyzer = TaskAnalyzer()
        
        analysis = analyzer.analyze("Create a simple function")
        result = decomposer.decompose(analysis)
        
        assert len(result['subtasks']) == 1
        assert result['root_task']['id'] == 'task_0'
    
    def test_development_task_decomposition(self):
        """Test decomposition of development task."""
        decomposer = TaskDecomposer()
        analyzer = TaskAnalyzer()
        
        analysis = analyzer.analyze("Build a REST API for user management")
        result = decomposer.decompose(analysis)
        
        assert len(result['subtasks']) > 1
        assert any('test' in task['description'].lower() for task in result['subtasks'])
        assert any('implement' in task['description'].lower() for task in result['subtasks'])
    
    def test_devops_task_decomposition(self):
        """Test decomposition of DevOps task."""
        decomposer = TaskDecomposer()
        analyzer = TaskAnalyzer()
        
        analysis = analyzer.analyze("Deploy web application to AWS")
        result = decomposer.decompose(analysis)
        
        assert len(result['subtasks']) > 1
        assert any('infrastructure' in task['description'].lower() for task in result['subtasks'])
    
    def test_data_task_decomposition(self):
        """Test decomposition of data task."""
        decomposer = TaskDecomposer()
        analyzer = TaskAnalyzer()
        
        analysis = analyzer.analyze("Analyze customer data and create visualization")
        result = decomposer.decompose(analysis)
        
        assert len(result['subtasks']) > 1
        assert any('data' in task['description'].lower() for task in result['subtasks'])
        assert any('visualization' in task['description'].lower() for task in result['subtasks'])
    
    def test_task_dependencies(self):
        """Test that decomposed tasks have proper dependencies."""
        decomposer = TaskDecomposer()
        analyzer = TaskAnalyzer()
        
        analysis = analyzer.analyze("Build and deploy a web application")
        result = decomposer.decompose(analysis)
        
        # Check that tasks have dependencies
        tasks_with_deps = [t for t in result['subtasks'] if t.get('dependencies')]
        assert len(tasks_with_deps) > 0
        
        # Check that first task has no dependencies
        first_task = result['subtasks'][0]
        assert len(first_task.get('dependencies', [])) == 0
    
    def test_task_tree_structure(self):
        """Test that task tree is properly built."""
        decomposer = TaskDecomposer()
        analyzer = TaskAnalyzer()
        
        analysis = analyzer.analyze("Build a complete application")
        result = decomposer.decompose(analysis)
        
        assert 'task_tree' in result
        assert 'task_0' in result['task_tree']


class TestDependencyMapper:
    """Tests for DependencyMapper."""
    
    def test_simple_graph_building(self):
        """Test building a simple dependency graph."""
        mapper = DependencyMapper()
        
        subtasks = [
            {'id': 'task_1', 'dependencies': []},
            {'id': 'task_2', 'dependencies': ['task_1']},
            {'id': 'task_3', 'dependencies': ['task_2']}
        ]
        
        result = mapper.build_graph(subtasks)
        
        assert result['has_cycles'] is False
        assert len(result['execution_order']) == 3
        assert result['execution_order'][0] == 'task_1'
    
    def test_parallel_tasks_detection(self):
        """Test detection of tasks that can run in parallel."""
        mapper = DependencyMapper()
        
        subtasks = [
            {'id': 'task_1', 'dependencies': []},
            {'id': 'task_2', 'dependencies': ['task_1']},
            {'id': 'task_3', 'dependencies': ['task_1']},
            {'id': 'task_4', 'dependencies': ['task_2', 'task_3']}
        ]
        
        result = mapper.build_graph(subtasks)
        
        assert result['has_cycles'] is False
        # task_2 and task_3 should be in the same parallel group
        parallel_groups = result['parallel_groups']
        assert any(set(group) == {'task_2', 'task_3'} for group in parallel_groups)
    
    def test_cycle_detection(self):
        """Test detection of circular dependencies."""
        mapper = DependencyMapper()
        
        subtasks = [
            {'id': 'task_1', 'dependencies': ['task_3']},
            {'id': 'task_2', 'dependencies': ['task_1']},
            {'id': 'task_3', 'dependencies': ['task_2']}
        ]
        
        result = mapper.build_graph(subtasks)
        
        assert result['has_cycles'] is True
        assert 'error' in result
    
    def test_get_ready_tasks(self):
        """Test getting tasks ready to execute."""
        mapper = DependencyMapper()
        
        subtasks = [
            {'id': 'task_1', 'dependencies': []},
            {'id': 'task_2', 'dependencies': ['task_1']},
            {'id': 'task_3', 'dependencies': ['task_1']}
        ]
        
        mapper.build_graph(subtasks)
        
        # Initially, only task_1 should be ready
        ready = mapper.get_ready_tasks(set(), subtasks)
        assert 'task_1' in ready
        assert len(ready) == 1
        
        # After task_1 completes, task_2 and task_3 should be ready
        ready = mapper.get_ready_tasks({'task_1'}, subtasks)
        assert 'task_2' in ready
        assert 'task_3' in ready


class TestExecutionPlanner:
    """Tests for ExecutionPlanner."""
    
    def test_plan_creation(self):
        """Test creation of execution plan."""
        mapper = DependencyMapper()
        planner = ExecutionPlanner()
        
        subtasks = [
            {'id': 'task_1', 'dependencies': [], 'estimated_complexity': 'simple'},
            {'id': 'task_2', 'dependencies': ['task_1'], 'estimated_complexity': 'simple'},
            {'id': 'task_3', 'dependencies': ['task_2'], 'estimated_complexity': 'simple'}
        ]
        
        dep_map = mapper.build_graph(subtasks)
        plan = planner.create_plan(dep_map, subtasks)
        
        assert plan['total_steps'] == 3
        assert 'steps' in plan
        assert plan['can_parallelize'] is False
    
    def test_parallel_execution_plan(self):
        """Test plan with parallel execution."""
        mapper = DependencyMapper()
        planner = ExecutionPlanner()
        
        subtasks = [
            {'id': 'task_1', 'dependencies': [], 'estimated_complexity': 'simple'},
            {'id': 'task_2', 'dependencies': ['task_1'], 'estimated_complexity': 'simple'},
            {'id': 'task_3', 'dependencies': ['task_1'], 'estimated_complexity': 'simple'}
        ]
        
        dep_map = mapper.build_graph(subtasks)
        plan = planner.create_plan(dep_map, subtasks)
        
        assert plan['can_parallelize'] is True
        # Should have step with both task_2 and task_3
        parallel_step = None
        for step in plan['steps']:
            if len(step['tasks']) > 1:
                parallel_step = step
                break
        assert parallel_step is not None
    
    def test_get_next_tasks(self):
        """Test getting next tasks to execute."""
        mapper = DependencyMapper()
        planner = ExecutionPlanner()
        
        subtasks = [
            {'id': 'task_1', 'dependencies': [], 'estimated_complexity': 'simple'},
            {'id': 'task_2', 'dependencies': ['task_1'], 'estimated_complexity': 'simple'}
        ]
        
        dep_map = mapper.build_graph(subtasks)
        plan = planner.create_plan(dep_map, subtasks)
        
        # Initially, task_1 should be next
        next_tasks = planner.get_next_tasks(set())
        assert 'task_1' in next_tasks
        
        # After completing task_1, task_2 should be next
        next_tasks = planner.get_next_tasks({'task_1'})
        assert 'task_2' in next_tasks
    
    def test_progress_tracking(self):
        """Test execution progress tracking."""
        planner = ExecutionPlanner()
        
        planner.task_status = {
            'task_1': TaskStatus.COMPLETED,
            'task_2': TaskStatus.RUNNING,
            'task_3': TaskStatus.PENDING
        }
        
        progress = planner.get_progress()
        
        assert progress['total_tasks'] == 3
        assert progress['completed'] == 1
        assert progress['running'] == 1
        assert progress['pending'] == 1
        assert progress['progress_percentage'] > 0
    
    def test_critical_path(self):
        """Test critical path calculation."""
        mapper = DependencyMapper()
        planner = ExecutionPlanner()
        
        subtasks = [
            {'id': 'task_1', 'dependencies': [], 'estimated_complexity': 'simple'},
            {'id': 'task_2', 'dependencies': ['task_1'], 'estimated_complexity': 'complex'},
            {'id': 'task_3', 'dependencies': ['task_1'], 'estimated_complexity': 'simple'},
            {'id': 'task_4', 'dependencies': ['task_2', 'task_3'], 'estimated_complexity': 'simple'}
        ]
        
        dep_map = mapper.build_graph(subtasks)
        critical_path = planner.get_critical_path(dep_map, subtasks)
        
        assert len(critical_path) > 0
        assert 'task_1' in critical_path
        # task_2 should be in critical path (longer than task_3)
        assert 'task_2' in critical_path


class TestIntegration:
    """Integration tests for the entire task engine pipeline."""
    
    def test_full_pipeline(self):
        """Test complete pipeline from analysis to execution plan."""
        analyzer = TaskAnalyzer()
        decomposer = TaskDecomposer()
        mapper = DependencyMapper()
        planner = ExecutionPlanner()
        
        # Analyze task
        task = "Build a REST API with authentication and deploy to cloud"
        analysis = analyzer.analyze(task)
        
        assert analysis['requires_decomposition'] is True
        
        # Decompose task
        decomposition = decomposer.decompose(analysis)
        assert len(decomposition['subtasks']) > 1
        
        # Build dependency graph
        dep_map = mapper.build_graph(decomposition['subtasks'])
        assert dep_map['has_cycles'] is False
        
        # Create execution plan
        plan = planner.create_plan(dep_map, decomposition['subtasks'])
        assert plan['total_steps'] > 0
        assert 'steps' in plan
    
    def test_simple_task_pipeline(self):
        """Test pipeline with simple task that doesn't need decomposition."""
        analyzer = TaskAnalyzer()
        decomposer = TaskDecomposer()
        mapper = DependencyMapper()
        planner = ExecutionPlanner()
        
        # Analyze simple task
        task = "Write a simple function"
        analysis = analyzer.analyze(task)
        
        # Decompose (should result in single task)
        decomposition = decomposer.decompose(analysis)
        assert len(decomposition['subtasks']) == 1
        
        # Build dependency graph
        dep_map = mapper.build_graph(decomposition['subtasks'])
        assert dep_map['has_cycles'] is False
        
        # Create execution plan
        plan = planner.create_plan(dep_map, decomposition['subtasks'])
        assert plan['total_steps'] == 1
