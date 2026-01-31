"""
Example: Task Execution with Agent Factory
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.agent_factory import AgentFactory
from persona_library import PersonaLibrary
from personality import BrainClone


def main():
    """Demonstrate automatic agent creation and task execution"""
    
    print("🤖 Agent Factory Example\n")
    
    # Initialize components
    brain_clone = BrainClone()
    persona_library = PersonaLibrary("persona_library/personas/personas.yaml")
    
    factory = AgentFactory(
        persona_library=persona_library,
        personality=brain_clone.get_personality()
    )
    
    # Example 1: Code development task
    print("="*60)
    print("📝 Example 1: Code Development Task")
    print("="*60)
    
    task1 = "Develop a REST API for user authentication"
    context1 = {
        "domain": "Web Development",
        "seniority": "Senior"
    }
    
    agent1 = factory.create_agent(task1, context1)
    print(f"Created agent: {agent1.dna}")
    print(f"Persona ID: {agent1.dna.persona_id}\n")
    
    result1 = agent1.execute_task(task1, context1)
    print(f"Status: {result1['status']}")
    if result1['status'] == 'clarification_needed':
        print("Questions:")
        for q in result1['questions']:
            print(f"  {q}")
    
    # Example 2: Data analysis task
    print("\n" + "="*60)
    print("📊 Example 2: Data Analysis Task")
    print("="*60)
    
    task2 = "Analyze user behavior data and create insights dashboard"
    context2 = {
        "domain": "Data Analytics",
        "seniority": "Senior",
        "budget": "Limited",
        "timeline": "2 weeks"
    }
    
    agent2 = factory.create_agent(task2, context2)
    print(f"Created agent: {agent2.dna}")
    print(f"Persona ID: {agent2.dna.persona_id}\n")
    
    # Example 3: Reusing existing persona
    print("\n" + "="*60)
    print("♻️  Example 3: Reusing Existing Persona")
    print("="*60)
    
    # Try to create same type of agent again
    task3 = "Deploy new microservice to production"
    context3 = {
        "domain": "Web Development",
        "seniority": "Senior"
    }
    
    agent3 = factory.create_agent(task3, context3)
    print(f"Created agent: {agent3.dna}")
    print(f"Persona ID: {agent3.dna.persona_id}")
    
    if agent3.dna.persona_id == agent1.dna.persona_id:
        print("✓ Reused existing persona!")
    else:
        print("✓ Created new persona")
    
    # Show library stats
    print("\n" + "="*60)
    print("📚 Persona Library Stats")
    print("="*60)
    stats = persona_library.get_stats()
    print(f"Total personas: {stats['total_personas']}")
    print(f"Roles: {', '.join(stats['roles'])}")
    print(f"Domains: {', '.join(stats['domains'])}")


if __name__ == "__main__":
    main()
