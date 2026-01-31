"""
Example: Using the coordination system for multi-agent task execution

This demonstrates Phase 3 coordination capabilities:
- Task decomposition and planning
- Multi-agent orchestration
- Progress tracking
- Result aggregation
"""
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from personality.brain_clone import BrainClone
from persona_library.library_manager import PersonaLibrary
from agents.agent_factory import AgentFactory
from coordination.orchestrator import Orchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """Demonstrate coordination system"""
    
    print("=" * 70)
    print("ABBY UNLEASHED - COORDINATION SYSTEM DEMO (Phase 3)")
    print("=" * 70)
    print()
    
    # Initialize components
    print("Initializing Abby Unleashed components...")
    
    brain_clone = BrainClone("config/brain_clone.yaml")
    persona_library = PersonaLibrary("persona_library/personas/personas.yaml")
    agent_factory = AgentFactory(
        persona_library=persona_library,
        personality=brain_clone.get_personality()
    )
    
    # Initialize orchestrator
    orchestrator = Orchestrator(agent_factory=agent_factory)
    orchestrator.start()
    
    print(f"✓ Loaded personality: {brain_clone.personality.get('identity', {}).get('name')}")
    print(f"✓ Loaded {len(persona_library.personas)} personas")
    print(f"✓ Orchestrator initialized and started")
    print()
    
    # Example 1: Simple task
    print("-" * 70)
    print("EXAMPLE 1: Simple Task")
    print("-" * 70)
    print()
    
    simple_task = "Create a Python function to calculate fibonacci numbers"
    print(f"Task: {simple_task}")
    print()
    
    result = orchestrator.execute_task(simple_task)
    
    print(f"Status: {result.get('workflow', {}).get('total_tasks', 1)} task(s) executed")
    print(f"Agents: {', '.join(result.get('workflow', {}).get('agents', ['N/A']))}")
    print()
    
    # Example 2: Complex multi-step task
    print("-" * 70)
    print("EXAMPLE 2: Complex Multi-Step Task")
    print("-" * 70)
    print()
    
    complex_task = """
    Build a REST API for a todo application with the following requirements:
    1. User authentication with JWT
    2. CRUD operations for todos
    3. Database integration with PostgreSQL
    4. Deployment configuration for Docker
    """
    
    print(f"Task: {complex_task.strip()}")
    print()
    print("Orchestrating multi-agent execution...")
    print()
    
    result = orchestrator.execute_task(complex_task)
    
    print("\nExecution Results:")
    print("-" * 70)
    print(f"Total Tasks: {result.get('workflow', {}).get('total_tasks', 0)}")
    print(f"Total Results: {result.get('workflow', {}).get('total_results', 0)}")
    print(f"Unique Agents: {result.get('workflow', {}).get('unique_agents', 0)}")
    print(f"Agents: {', '.join(result.get('workflow', {}).get('agents', []))}")
    print()
    
    # Show execution details
    if 'execution' in result:
        print("Execution Details:")
        print(f"  Total Steps: {result['execution'].get('total_steps', 0)}")
        print(f"  Can Parallelize: {result['execution'].get('can_parallelize', False)}")
        print(f"  Overall Progress: {result['execution'].get('overall_progress', 0):.1%}")
        print()
    
    # Get progress statistics
    print("-" * 70)
    print("ORCHESTRATOR STATISTICS")
    print("-" * 70)
    
    progress = orchestrator.get_progress()
    
    print(f"\nTask Statistics:")
    task_stats = progress.get('task_stats', {})
    print(f"  Total Tasks: {task_stats.get('total_tasks', 0)}")
    status_counts = task_stats.get('status_counts', {})
    for status, count in status_counts.items():
        if count > 0:
            print(f"  {status.replace('_', ' ').title()}: {count}")
    
    print(f"\nResult Statistics:")
    result_stats = progress.get('result_stats', {})
    print(f"  Total Results: {result_stats.get('total_results', 0)}")
    print(f"  Unique Tasks: {result_stats.get('unique_tasks', 0)}")
    print(f"  Unique Agents: {result_stats.get('unique_agents', 0)}")
    
    print(f"\nMessage Bus Statistics:")
    message_stats = progress.get('message_stats', {})
    print(f"  Running: {message_stats.get('running', False)}")
    print(f"  Messages in History: {message_stats.get('history_size', 0)}")
    print(f"  Active Subscribers: {message_stats.get('subscribers', 0)}")
    
    # Example 3: Get formatted results
    print()
    print("-" * 70)
    print("FORMATTED RESULTS")
    print("-" * 70)
    print()
    
    # Get all task IDs
    task_ids = list(orchestrator.task_tracker.tasks.keys())
    
    if task_ids:
        formatted = orchestrator.get_results(task_ids[:3], format_type="summary")
        print(formatted)
    
    # Cleanup
    print()
    print("-" * 70)
    print("Cleaning up...")
    orchestrator.stop()
    orchestrator.cleanup()
    
    print("✓ Orchestrator stopped and cleaned up")
    print()
    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
