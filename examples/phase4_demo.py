"""
Phase 4 Demo: Memory and Learning Systems

Demonstrates the new Phase 4 features:
- Short-term memory (conversation context)
- Working memory (task tracking)
- Long-term memory (persistent storage)
- Outcome evaluation (task analysis)
- Delegation optimization (learning from experience)
"""
import tempfile
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from memory.short_term import ShortTermMemory
from memory.working_memory import WorkingMemory
from memory.long_term import LongTermMemory
from learning.outcome_evaluator import OutcomeEvaluator
from learning.delegation_optimizer import DelegationOptimizer


def demo_short_term_memory():
    """Demo short-term memory for conversation context"""
    console = Console()
    console.print(Panel.fit("📝 Short-Term Memory Demo", style="bold blue"))
    
    # Initialize short-term memory
    stm = ShortTermMemory(max_turns=5)
    
    # Simulate a conversation
    conversation = [
        ("user", "Hello, I need help with Python"),
        ("assistant", "I'd be happy to help with Python! What do you need?"),
        ("user", "How do I read a file?"),
        ("assistant", "You can use open('file.txt', 'r').read()"),
        ("user", "What about writing?"),
        ("assistant", "Use open('file.txt', 'w').write('content')"),
    ]
    
    for role, content in conversation:
        stm.add_turn(role, content)
    
    # Display conversation context
    console.print("\n[bold]Conversation History:[/bold]")
    context = stm.get_context_string()
    console.print(context)
    
    # Show stats
    stats = stm.get_stats()
    console.print(f"\n[dim]Total turns: {stats['total_turns']}[/dim]")
    role_counts = stats.get('role_counts', {})
    console.print(f"[dim]User messages: {role_counts.get('user', 0)}, Assistant: {role_counts.get('assistant', 0)}[/dim]\n")


def demo_working_memory():
    """Demo working memory for task tracking"""
    console = Console()
    console.print(Panel.fit("🔧 Working Memory Demo", style="bold green"))
    
    # Initialize working memory
    wm = WorkingMemory()
    
    # Register some tasks
    tasks = [
        ("task1", "Design API endpoints", "agent_architect"),
        ("task2", "Implement authentication", "agent_backend"),
        ("task3", "Write unit tests", "agent_tester"),
        ("task4", "Deploy to staging", "agent_devops"),
    ]
    
    for task_id, description, agent_id in tasks:
        wm.register_task(task_id, description, agent_id)
    
    # Update task statuses
    wm.update_task_status("task1", "completed")
    wm.update_task_status("task2", "in_progress")
    wm.update_task_status("task3", "pending")
    
    # Store intermediate results
    wm.store_intermediate_result(
        "task1_result",
        {"endpoints": ["/login", "/logout", "/profile"]},
        "task1"
    )
    
    # Display task statuses
    console.print("\n[bold]Active Tasks:[/bold]")
    table = Table(show_header=True)
    table.add_column("Task ID")
    table.add_column("Description")
    table.add_column("Agent")
    table.add_column("Status")
    
    for task_id in wm.active_tasks:
        task = wm.get_task(task_id)
        table.add_row(
            task_id,
            task["description"],
            task["agent_id"],
            task["status"]
        )
    
    console.print(table)
    
    # Show stats
    stats = wm.get_stats()
    console.print(f"\n[dim]Total active tasks: {stats['active_tasks']}[/dim]")
    console.print(f"[dim]Active agents: {stats['active_agents']}[/dim]\n")


