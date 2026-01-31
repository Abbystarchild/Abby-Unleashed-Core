"""
Task Tracker for monitoring task progress
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Task:
    """Task object for tracking"""
    
    def __init__(
        self,
        task_id: str,
        description: str,
        agent_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id
        self.description = description
        self.agent_id = agent_id
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        self.status = TaskStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress = 0.0  # 0.0 to 1.0
    
    def start(self, agent_id: str):
        """Mark task as started"""
        self.status = TaskStatus.IN_PROGRESS
        self.agent_id = agent_id
        self.started_at = datetime.now()
    
    def update_progress(self, progress: float):
        """Update task progress"""
        self.progress = max(0.0, min(1.0, progress))
    
    def complete(self, result: Dict[str, Any]):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()
        self.progress = 1.0
    
    def fail(self, error: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()
    
    def block(self):
        """Mark task as blocked (waiting for dependencies)"""
        self.status = TaskStatus.BLOCKED
    
    def assign(self, agent_id: str):
        """Assign task to agent"""
        self.status = TaskStatus.ASSIGNED
        self.agent_id = agent_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "progress": self.progress,
            "dependencies": self.dependencies,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class TaskTracker:
    """
    Task tracker for monitoring task execution
    
    Tracks status, progress, and dependencies for all tasks
    """
    
    def __init__(self):
        """Initialize task tracker"""
        self.tasks: Dict[str, Task] = {}
        logger.info("Task tracker initialized")
    
    def add_task(
        self,
        task_id: str,
        description: str,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Add a new task to track
        
        Args:
            task_id: Unique task identifier
            description: Task description
            dependencies: List of task IDs this task depends on
            metadata: Additional task metadata
            
        Returns:
            Created task object
        """
        if task_id in self.tasks:
            logger.warning(f"Task {task_id} already exists")
            return self.tasks[task_id]
        
        task = Task(
            task_id=task_id,
            description=description,
            dependencies=dependencies,
            metadata=metadata
        )
        
        self.tasks[task_id] = task
        logger.debug(f"Added task: {task_id}")
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get task by ID
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task object or None
        """
        return self.tasks.get(task_id)
    
    def assign_task(self, task_id: str, agent_id: str):
        """
        Assign task to agent
        
        Args:
            task_id: Task identifier
            agent_id: Agent identifier
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task.assign(agent_id)
        logger.info(f"Assigned task {task_id} to agent {agent_id}")
    
    def start_task(self, task_id: str, agent_id: str):
        """
        Mark task as started
        
        Args:
            task_id: Task identifier
            agent_id: Agent identifier
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task.start(agent_id)
        logger.info(f"Task {task_id} started by agent {agent_id}")
    
    def update_progress(self, task_id: str, progress: float):
        """
        Update task progress
        
        Args:
            task_id: Task identifier
            progress: Progress value (0.0 to 1.0)
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task.update_progress(progress)
        logger.debug(f"Task {task_id} progress: {progress:.1%}")
    
    def complete_task(self, task_id: str, result: Dict[str, Any]):
        """
        Mark task as completed
        
        Args:
            task_id: Task identifier
            result: Task result
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task.complete(result)
        logger.info(f"Task {task_id} completed")
    
    def fail_task(self, task_id: str, error: str):
        """
        Mark task as failed
        
        Args:
            task_id: Task identifier
            error: Error message
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task.fail(error)
        logger.error(f"Task {task_id} failed: {error}")
    
    def block_task(self, task_id: str):
        """
        Mark task as blocked
        
        Args:
            task_id: Task identifier
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task.block()
        logger.debug(f"Task {task_id} blocked")
    
    def get_ready_tasks(self) -> List[Task]:
        """
        Get tasks that are ready to execute (all dependencies completed)
        
        Returns:
            List of ready tasks
        """
        ready = []
        
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            if self._dependencies_satisfied(task):
                ready.append(task)
        
        return ready
    
    def _dependencies_satisfied(self, task: Task) -> bool:
        """
        Check if task dependencies are satisfied
        
        Args:
            task: Task to check
            
        Returns:
            True if all dependencies completed
        """
        for dep_id in task.dependencies:
            dep_task = self.get_task(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """
        Get tasks by status
        
        Args:
            status: Task status to filter by
            
        Returns:
            List of tasks with given status
        """
        return [t for t in self.tasks.values() if t.status == status]
    
    def get_tasks_by_agent(self, agent_id: str) -> List[Task]:
        """
        Get tasks assigned to agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of tasks assigned to agent
        """
        return [t for t in self.tasks.values() if t.agent_id == agent_id]
    
    def get_overall_progress(self) -> float:
        """
        Get overall progress across all tasks
        
        Returns:
            Overall progress (0.0 to 1.0)
        """
        if not self.tasks:
            return 0.0
        
        total_progress = sum(t.progress for t in self.tasks.values())
        return total_progress / len(self.tasks)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get tracker statistics
        
        Returns:
            Statistics dictionary
        """
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = len(self.get_tasks_by_status(status))
        
        return {
            "total_tasks": len(self.tasks),
            "status_counts": status_counts,
            "overall_progress": self.get_overall_progress(),
            "ready_tasks": len(self.get_ready_tasks())
        }
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all tasks as dictionaries
        
        Returns:
            List of task dictionaries
        """
        return [t.to_dict() for t in self.tasks.values()]
