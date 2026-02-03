"""
System Resource Manager - Provides optimal agent configuration based on hardware
"""
import os
import yaml
import psutil
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentLimits:
    """Agent resource limits"""
    max_concurrent: int
    optimal_concurrent: int
    memory_per_agent_mb: int
    max_memory_percent: float
    min_free_memory_gb: float


@dataclass
class TaskScaling:
    """Agent scaling based on task complexity"""
    simple_task: int
    medium_task: int
    complex_task: int
    large_project: int
    massive_project: int


class SystemResourceManager:
    """
    Manages system resources and provides optimal agent configurations
    """
    
    CONFIG_PATH = "config/system_resources.yaml"
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or self.CONFIG_PATH
        self.config = self._load_config()
        self._detect_and_update()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Could not load config: {e}")
        return {}
    
    def _detect_and_update(self):
        """Detect current system resources and update recommendations"""
        memory = psutil.virtual_memory()
        self.total_ram_gb = memory.total / (1024**3)
        self.available_ram_gb = memory.available / (1024**3)
        self.cpu_cores = psutil.cpu_count()
        
        # Calculate optimal based on current state
        self._calculate_optimal()
    
    def _calculate_optimal(self):
        """Calculate optimal agent counts based on current resources"""
        available_mb = self.available_ram_gb * 1024
        
        # Memory-based: use 50% of available at ~50MB per agent
        memory_limit = int(available_mb * 0.5 / 50)
        
        # CPU-based: 2 agents per core
        cpu_limit = self.cpu_cores * 2
        
        # Take minimum, cap at configured max or 50
        config_max = self.config.get('agent_limits', {}).get('max_concurrent', 50)
        self.optimal_agents = min(memory_limit, cpu_limit, config_max)
        self.max_agents = min(memory_limit, config_max)
    
    def get_agent_limits(self) -> AgentLimits:
        """Get current agent limits"""
        limits = self.config.get('agent_limits', {})
        return AgentLimits(
            max_concurrent=self.max_agents,
            optimal_concurrent=self.optimal_agents,
            memory_per_agent_mb=limits.get('memory_per_agent_mb', 50),
            max_memory_percent=limits.get('max_memory_percent', 70),
            min_free_memory_gb=limits.get('min_free_memory_gb', 2)
        )
    
    def get_task_scaling(self) -> TaskScaling:
        """Get agent scaling for different task sizes"""
        scaling = self.config.get('task_scaling', {})
        return TaskScaling(
            simple_task=min(scaling.get('simple_task', 1), self.optimal_agents),
            medium_task=min(scaling.get('medium_task', 3), self.optimal_agents),
            complex_task=min(scaling.get('complex_task', 8), self.optimal_agents),
            large_project=min(scaling.get('large_project', 15), self.optimal_agents),
            massive_project=min(scaling.get('massive_project', 30), self.optimal_agents)
        )
    
    def get_agents_for_complexity(self, complexity: str) -> int:
        """
        Get recommended number of agents for a task complexity
        
        Args:
            complexity: simple, medium, complex, large, massive
            
        Returns:
            Recommended agent count
        """
        scaling = self.get_task_scaling()
        complexity_map = {
            'simple': scaling.simple_task,
            'medium': scaling.medium_task,
            'complex': scaling.complex_task,
            'large': scaling.large_project,
            'massive': scaling.massive_project
        }
        return complexity_map.get(complexity.lower(), scaling.medium_task)
    
    def can_spawn_agent(self) -> tuple[bool, str]:
        """
        Check if system can safely spawn another agent
        
        Returns:
            (can_spawn, reason)
        """
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        free_gb = memory.available / (1024**3)
        
        limits = self.get_agent_limits()
        
        if memory_percent >= limits.max_memory_percent:
            return False, f"Memory usage at {memory_percent:.1f}% (max {limits.max_memory_percent}%)"
        
        if free_gb < limits.min_free_memory_gb:
            return False, f"Only {free_gb:.1f}GB free (min {limits.min_free_memory_gb}GB)"
        
        return True, "OK"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        memory = psutil.virtual_memory()
        return {
            'system': {
                'total_ram_gb': round(self.total_ram_gb, 1),
                'available_ram_gb': round(memory.available / (1024**3), 1),
                'memory_percent': round(memory.percent, 1),
                'cpu_cores': self.cpu_cores
            },
            'limits': {
                'max_agents': self.max_agents,
                'optimal_agents': self.optimal_agents,
                'can_spawn': self.can_spawn_agent()[0]
            },
            'scaling': {
                'simple': self.get_agents_for_complexity('simple'),
                'medium': self.get_agents_for_complexity('medium'),
                'complex': self.get_agents_for_complexity('complex'),
                'large': self.get_agents_for_complexity('large'),
                'massive': self.get_agents_for_complexity('massive')
            }
        }
    
    def print_status(self):
        """Print system status"""
        status = self.get_status()
        
        print("=" * 60)
        print("ABBY SYSTEM RESOURCE STATUS")
        print("=" * 60)
        print(f"Total RAM:     {status['system']['total_ram_gb']} GB")
        print(f"Available:     {status['system']['available_ram_gb']} GB")
        print(f"Memory Used:   {status['system']['memory_percent']}%")
        print(f"CPU Cores:     {status['system']['cpu_cores']}")
        print("-" * 60)
        print(f"Max Agents:    {status['limits']['max_agents']}")
        print(f"Optimal:       {status['limits']['optimal_agents']}")
        print(f"Can Spawn:     {'✓' if status['limits']['can_spawn'] else '✗'}")
        print("-" * 60)
        print("Task Scaling:")
        print(f"  Simple:      {status['scaling']['simple']} agents")
        print(f"  Medium:      {status['scaling']['medium']} agents")
        print(f"  Complex:     {status['scaling']['complex']} agents")
        print(f"  Large:       {status['scaling']['large']} agents")
        print(f"  Massive:     {status['scaling']['massive']} agents")
        print("=" * 60)


# Global instance
_resource_manager: Optional[SystemResourceManager] = None

def get_resource_manager() -> SystemResourceManager:
    """Get or create the global resource manager"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = SystemResourceManager()
    return _resource_manager


if __name__ == "__main__":
    manager = get_resource_manager()
    manager.print_status()
