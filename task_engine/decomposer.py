"""
Task Decomposer - Recursively breaks down tasks into subtasks

Responsibilities:
- Break complex tasks into manageable subtasks
- Apply decomposition strategies based on task type
- Maintain task hierarchy
- Ensure subtasks are executable
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SubTask:
    """Represents a subtask in the decomposition tree."""
    id: str
    description: str
    parent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    domain: str = 'general'
    estimated_complexity: str = 'simple'
    status: str = 'pending'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert subtask to dictionary."""
        return {
            'id': self.id,
            'description': self.description,
            'parent_id': self.parent_id,
            'dependencies': self.dependencies,
            'domain': self.domain,
            'estimated_complexity': self.estimated_complexity,
            'status': self.status,
            'created_at': self.created_at
        }


class TaskDecomposer:
    """
    Decomposes complex tasks into executable subtasks.
    """
    
    def __init__(self):
        """Initialize the task decomposer."""
        self.decomposition_strategies = {
            'development': self._decompose_development_task,
            'devops': self._decompose_devops_task,
            'data': self._decompose_data_task,
            'research': self._decompose_research_task,
            'general': self._decompose_general_task
        }
    
    def decompose(self, task_analysis: Dict[str, Any], max_depth: int = 3) -> Dict[str, Any]:
        """
        Decompose a task based on its analysis.
        
        Args:
            task_analysis: Analysis result from TaskAnalyzer
            max_depth: Maximum decomposition depth (default: 3)
            
        Returns:
            Dictionary containing:
            - root_task: Root task info
            - subtasks: List of SubTask objects
            - task_tree: Hierarchical structure
        """
        if not task_analysis.get('requires_decomposition', False):
            # No decomposition needed
            root_task = SubTask(
                id='task_0',
                description=task_analysis['description'],
                domain=task_analysis['domains'][0] if task_analysis['domains'] else 'general',
                estimated_complexity=task_analysis['complexity'].value
            )
            return {
                'root_task': root_task.to_dict(),
                'subtasks': [root_task.to_dict()],
                'task_tree': {root_task.id: []}
            }
        
        # Determine primary domain
        primary_domain = task_analysis['domains'][0] if task_analysis['domains'] else 'general'
        
        # Select decomposition strategy
        strategy = self.decomposition_strategies.get(primary_domain, self._decompose_general_task)
        
        # Create root task
        root_task = SubTask(
            id='task_0',
            description=task_analysis['description'],
            domain=primary_domain,
            estimated_complexity=task_analysis['complexity'].value
        )
        
        # Decompose using strategy
        subtasks = strategy(task_analysis, root_task.id)
        
        # Build task tree
        task_tree = self._build_task_tree([root_task] + subtasks)
        
        return {
            'root_task': root_task.to_dict(),
            'subtasks': [task.to_dict() for task in subtasks],
            'task_tree': task_tree
        }
    
    def _decompose_development_task(self, analysis: Dict[str, Any], parent_id: str) -> List[SubTask]:
        """Decompose a development task."""
        subtasks = []
        task_id = 1
        
        # Standard development phases
        phases = [
            ('Requirements analysis', 'development'),
            ('Design and architecture', 'design'),
            ('Implementation', 'development'),
            ('Testing', 'testing'),
            ('Documentation', 'development')
        ]
        
        for phase_desc, domain in phases:
            subtask = SubTask(
                id=f'task_{task_id}',
                description=f'{phase_desc} for {analysis["description"]}',
                parent_id=parent_id,
                domain=domain,
                estimated_complexity='simple'
            )
            
            # Add dependencies (sequential)
            if task_id > 1:
                subtask.dependencies.append(f'task_{task_id - 1}')
            
            subtasks.append(subtask)
            task_id += 1
        
        return subtasks
    
    def _decompose_devops_task(self, analysis: Dict[str, Any], parent_id: str) -> List[SubTask]:
        """Decompose a DevOps task."""
        subtasks = []
        task_id = 1
        
        phases = [
            ('Infrastructure setup', 'devops'),
            ('Configuration management', 'devops'),
            ('Deployment pipeline', 'devops'),
            ('Monitoring and logging', 'devops'),
            ('Security hardening', 'devops')
        ]
        
        for phase_desc, domain in phases:
            subtask = SubTask(
                id=f'task_{task_id}',
                description=f'{phase_desc} for {analysis["description"]}',
                parent_id=parent_id,
                domain=domain,
                estimated_complexity='simple'
            )
            
            if task_id > 1:
                subtask.dependencies.append(f'task_{task_id - 1}')
            
            subtasks.append(subtask)
            task_id += 1
        
        return subtasks
    
    def _decompose_data_task(self, analysis: Dict[str, Any], parent_id: str) -> List[SubTask]:
        """Decompose a data analysis task."""
        subtasks = []
        task_id = 1
        
        phases = [
            ('Data collection and preparation', 'data'),
            ('Exploratory data analysis', 'data'),
            ('Data processing and transformation', 'data'),
            ('Analysis and modeling', 'data'),
            ('Visualization and reporting', 'data')
        ]
        
        for phase_desc, domain in phases:
            subtask = SubTask(
                id=f'task_{task_id}',
                description=f'{phase_desc} for {analysis["description"]}',
                parent_id=parent_id,
                domain=domain,
                estimated_complexity='simple'
            )
            
            if task_id > 1:
                subtask.dependencies.append(f'task_{task_id - 1}')
            
            subtasks.append(subtask)
            task_id += 1
        
        return subtasks
    
    def _decompose_research_task(self, analysis: Dict[str, Any], parent_id: str) -> List[SubTask]:
        """Decompose a research task."""
        subtasks = []
        task_id = 1
        
        phases = [
            ('Define research scope and questions', 'research'),
            ('Literature review and background research', 'research'),
            ('Data gathering and analysis', 'research'),
            ('Synthesis and conclusions', 'research'),
            ('Documentation and presentation', 'research')
        ]
        
        for phase_desc, domain in phases:
            subtask = SubTask(
                id=f'task_{task_id}',
                description=f'{phase_desc} for {analysis["description"]}',
                parent_id=parent_id,
                domain=domain,
                estimated_complexity='simple'
            )
            
            if task_id > 1:
                subtask.dependencies.append(f'task_{task_id - 1}')
            
            subtasks.append(subtask)
            task_id += 1
        
        return subtasks
    
    def _decompose_general_task(self, analysis: Dict[str, Any], parent_id: str) -> List[SubTask]:
        """Decompose a general task."""
        subtasks = []
        requirements = analysis.get('key_requirements', [])
        
        if not requirements:
            # Fallback to basic decomposition
            requirements = [
                'Analyze requirements',
                'Plan approach',
                'Execute task',
                'Verify results'
            ]
        
        for idx, req in enumerate(requirements[:5], 1):  # Limit to 5 subtasks
            subtask = SubTask(
                id=f'task_{idx}',
                description=req,
                parent_id=parent_id,
                domain='general',
                estimated_complexity='simple'
            )
            
            # Add sequential dependency
            if idx > 1:
                subtask.dependencies.append(f'task_{idx - 1}')
            
            subtasks.append(subtask)
        
        return subtasks
    
    def _build_task_tree(self, all_tasks: List[SubTask]) -> Dict[str, List[str]]:
        """Build a hierarchical tree structure from tasks."""
        tree = {}
        
        for task in all_tasks:
            tree[task.id] = []
        
        for task in all_tasks:
            if task.parent_id:
                if task.parent_id in tree:
                    tree[task.parent_id].append(task.id)
        
        return tree
