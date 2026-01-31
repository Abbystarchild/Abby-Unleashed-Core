"""
Task Engine Demo - Demonstrates task decomposition and execution planning

This example shows how to:
1. Analyze a complex task
2. Decompose it into subtasks
3. Build dependency graph
4. Create execution plan
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from task_engine import TaskAnalyzer, TaskDecomposer, DependencyMapper, ExecutionPlanner
from rich.console import Console
from rich.tree import Tree
from rich.table import Table

console = Console()


def print_task_analysis(analysis):
    """Print task analysis results."""
    console.print("\n[bold cyan]Task Analysis Results[/bold cyan]")
    console.print(f"Complexity: [yellow]{analysis['complexity'].value}[/yellow]")
    console.print(f"Domains: [green]{', '.join(analysis['domains'])}[/green]")
    console.print(f"Requires Decomposition: [magenta]{analysis['requires_decomposition']}[/magenta]")
    console.print(f"Estimated Subtasks: [blue]{analysis['estimated_subtasks']}[/blue]")


def print_decomposition(result):
    """Print decomposition results as a tree."""
    console.print("\n[bold cyan]Task Decomposition Tree[/bold cyan]")
    
    root_task = result['root_task']
    tree = Tree(f"[bold]{root_task['description']}[/bold]")
    
    for subtask in result['subtasks']:
        task_str = f"[{subtask['domain']}] {subtask['description']}"
        if subtask.get('dependencies'):
            task_str += f" (depends on: {', '.join(subtask['dependencies'])})"
        tree.add(task_str)
    
    console.print(tree)


def print_dependency_map(dep_map):
    """Print dependency map results."""
    console.print("\n[bold cyan]Dependency Analysis[/bold cyan]")
    console.print(f"Has Cycles: [red]{dep_map['has_cycles']}[/red]")
    console.print(f"Execution Order: [green]{' → '.join(dep_map['execution_order'])}[/green]")
    
    if dep_map.get('parallel_groups'):
        console.print("\n[bold]Parallel Execution Groups:[/bold]")
        for i, group in enumerate(dep_map['parallel_groups'], 1):
            can_parallel = "✓ Can parallelize" if len(group) > 1 else "Sequential"
            console.print(f"  Group {i}: {group} - {can_parallel}")


def print_execution_plan(plan):
    """Print execution plan."""
    console.print("\n[bold cyan]Execution Plan[/bold cyan]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Step", style="dim", width=6)
    table.add_column("Tasks")
    table.add_column("Can Parallelize")
    
    for step in plan['steps']:
        table.add_row(
            str(step['step_number']),
            ', '.join(step['tasks']),
            "✓" if step['can_parallelize'] else "✗"
        )
    
    console.print(table)
    console.print(f"\nTotal Steps: [yellow]{plan['total_steps']}[/yellow]")
    console.print(f"Can Parallelize: [green]{plan['can_parallelize']}[/green]")
    console.print(f"Estimated Time: [blue]{plan['estimated_time']} minutes[/blue]")


def main():
    """Main demo function."""
    console.print("[bold green]╔═══════════════════════════════════════════╗[/bold green]")
    console.print("[bold green]║   Task Engine Demonstration               ║[/bold green]")
    console.print("[bold green]╚═══════════════════════════════════════════╝[/bold green]")
    
    # Example task
    task = "Build a complete REST API with user authentication, database integration, and deploy to AWS"
    console.print(f"\n[bold]Task:[/bold] {task}")
    
    # Initialize components
    analyzer = TaskAnalyzer()
    decomposer = TaskDecomposer()
    mapper = DependencyMapper()
    planner = ExecutionPlanner()
    
    # Step 1: Analyze task
    console.print("\n[bold yellow]Step 1: Analyzing Task...[/bold yellow]")
    analysis = analyzer.analyze(task)
    print_task_analysis(analysis)
    
    # Step 2: Decompose task
    console.print("\n[bold yellow]Step 2: Decomposing Task...[/bold yellow]")
    decomposition = decomposer.decompose(analysis)
    print_decomposition(decomposition)
    
    # Step 3: Build dependency graph
    console.print("\n[bold yellow]Step 3: Building Dependency Graph...[/bold yellow]")
    dep_map = mapper.build_graph(decomposition['subtasks'])
    print_dependency_map(dep_map)
    
    # Step 4: Create execution plan
    console.print("\n[bold yellow]Step 4: Creating Execution Plan...[/bold yellow]")
    plan = planner.create_plan(dep_map, decomposition['subtasks'])
    print_execution_plan(plan)
    
    # Step 5: Calculate critical path
    console.print("\n[bold yellow]Step 5: Calculating Critical Path...[/bold yellow]")
    critical_path = planner.get_critical_path(dep_map, decomposition['subtasks'])
    console.print(f"Critical Path: [red]{' → '.join(critical_path)}[/red]")
    
    console.print("\n[bold green]✓ Task Engine Demo Complete![/bold green]")
    
    # Try a simpler task
    console.print("\n" + "="*50)
    simple_task = "Create a simple Python function"
    console.print(f"\n[bold]Simple Task:[/bold] {simple_task}")
    
    simple_analysis = analyzer.analyze(simple_task)
    console.print(f"Complexity: [yellow]{simple_analysis['complexity'].value}[/yellow]")
    console.print(f"Requires Decomposition: [magenta]{simple_analysis['requires_decomposition']}[/magenta]")
    
    console.print("\n[bold green]✓ Done![/bold green]")


if __name__ == "__main__":
    main()
