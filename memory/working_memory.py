"""
Working memory for active tasks and temporary data

Manages currently active tasks, intermediate results, and scratch pad data
"""
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class WorkingMemory:
    """
    Working memory for active tasks
    
    Stores information about currently executing tasks,
    intermediate results, and temporary scratch data
    """
    
    def __init__(self):
        """Initialize working memory"""
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.scratch_pad: Dict[str, Any] = {}
        self.intermediate_results: Dict[str, Any] = {}
        self.active_agents: Set[str] = set()
        logger.info("Working memory initialized")
    
    def register_task(
        self,
        task_id: str,
        description: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register a new active task
        
        Args:
            task_id: Task identifier
            description: Task description
            agent_id: Agent handling the task
            metadata: Optional metadata
        """
        self.active_tasks[task_id] = {
            "description": description,
            "agent_id": agent_id,
            "metadata": metadata or {},
            "started_at": datetime.now(),
            "status": "active"
        }
        
        if agent_id:
            self.active_agents.add(agent_id)
        
        logger.debug(f"Registered task: {task_id}")
    
    def update_task_status(self, task_id: str, status: str):
        """
        Update task status
        
        Args:
            task_id: Task identifier
            status: New status
        """
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = status
            self.active_tasks[task_id]["updated_at"] = datetime.now()
            logger.debug(f"Task {task_id} status: {status}")
    
    def complete_task(self, task_id: str):
        """
        Mark task as completed and remove from active tasks
        
        Args:
            task_id: Task identifier
        """
        if task_id in self.active_tasks:
            task = self.active_tasks.pop(task_id)
            
            # Remove agent if no more tasks
            agent_id = task.get("agent_id")
            if agent_id:
                has_other_tasks = any(
                    t.get("agent_id") == agent_id 
                    for t in self.active_tasks.values()
                )
                if not has_other_tasks:
                    self.active_agents.discard(agent_id)
            
            logger.debug(f"Completed task: {task_id}")
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task information
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task dictionary or None
        """
        return self.active_tasks.get(task_id)
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all active tasks
        
        Returns:
            List of active task dictionaries
        """
        return list(self.active_tasks.values())
    
    def get_tasks_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get tasks for specific agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of task dictionaries
        """
        return [
            task for task in self.active_tasks.values()
            if task.get("agent_id") == agent_id
        ]
    
    def store_intermediate_result(
        self,
        key: str,
        value: Any,
        task_id: Optional[str] = None
    ):
        """
        Store an intermediate result
        
        Args:
            key: Result key
            value: Result value
            task_id: Associated task (optional)
        """
        self.intermediate_results[key] = {
            "value": value,
            "task_id": task_id,
            "stored_at": datetime.now()
        }
        logger.debug(f"Stored intermediate result: {key}")
    
    def get_intermediate_result(self, key: str) -> Optional[Any]:
        """
        Get an intermediate result
        
        Args:
            key: Result key
            
        Returns:
            Result value or None
        """
        result = self.intermediate_results.get(key)
        return result["value"] if result else None
    
    def clear_intermediate_results(self, task_id: Optional[str] = None):
        """
        Clear intermediate results
        
        Args:
            task_id: Clear only results for this task (all if None)
        """
        if task_id:
            self.intermediate_results = {
                k: v for k, v in self.intermediate_results.items()
                if v.get("task_id") != task_id
            }
        else:
            self.intermediate_results.clear()
        
        logger.debug("Cleared intermediate results")
    
    def set_scratch(self, key: str, value: Any):
        """
        Store data in scratch pad
        
        Args:
            key: Data key
            value: Data value
        """
        self.scratch_pad[key] = value
    
    def get_scratch(self, key: str) -> Optional[Any]:
        """
        Get data from scratch pad
        
        Args:
            key: Data key
            
        Returns:
            Data value or None
        """
        return self.scratch_pad.get(key)
    
    def clear_scratch(self):
        """Clear scratch pad"""
        self.scratch_pad.clear()
        logger.debug("Cleared scratch pad")
    
    def clear_all(self):
        """Clear all working memory"""
        self.active_tasks.clear()
        self.scratch_pad.clear()
        self.intermediate_results.clear()
        self.active_agents.clear()
        logger.info("Cleared all working memory")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get working memory statistics
        
        Returns:
            Statistics dictionary
        """
        return {
            "active_tasks": len(self.active_tasks),
            "active_agents": len(self.active_agents),
            "intermediate_results": len(self.intermediate_results),
            "scratch_items": len(self.scratch_pad)
        }
    
    def get_context_summary(self) -> str:
        """
        Get a summary of current working context
        
        Returns:
            Summary string
        """
        lines = []
        lines.append(f"Active Tasks: {len(self.active_tasks)}")
        
        for task_id, task in self.active_tasks.items():
            lines.append(f"  - {task_id}: {task['description'][:50]}...")
        
        if self.active_agents:
            lines.append(f"\nActive Agents: {', '.join(self.active_agents)}")
        
        return "\n".join(lines)
