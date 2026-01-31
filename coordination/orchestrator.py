"""
Orchestrator - Master coordinator for multi-agent task execution
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from task_engine.task_analyzer import TaskAnalyzer
from task_engine.decomposer import TaskDecomposer
from task_engine.dependency_mapper import DependencyMapper
from task_engine.execution_planner import ExecutionPlanner
from agents.agent_factory import AgentFactory
from .message_bus import MessageBus, Message, MessageType
from .task_tracker import TaskTracker, TaskStatus
from .result_aggregator import ResultAggregator

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Master coordinator for multi-agent task execution
    
    Integrates task decomposition, agent coordination, progress tracking,
    and result aggregation for complex workflows
    """
    
    def __init__(
        self,
        agent_factory: AgentFactory,
        task_analyzer: Optional[TaskAnalyzer] = None,
        task_decomposer: Optional[TaskDecomposer] = None,
        dependency_mapper: Optional[DependencyMapper] = None,
        execution_planner: Optional[ExecutionPlanner] = None
    ):
        """
        Initialize orchestrator
        
        Args:
            agent_factory: Factory for creating agents
            task_analyzer: Task analyzer (creates if None)
            task_decomposer: Task decomposer (creates if None)
            dependency_mapper: Dependency mapper (creates if None)
            execution_planner: Execution planner (creates if None)
        """
        self.agent_factory = agent_factory
        
        # Task engine components
        self.task_analyzer = task_analyzer or TaskAnalyzer()
        self.task_decomposer = task_decomposer or TaskDecomposer()
        self.dependency_mapper = dependency_mapper or DependencyMapper()
        self.execution_planner = execution_planner or ExecutionPlanner()
        
        # Coordination components
        self.message_bus = MessageBus()
        self.task_tracker = TaskTracker()
        self.result_aggregator = ResultAggregator()
        
        # Active agents
        self.agents: Dict[str, Any] = {}
        
        logger.info("Orchestrator initialized")
    
    def start(self):
        """Start orchestrator services"""
        self.message_bus.start()
        logger.info("Orchestrator started")
    
    def stop(self):
        """Stop orchestrator services"""
        self.message_bus.stop()
        logger.info("Orchestrator stopped")
    
    def execute_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a task with multi-agent coordination
        
        Args:
            task_description: Description of task to execute
            context: Optional task context
            
        Returns:
            Execution result dictionary
        """
        context = context or {}
        
        logger.info(f"Orchestrating task: {task_description[:100]}...")
        
        try:
            # 1. Analyze task
            analysis = self.task_analyzer.analyze(task_description, context)
            logger.info(f"Task complexity: {analysis['complexity'].value}")
            logger.info(f"Domains: {', '.join(analysis['domains'])}")
            
            # 2. Decompose task (if complex)
            decomposition = self.task_decomposer.decompose(analysis)
            subtasks = decomposition['subtasks']
            logger.info(f"Decomposed into {len(subtasks)} subtask(s)")
            
            # 3. Build dependency graph
            dep_map = self.dependency_mapper.build_graph(subtasks)
            
            # 4. Create execution plan
            execution_plan = self.execution_planner.create_plan(dep_map, subtasks)
            logger.info(f"Execution plan: {execution_plan['total_steps']} steps")
            logger.info(f"Can parallelize: {execution_plan['can_parallelize']}")
            
            # 5. Execute plan with agents
            result = self._execute_plan(execution_plan, context)
            
            return result
        
        except Exception as e:
            logger.error(f"Error orchestrating task: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _execute_plan(
        self,
        execution_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the task plan
        
        Args:
            execution_plan: Execution plan from planner
            context: Task context
            
        Returns:
            Execution result
        """
        # Add all tasks to tracker
        task_ids = []
        for step in execution_plan['steps']:
            task = step['task']
            task_id = task['id']
            task_ids.append(task_id)
            
            self.task_tracker.add_task(
                task_id=task_id,
                description=task['description'],
                dependencies=task.get('dependencies', []),
                metadata=task.get('metadata', {})
            )
        
        # Execute tasks in order
        for step in execution_plan['steps']:
            step_num = step['step_number']
            tasks = step['tasks'] if 'tasks' in step else [step['task']]
            
            logger.info(f"Executing step {step_num}/{execution_plan['total_steps']}")
            
            # Execute tasks in this step (can be parallel)
            for task in tasks:
                self._execute_single_task(task, context)
        
        # Aggregate results
        final_result = self.result_aggregator.aggregate_workflow_results(task_ids)
        
        # Add execution statistics
        final_result['execution'] = {
            "total_steps": execution_plan['total_steps'],
            "can_parallelize": execution_plan['can_parallelize'],
            "critical_path_length": execution_plan.get('critical_path_length', 0),
            "overall_progress": self.task_tracker.get_overall_progress()
        }
        
        return final_result
    
    def _execute_single_task(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """
        Execute a single task with an agent
        
        Args:
            task: Task dictionary
            context: Task context
        """
        task_id = task['id']
        description = task['description']
        
        logger.info(f"Executing task: {task_id}")
        
        # Publish task assigned message
        self.message_bus.publish(Message(
            msg_type=MessageType.TASK_ASSIGNED,
            sender="orchestrator",
            content={"task_id": task_id, "description": description}
        ))
        
        try:
            # Create agent for this task
            agent = self.agent_factory.create_agent(description, context)
            agent_id = f"{agent.dna.role}_{datetime.now().timestamp()}"
            self.agents[agent_id] = agent
            
            # Assign and start task
            self.task_tracker.assign_task(task_id, agent_id)
            self.task_tracker.start_task(task_id, agent_id)
            
            # Publish task started message
            self.message_bus.publish(Message(
                msg_type=MessageType.TASK_STARTED,
                sender=agent_id,
                content={"task_id": task_id}
            ))
            
            # Execute task
            result = agent.execute_task(description, context)
            
            # Check if clarification needed
            if result.get("status") == "clarification_needed":
                self.task_tracker.block_task(task_id)
                logger.warning(f"Task {task_id} requires clarification")
                return
            
            # Complete task
            self.task_tracker.complete_task(task_id, result)
            self.result_aggregator.add_result(
                task_id=task_id,
                agent_id=agent_id,
                output=result.get('output', result),
                metadata=result.get('metadata', {})
            )
            
            # Publish completion message
            self.message_bus.publish(Message(
                msg_type=MessageType.TASK_COMPLETED,
                sender=agent_id,
                content={"task_id": task_id, "result": result}
            ))
            
            logger.info(f"Task {task_id} completed successfully")
        
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            self.task_tracker.fail_task(task_id, str(e))
            
            # Publish failure message
            self.message_bus.publish(Message(
                msg_type=MessageType.TASK_FAILED,
                sender="orchestrator",
                content={"task_id": task_id, "error": str(e)}
            ))
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get current execution progress
        
        Returns:
            Progress dictionary
        """
        return {
            "overall_progress": self.task_tracker.get_overall_progress(),
            "task_stats": self.task_tracker.get_stats(),
            "result_stats": self.result_aggregator.get_stats(),
            "message_stats": self.message_bus.get_stats()
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific task
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status dictionary or None
        """
        task = self.task_tracker.get_task(task_id)
        if not task:
            return None
        
        return task.to_dict()
    
    def get_results(
        self,
        task_ids: Optional[List[str]] = None,
        format_type: str = "summary"
    ) -> str:
        """
        Get formatted results
        
        Args:
            task_ids: Optional list of task IDs (all if None)
            format_type: Output format (summary, detailed, json)
            
        Returns:
            Formatted results string
        """
        if not task_ids:
            task_ids = list(self.task_tracker.tasks.keys())
        
        return self.result_aggregator.format_final_output(task_ids, format_type)
    
    def cleanup(self):
        """Clean up orchestrator resources"""
        self.task_tracker.tasks.clear()
        self.result_aggregator.clear_all_results()
        self.message_bus.clear_history()
        self.agents.clear()
        logger.info("Orchestrator cleaned up")