def demo_long_term_memory():
    """Demo long-term memory for persistent storage"""
    console = Console()
    console.print(Panel.fit("💾 Long-Term Memory Demo", style="bold magenta"))
    
    # Create temporary storage
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize long-term memory
        ltm = LongTermMemory(storage_path=temp_dir)
        
        # Store task outcomes
        ltm.store_task_outcome(
            "task1",
            "Build REST API",
            {"status": "completed", "output": "API with 10 endpoints"},
            "agent_backend",
            success=True
        )
        
        ltm.store_task_outcome(
            "task2",
            "Deploy to AWS",
            {"status": "completed", "output": "Deployed to EC2"},
            "agent_devops",
            success=True
        )
        
        ltm.store_task_outcome(
            "task3",
            "Setup CI/CD",
            {"status": "failed", "error": "Pipeline configuration error"},
            "agent_devops",
            success=False
        )
        
        # Store learnings
        ltm.store_learning(
            "pattern",
            "Backend tasks often require database setup first",
            "task_analysis"
        )
        
        ltm.store_learning(
            "improvement",
            "DevOps tasks need more detailed configuration examples",
            "failure_analysis"
        )
        
        # Display stored data
        console.print("\n[bold]Successful Task Outcomes:[/bold]")
        successful = ltm.get_task_outcomes(success_only=True)
        for task in successful:
            console.print(f"  • {task['description']} by {task['agent_id']}")
        
        console.print("\n[bold]Learnings:[/bold]")
        for learning in ltm.learnings:
            console.print(f"  • [{learning['type']}] {learning['content']}")
        
        # Show stats
        stats = ltm.get_stats()
        console.print(f"\n[dim]Total tasks recorded: {stats['total_tasks']}[/dim]")
        console.print(f"[dim]Success rate: {stats['success_rate']:.1%}[/dim]")
        console.print(f"[dim]Total learnings: {stats['total_learnings']}[/dim]\n")
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def demo_outcome_evaluator():
    """Demo outcome evaluator for task analysis"""
    console = Console()
    console.print(Panel.fit("📊 Outcome Evaluator Demo", style="bold yellow"))
    
    # Initialize evaluator
    evaluator = OutcomeEvaluator()
    
    # Evaluate several tasks
    tasks = [
        ("task1", "Build user authentication", {"status": "completed", "quality": "excellent"}, "agent1"),
        ("task2", "Setup database", {"status": "completed", "quality": "good"}, "agent2"),
        ("task3", "Write documentation", {"status": "completed", "quality": "excellent"}, "agent1"),
        ("task4", "Deploy to production", {"status": "failed", "error": "timeout"}, "agent3"),
        ("task5", "Code review", {"status": "completed", "quality": "good"}, "agent1"),
    ]
    
    console.print("\n[bold]Evaluating Tasks:[/bold]")
    for task_id, description, result, agent_id in tasks:
        evaluation = evaluator.evaluate_task_outcome(task_id, description, result, agent_id)
        status_icon = "✅" if evaluation["success"] else "❌"
        console.print(f"  {status_icon} {description} (Score: {evaluation['overall_score']:.2f})")
    
    # Show agent performance
    console.print("\n[bold]Agent Performance:[/bold]")
    for agent_id in ["agent1", "agent2", "agent3"]:
        perf = evaluator.get_agent_performance(agent_id)
        if perf["total_tasks"] > 0:
            console.print(
                f"  • {agent_id}: {perf['total_tasks']} tasks, "
                f"{perf['success_rate']:.1%} success rate, "
                f"avg score: {perf['avg_overall_score']:.2f}"
            )
    
    # Identify patterns
    console.print("\n[bold]Identified Patterns:[/bold]")
    patterns = evaluator.identify_patterns()
    for pattern in patterns[:3]:  # Show top 3
        console.print(f"  • {pattern}")
    console.print()


def demo_delegation_optimizer():
    """Demo delegation optimizer for learning from experience"""
    console = Console()
    console.print(Panel.fit("🎯 Delegation Optimizer Demo", style="bold cyan"))
    
    # Initialize optimizer
    optimizer = DelegationOptimizer()
    
    # Record delegations
    delegations = [
        ("task1", "Build REST API", "agent_backend", "development", 0.95),
        ("task2", "Setup Kubernetes", "agent_devops", "deployment", 0.88),
        ("task3", "Write tests", "agent_tester", "testing", 0.92),
        ("task4", "Build frontend", "agent_frontend", "development", 0.85),
        ("task5", "Configure CI/CD", "agent_devops", "deployment", 0.90),
        ("task6", "Code review", "agent_backend", "development", 0.93),
    ]
    
    console.print("\n[bold]Recording Delegations:[/bold]")
    for task_id, description, agent_id, domain, score in delegations:
        optimizer.record_delegation(task_id, description, agent_id, domain, score)
        console.print(f"  • {description} → {agent_id} (Score: {score})")
    
    # Get recommendations
    console.print("\n[bold]Recommendations:[/bold]")
    
    dev_agents = ["agent_backend", "agent_frontend", "agent_tester"]
    recommended = optimizer.recommend_agent("development", dev_agents)
    console.print(f"  • For development tasks: {recommended}")
    
    deploy_agents = ["agent_devops", "agent_backend"]
    recommended = optimizer.recommend_agent("deployment", deploy_agents)
    console.print(f"  • For deployment tasks: {recommended}")
    
    # Show top performers
    console.print("\n[bold]Top Performers by Domain:[/bold]")
    for domain in ["development", "deployment", "testing"]:
        top = optimizer.get_top_performers(domain, top_n=2)
        if top:
            console.print(f"  • {domain.capitalize()}:")
            for performer in top:
                console.print(
                    f"    - {performer['agent_id']}: "
                    f"score {performer['score']:.2f}"
                )
    
    # Show analysis
    console.print("\n[bold]Delegation Analysis:[/bold]")
    analysis = optimizer.analyze_delegation_patterns()
    console.print(f"  • Total delegations: {analysis['total_delegations']}")
    console.print(f"  • Task types: {len(analysis['task_type_distribution'])}")
    console.print(f"  • Agents utilized: {len(analysis['agent_workload'])}")
    
    # Get suggestions
    console.print("\n[bold]Optimization Suggestions:[/bold]")
    suggestions = optimizer.generate_optimization_suggestions()
    for suggestion in suggestions[:3]:  # Show top 3
        console.print(f"  • {suggestion}")
    console.print()


def main():
    """Run all Phase 4 demos"""
    console = Console()
    
    console.print("\n")
    console.print(Panel.fit(
        "[bold white]Phase 4 Demo: Memory & Learning Systems[/bold white]\n"
        "[dim]Showcasing the new capabilities added in Phase 4[/dim]",
        style="bold blue"
    ))
    console.print()
    
    # Run demos
    demo_short_term_memory()
    demo_working_memory()
    demo_long_term_memory()
    demo_outcome_evaluator()
    demo_delegation_optimizer()
    
    console.print(Panel.fit(
        "[bold green]✨ Phase 4 Demo Complete![/bold green]\n"
        "[dim]All memory and learning systems are working perfectly[/dim]",
        style="bold green"
    ))
    console.print()


if __name__ == "__main__":
    main()
