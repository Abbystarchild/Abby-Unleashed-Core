"""
Result Aggregator for combining outputs from multiple agents
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Result:
    """Result object from agent execution"""
    
    def __init__(
        self,
        task_id: str,
        agent_id: str,
        output: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id
        self.agent_id = agent_id
        self.output = output
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "output": self.output,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class ResultAggregator:
    """
    Result aggregator for combining outputs from multiple agents
    
    Collects, organizes, and formats results from task execution
    """
    
    def __init__(self):
        """Initialize result aggregator"""
        self.results: Dict[str, Result] = {}
        self.task_results: Dict[str, List[str]] = {}  # task_id -> [result_ids]
        logger.info("Result aggregator initialized")
    
    def add_result(
        self,
        task_id: str,
        agent_id: str,
        output: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a result from agent execution
        
        Args:
            task_id: Task identifier
            agent_id: Agent identifier
            output: Agent output
            metadata: Optional metadata
            
        Returns:
            Result ID
        """
        result_id = f"{task_id}_{agent_id}_{datetime.now().timestamp()}"
        
        result = Result(
            task_id=task_id,
            agent_id=agent_id,
            output=output,
            metadata=metadata
        )
        
        self.results[result_id] = result
        
        # Track by task
        if task_id not in self.task_results:
            self.task_results[task_id] = []
        self.task_results[task_id].append(result_id)
        
        logger.debug(f"Added result {result_id} for task {task_id}")
        
        return result_id
    
    def get_result(self, result_id: str) -> Optional[Result]:
        """
        Get result by ID
        
        Args:
            result_id: Result identifier
            
        Returns:
            Result object or None
        """
        return self.results.get(result_id)
    
    def get_task_results(self, task_id: str) -> List[Result]:
        """
        Get all results for a task
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of results
        """
        result_ids = self.task_results.get(task_id, [])
        return [self.results[rid] for rid in result_ids if rid in self.results]
    
    def aggregate_task_results(self, task_id: str) -> Dict[str, Any]:
        """
        Aggregate results for a task into a single output
        
        Args:
            task_id: Task identifier
            
        Returns:
            Aggregated result dictionary
        """
        results = self.get_task_results(task_id)
        
        if not results:
            return {
                "task_id": task_id,
                "status": "no_results",
                "outputs": []
            }
        
        # Collect all outputs
        outputs = []
        for result in results:
            outputs.append({
                "agent_id": result.agent_id,
                "output": result.output,
                "metadata": result.metadata,
                "timestamp": result.timestamp.isoformat()
            })
        
        # Sort by timestamp
        outputs.sort(key=lambda x: x["timestamp"])
        
        return {
            "task_id": task_id,
            "status": "completed",
            "outputs": outputs,
            "num_results": len(outputs),
            "agents": list(set(r.agent_id for r in results)),
            "first_result": outputs[0]["timestamp"],
            "last_result": outputs[-1]["timestamp"]
        }
    
    def aggregate_workflow_results(self, task_ids: List[str]) -> Dict[str, Any]:
        """
        Aggregate results from multiple related tasks (workflow)
        
        Args:
            task_ids: List of task identifiers
            
        Returns:
            Aggregated workflow results
        """
        workflow_results = {}
        
        for task_id in task_ids:
            workflow_results[task_id] = self.aggregate_task_results(task_id)
        
        # Calculate workflow statistics
        total_results = sum(
            r.get("num_results", 0) 
            for r in workflow_results.values()
        )
        
        all_agents = set()
        for r in workflow_results.values():
            all_agents.update(r.get("agents", []))
        
        return {
            "workflow": {
                "total_tasks": len(task_ids),
                "total_results": total_results,
                "unique_agents": len(all_agents),
                "agents": list(all_agents)
            },
            "task_results": workflow_results
        }
    
    def get_agent_results(self, agent_id: str) -> List[Result]:
        """
        Get all results from a specific agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of results from agent
        """
        return [
            r for r in self.results.values() 
            if r.agent_id == agent_id
        ]
    
    def clear_task_results(self, task_id: str):
        """
        Clear results for a task
        
        Args:
            task_id: Task identifier
        """
        if task_id not in self.task_results:
            return
        
        result_ids = self.task_results[task_id]
        for rid in result_ids:
            if rid in self.results:
                del self.results[rid]
        
        del self.task_results[task_id]
        logger.debug(f"Cleared results for task {task_id}")
    
    def clear_all_results(self):
        """Clear all results"""
        self.results.clear()
        self.task_results.clear()
        logger.info("Cleared all results")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get aggregator statistics
        
        Returns:
            Statistics dictionary
        """
        unique_tasks = len(self.task_results)
        unique_agents = len(set(r.agent_id for r in self.results.values()))
        
        return {
            "total_results": len(self.results),
            "unique_tasks": unique_tasks,
            "unique_agents": unique_agents
        }
    
    def format_final_output(
        self,
        task_ids: List[str],
        format_type: str = "summary"
    ) -> str:
        """
        Format final output for presentation
        
        Args:
            task_ids: List of task identifiers
            format_type: Output format (summary, detailed, json)
            
        Returns:
            Formatted output string
        """
        workflow_results = self.aggregate_workflow_results(task_ids)
        
        if format_type == "json":
            import json
            return json.dumps(workflow_results, indent=2)
        
        if format_type == "detailed":
            output = []
            output.append("=" * 60)
            output.append("WORKFLOW RESULTS")
            output.append("=" * 60)
            output.append(f"\nTotal Tasks: {workflow_results['workflow']['total_tasks']}")
            output.append(f"Total Results: {workflow_results['workflow']['total_results']}")
            output.append(f"Agents Involved: {', '.join(workflow_results['workflow']['agents'])}")
            output.append("\n" + "-" * 60)
            
            for task_id, task_result in workflow_results['task_results'].items():
                output.append(f"\nTask: {task_id}")
                output.append(f"Status: {task_result['status']}")
                if task_result.get('outputs'):
                    for i, result in enumerate(task_result['outputs'], 1):
                        output.append(f"\n  Result {i} (from {result['agent_id']}):")
                        output.append(f"    {result['output']}")
            
            output.append("\n" + "=" * 60)
            return "\n".join(output)
        
        # Summary format (default)
        output = []
        output.append(f"Workflow completed with {workflow_results['workflow']['total_tasks']} tasks")
        output.append(f"Total results: {workflow_results['workflow']['total_results']}")
        output.append(f"Agents: {', '.join(workflow_results['workflow']['agents'])}")
        
        return "\n".join(output)
