"""
Dependency Mapper - Builds task dependency graph (DAG)

Responsibilities:
- Create directed acyclic graph (DAG) from task dependencies
- Validate that no circular dependencies exist
- Identify tasks that can run in parallel
- Calculate critical path
"""

from typing import Dict, List, Set, Any, Optional
from collections import defaultdict, deque


class DependencyMapper:
    """
    Maps task dependencies and creates execution graph.
    """
    
    def __init__(self):
        """Initialize the dependency mapper."""
        self.graph = defaultdict(list)  # adjacency list
        self.in_degree = defaultdict(int)  # in-degree for topological sort
    
    def build_graph(self, subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build dependency graph from subtasks.
        
        Args:
            subtasks: List of subtask dictionaries with dependencies
            
        Returns:
            Dictionary containing:
            - graph: Adjacency list representation
            - in_degree: In-degree of each node
            - parallel_groups: Lists of tasks that can run in parallel
            - execution_order: Topologically sorted task order
            - has_cycles: Boolean indicating if cycles exist
        """
        self.graph = defaultdict(list)
        self.in_degree = defaultdict(int)
        
        # Build the graph
        for task in subtasks:
            task_id = task['id']
            # Initialize in_degree for all tasks
            if task_id not in self.in_degree:
                self.in_degree[task_id] = 0
            
            # Add edges for dependencies
            for dep in task.get('dependencies', []):
                self.graph[dep].append(task_id)
                self.in_degree[task_id] += 1
        
        # Check for cycles
        has_cycles = self._has_cycles(list(self.graph.keys()))
        
        if has_cycles:
            return {
                'graph': dict(self.graph),
                'in_degree': dict(self.in_degree),
                'parallel_groups': [],
                'execution_order': [],
                'has_cycles': True,
                'error': 'Circular dependency detected'
            }
        
        # Calculate execution order and parallel groups
        execution_order = self._topological_sort()
        parallel_groups = self._identify_parallel_groups(subtasks)
        
        return {
            'graph': dict(self.graph),
            'in_degree': dict(self.in_degree),
            'parallel_groups': parallel_groups,
            'execution_order': execution_order,
            'has_cycles': False
        }
    
    def _topological_sort(self) -> List[str]:
        """
        Perform topological sort using Kahn's algorithm.
        
        Returns:
            List of task IDs in execution order
        """
        # Create a copy of in_degree
        in_degree_copy = self.in_degree.copy()
        
        # Find all nodes with in-degree 0
        queue = deque([node for node in in_degree_copy if in_degree_copy[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            # Reduce in-degree for neighbors
            for neighbor in self.graph[node]:
                in_degree_copy[neighbor] -= 1
                if in_degree_copy[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def _has_cycles(self, nodes: List[str]) -> bool:
        """
        Check if the graph has cycles using DFS.
        
        Args:
            nodes: List of node IDs to check
            
        Returns:
            True if cycles exist, False otherwise
        """
        visited = set()
        rec_stack = set()
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in nodes:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    def _identify_parallel_groups(self, subtasks: List[Dict[str, Any]]) -> List[List[str]]:
        """
        Identify groups of tasks that can run in parallel.
        
        Tasks can run in parallel if:
        1. They have no dependencies on each other
        2. They have the same depth in the dependency tree
        
        Args:
            subtasks: List of subtask dictionaries
            
        Returns:
            List of parallel groups, where each group is a list of task IDs
        """
        # Calculate depth for each task
        depths = self._calculate_depths(subtasks)
        
        # Group tasks by depth
        depth_groups = defaultdict(list)
        for task_id, depth in depths.items():
            depth_groups[depth].append(task_id)
        
        # Convert to list of groups
        parallel_groups = []
        for depth in sorted(depth_groups.keys()):
            group = depth_groups[depth]
            if len(group) > 1:
                # Multiple tasks at same depth can run in parallel
                parallel_groups.append(group)
            else:
                # Single task, add as its own group
                parallel_groups.append(group)
        
        return parallel_groups
    
    def _calculate_depths(self, subtasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate the depth of each task in the dependency tree.
        
        Args:
            subtasks: List of subtask dictionaries
            
        Returns:
            Dictionary mapping task_id to depth
        """
        depths = {}
        in_degree_copy = self.in_degree.copy()
        
        # BFS to calculate depths
        queue = deque([(node, 0) for node in in_degree_copy if in_degree_copy[node] == 0])
        
        while queue:
            node, depth = queue.popleft()
            depths[node] = depth
            
            for neighbor in self.graph[node]:
                in_degree_copy[neighbor] -= 1
                if in_degree_copy[neighbor] == 0:
                    queue.append((neighbor, depth + 1))
        
        return depths
    
    def get_ready_tasks(self, completed_tasks: Set[str], subtasks: List[Dict[str, Any]]) -> List[str]:
        """
        Get tasks that are ready to execute based on completed tasks.
        
        Args:
            completed_tasks: Set of completed task IDs
            subtasks: List of all subtasks
            
        Returns:
            List of task IDs ready to execute
        """
        ready = []
        
        for task in subtasks:
            task_id = task['id']
            
            # Skip if already completed
            if task_id in completed_tasks:
                continue
            
            # Check if all dependencies are satisfied
            dependencies = task.get('dependencies', [])
            if all(dep in completed_tasks for dep in dependencies):
                ready.append(task_id)
        
        return ready
