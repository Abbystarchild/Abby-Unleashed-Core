"""
Execution Planner - Creates execution plan from dependencies

Responsibilities:
- Generate optimized execution plan
- Handle sequential and parallel execution
- Track task status and progress
- Manage task scheduling
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class ExecutionStep:
    """Represents a step in the execution plan."""
    step_number: int
    tasks: List[str]  # Task IDs to execute in this step
    can_parallelize: bool
    dependencies_satisfied: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'step_number': self.step_number,
            'tasks': self.tasks,
            'can_parallelize': self.can_parallelize,
            'dependencies_satisfied': self.dependencies_satisfied
        }


class ExecutionPlanner:
    """
    Creates and manages execution plans for task graphs.
    """
    
    def __init__(self):
        """Initialize the execution planner."""
        self.current_plan = None
        self.task_status = {}
    
    def create_plan(self, dependency_map: Dict[str, Any], subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create an execution plan from dependency map.
        
        Args:
            dependency_map: Result from DependencyMapper.build_graph()
            subtasks: List of subtask dictionaries
            
        Returns:
            Dictionary containing:
            - steps: List of ExecutionStep objects
            - total_steps: Total number of steps
            - can_parallelize: Whether any steps can be parallelized
            - estimated_time: Rough estimate (if provided in subtasks)
        """
        if dependency_map.get('has_cycles', False):
            return {
                'steps': [],
                'total_steps': 0,
                'can_parallelize': False,
                'error': 'Cannot create plan: circular dependency detected'
            }
        
        # Get parallel groups from dependency map
        parallel_groups = dependency_map.get('parallel_groups', [])
        execution_order = dependency_map.get('execution_order', [])
        
        # Create execution steps from parallel groups
        steps = []
        for step_num, group in enumerate(parallel_groups, 1):
            can_parallelize = len(group) > 1
            step = ExecutionStep(
                step_number=step_num,
                tasks=group,
                can_parallelize=can_parallelize
            )
            steps.append(step)
        
        # If no parallel groups, create sequential plan
        if not steps and execution_order:
            for step_num, task_id in enumerate(execution_order, 1):
                step = ExecutionStep(
                    step_number=step_num,
                    tasks=[task_id],
                    can_parallelize=False
                )
                steps.append(step)
        
        # Initialize task status
        for task in subtasks:
            self.task_status[task['id']] = TaskStatus.PENDING
        
        # Check if any parallelization is possible
        can_parallelize = any(step.can_parallelize for step in steps)
        
        plan = {
            'steps': [step.to_dict() for step in steps],
            'total_steps': len(steps),
            'can_parallelize': can_parallelize,
            'estimated_time': self._estimate_total_time(subtasks),
            'created_at': datetime.now().isoformat()
        }
        
        self.current_plan = plan
        return plan
    
    def get_next_tasks(self, completed_tasks: Set[str]) -> List[str]:
        """
        Get next tasks to execute based on completed tasks.
        
        Args:
            completed_tasks: Set of completed task IDs
            
        Returns:
            List of task IDs ready to execute
        """
        if not self.current_plan:
            return []
        
        next_tasks = []
        
        for step in self.current_plan['steps']:
            # Check if all tasks in previous steps are completed
            step_tasks = step['tasks']
            
            # Get tasks that haven't been completed
            pending_in_step = [t for t in step_tasks if t not in completed_tasks]
            
            if pending_in_step:
                # This is the next step to execute
                next_tasks = pending_in_step
                break
        
        return next_tasks
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """
        Update the status of a task.
        
        Args:
            task_id: Task ID to update
            status: New TaskStatus
        """
        self.task_status[task_id] = status
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get current execution progress.
        
        Returns:
            Dictionary with progress information
        """
        if not self.task_status:
            return {
                'total_tasks': 0,
                'completed': 0,
                'running': 0,
                'pending': 0,
                'failed': 0,
                'progress_percentage': 0.0
            }
        
        total = len(self.task_status)
        completed = sum(1 for s in self.task_status.values() if s == TaskStatus.COMPLETED)
        running = sum(1 for s in self.task_status.values() if s == TaskStatus.RUNNING)
        pending = sum(1 for s in self.task_status.values() if s == TaskStatus.PENDING)
        failed = sum(1 for s in self.task_status.values() if s == TaskStatus.FAILED)
        
        progress = (completed / total * 100) if total > 0 else 0.0
        
        return {
            'total_tasks': total,
            'completed': completed,
            'running': running,
            'pending': pending,
            'failed': failed,
            'progress_percentage': round(progress, 2)
        }
    
    def _estimate_total_time(self, subtasks: List[Dict[str, Any]]) -> Optional[int]:
        """
        Estimate total execution time in minutes.
        
        Args:
            subtasks: List of subtasks
            
        Returns:
            Estimated time in minutes, or None if cannot estimate
        """
        # Simple heuristic: assume each simple task takes 5 minutes
        complexity_time = {
            'simple': 5,
            'medium': 15,
            'complex': 30
        }
        
        total_time = 0
        for task in subtasks:
            complexity = task.get('estimated_complexity', 'simple')
            total_time += complexity_time.get(complexity, 5)
        
        return total_time
    
    def get_critical_path(self, dependency_map: Dict[str, Any], subtasks: List[Dict[str, Any]]) -> List[str]:
        """
        Calculate the critical path through the task graph.
        
        The critical path is the longest path from start to end.
        
        Args:
            dependency_map: Result from DependencyMapper
            subtasks: List of subtasks
            
        Returns:
            List of task IDs on the critical path
        """
        # Build task duration map
        task_duration = {}
        for task in subtasks:
            complexity = task.get('estimated_complexity', 'simple')
            duration = {'simple': 5, 'medium': 15, 'complex': 30}.get(complexity, 5)
            task_duration[task['id']] = duration
        
        # Calculate longest path using dynamic programming
        execution_order = dependency_map.get('execution_order', [])
        graph = dependency_map.get('graph', {})
        
        # Distance from start
        dist = {task_id: 0 for task_id in execution_order}
        predecessor = {task_id: None for task_id in execution_order}
        
        # Process in topological order
        for task_id in execution_order:
            current_dist = dist[task_id] + task_duration.get(task_id, 5)
            
            for next_task in graph.get(task_id, []):
                if current_dist > dist[next_task]:
                    dist[next_task] = current_dist
                    predecessor[next_task] = task_id
        
        # Find task with maximum distance (end of critical path)
        if not dist:
            return []
        
        end_task = max(dist, key=dist.get)
        
        # Backtrack to find critical path
        path = []
        current = end_task
        while current is not None:
            path.append(current)
            current = predecessor[current]
        
        return list(reversed(path))
