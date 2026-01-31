"""
Example: Using Persona Library
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents import AgentDNA
from persona_library import PersonaLibrary
from personality import BrainClone


def main():
    """Demonstrate persona library usage"""
    
    print("🗂️  Persona Library Example\n")
    
    # Initialize
    library = PersonaLibrary("persona_library/personas/personas.yaml")
    brain_clone = BrainClone()
    
    print(f"📚 Current library stats:")
    stats = library.get_stats()
    print(f"  - Total personas: {stats['total_personas']}")
    print(f"  - Roles: {', '.join(stats['roles']) if stats['roles'] else 'None'}")
    print(f"  - Domains: {', '.join(stats['domains']) if stats['domains'] else 'None'}\n")
    
    # Create a new persona
    print("➕ Creating new DevOps persona...")
    devops_dna = AgentDNA(
        role="DevOps Engineer",
        seniority="Senior",
        domain="Cloud Infrastructure (AWS/Kubernetes)",
        industry_knowledge=[
            "AWS Well-Architected Framework",
            "Kubernetes best practices",
            "Infrastructure as Code (IaC)",
            "Cost optimization"
        ],
        methodologies=[
            "GitOps with ArgoCD",
            "Blue-green deployments",
            "Terraform for IaC"
        ],
        constraints={
            "cost": "< $500/month for dev",
            "security": "Private subnets only",
            "automation": "Everything in code"
        },
        output_format={
            "code": "Terraform modules",
            "docs": "Markdown",
            "diagrams": "Mermaid"
        }
    )
    
    # Save to library
    library.save(devops_dna)
    print(f"✓ Saved persona: {devops_dna.persona_id}\n")
    
    # Search for match
    print("🔍 Searching for DevOps persona...")
    requirements = {
        "role": "DevOps Engineer",
        "domain": "Cloud Infrastructure (AWS/Kubernetes)"
    }
    
    match = library.find_match(requirements)
    
    if match:
        print(f"✓ Found match: {match.persona_id}")
        print(f"  - Role: {match.role}")
        print(f"  - Domain: {match.domain}")
        print(f"  - Times used: {match.times_used}")
    else:
        print("✗ No match found")
    
    # List all personas
    print(f"\n📋 All personas in library:")
    for persona in library.list_all():
        print(f"  - {persona.seniority} {persona.role} ({persona.domain})")
        print(f"    ID: {persona.persona_id}")
        print(f"    Used: {persona.times_used} times\n")


if __name__ == "__main__":
    main()
