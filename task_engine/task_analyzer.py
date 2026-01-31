"""
Task Analyzer - Analyzes and classifies incoming tasks

Responsibilities:
- Extract task requirements and objectives
- Classify task complexity (simple, medium, complex)
- Identify required domains/skills
- Determine if task needs decomposition
"""

from typing import Dict, List, Any
from enum import Enum


class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"      # Single-step task, one agent
    MEDIUM = "medium"      # Multi-step task, sequential execution
    COMPLEX = "complex"    # Multi-agent, parallel execution possible


class TaskAnalyzer:
    """
    Analyzes tasks to determine complexity, requirements, and decomposition needs.
    """
    
    def __init__(self):
        """Initialize the task analyzer."""
        self.complexity_keywords = {
            'simple': ['simple', 'quick', 'one', 'single', 'just'],
            'medium': ['multi', 'several', 'multiple', 'few'],
            'complex': ['system', 'full', 'complete', 'comprehensive', 'enterprise', 'integrate']
        }
        
        self.domain_keywords = {
            'development': ['code', 'develop', 'build', 'implement', 'api', 'function', 'python', 'rest'],
            'devops': ['deploy', 'infrastructure', 'cloud', 'docker', 'kubernetes', 'ci/cd', 'aws'],
            'data': ['data', 'analyze', 'dashboard', 'report', 'statistics', 'visualization'],
            'research': ['research', 'investigate', 'study', 'evaluate'],
            'design': ['design', 'ui', 'ux', 'mockup', 'prototype', 'interface'],
            'testing': ['test', 'qa', 'testing', 'validation', 'verify']
        }
        
        # Priority keywords for domain selection when scores are tied
        self.priority_keywords = {
            'devops': ['deploy', 'cloud', 'aws', 'kubernetes', 'infrastructure'],
            'data': ['data', 'analyze', 'dashboard'],
            'testing': ['test', 'qa']
        }
    
    def analyze(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze a task and return its characteristics.
        
        Args:
            task_description: The task to analyze
            context: Optional context about the task
            
        Returns:
            Dictionary containing task analysis:
            - complexity: TaskComplexity enum
            - domains: List of required domains/skills
            - requires_decomposition: Boolean
            - estimated_subtasks: Estimated number of subtasks
            - key_requirements: List of key requirements extracted
        """
        context = context or {}
        task_lower = task_description.lower()
        
        # Determine complexity
        complexity = self._determine_complexity(task_lower)
        
        # Identify domains
        domains = self._identify_domains(task_lower)
        
        # Extract key requirements
        requirements = self._extract_requirements(task_description)
        
        # Determine if decomposition is needed
        requires_decomposition = complexity in [TaskComplexity.MEDIUM, TaskComplexity.COMPLEX]
        
        # Estimate subtasks
        estimated_subtasks = self._estimate_subtasks(complexity, task_lower)
        
        return {
            'complexity': complexity,
            'domains': domains,
            'requires_decomposition': requires_decomposition,
            'estimated_subtasks': estimated_subtasks,
            'key_requirements': requirements,
            'description': task_description,
            'context': context
        }
    
    def _determine_complexity(self, task_text: str) -> TaskComplexity:
        """Determine task complexity based on keywords and structure."""
        # Count complexity indicators
        complex_score = 0
        medium_score = 0
        simple_score = 0
        
        for keyword in self.complexity_keywords['complex']:
            if keyword in task_text:
                complex_score += 1
        
        for keyword in self.complexity_keywords['medium']:
            if keyword in task_text:
                medium_score += 1
        
        for keyword in self.complexity_keywords['simple']:
            if keyword in task_text:
                simple_score += 1
        
        # Check for multiple action verbs
        action_verbs = ['create', 'build', 'develop', 'design', 'implement', 
                       'deploy', 'test', 'analyze', 'integrate', 'configure']
        action_count = sum(1 for verb in action_verbs if verb in task_text)
        
        # Determine complexity
        if complex_score > 0 or action_count > 3:
            return TaskComplexity.COMPLEX
        # If there's an action verb (build/deploy/etc) but no explicit "simple", it's at least medium
        elif action_count >= 1 and simple_score == 0:
            return TaskComplexity.MEDIUM
        elif simple_score > 0 and action_count <= 1:
            return TaskComplexity.SIMPLE
        elif medium_score > 0 or action_count > 1:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.SIMPLE
    
    def _identify_domains(self, task_text: str) -> List[str]:
        """Identify relevant domains/skills needed for the task."""
        domain_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in task_text:
                    score += 1
            if score > 0:
                domain_scores[domain] = score
        
        # Check for priority keywords to break ties
        for domain, priority_kws in self.priority_keywords.items():
            if domain in domain_scores:
                for kw in priority_kws:
                    if kw in task_text:
                        domain_scores[domain] += 0.5  # Add half point for priority
                        break
        
        # Sort domains by score (highest first)
        domains = sorted(domain_scores.keys(), key=lambda d: domain_scores[d], reverse=True)
        
        return domains if domains else ['general']
    
    def _extract_requirements(self, task_description: str) -> List[str]:
        """Extract key requirements from task description."""
        requirements = []
        
        # Split by common separators
        parts = task_description.replace(',', '\n').replace(' and ', '\n').split('\n')
        
        for part in parts:
            part = part.strip()
            if part and len(part) > 5:  # Ignore very short fragments
                requirements.append(part)
        
        return requirements[:10]  # Limit to 10 requirements
    
    def _estimate_subtasks(self, complexity: TaskComplexity, task_text: str) -> int:
        """Estimate number of subtasks needed."""
        base_counts = {
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MEDIUM: 3,
            TaskComplexity.COMPLEX: 5
        }
        
        base = base_counts[complexity]
        
        # Adjust based on action verbs
        action_verbs = ['create', 'build', 'develop', 'design', 'implement', 
                       'deploy', 'test', 'analyze', 'integrate', 'configure']
        action_count = sum(1 for verb in action_verbs if verb in task_text)
        
        return min(base + action_count, 10)  # Cap at 10 subtasks
