#!/usr/bin/env python3
"""
Engram Creator CLI - Interactive tool for creating personality engrams

This tool walks you through a comprehensive questionnaire to create
an accurate digital clone of your personality based on:

1. Big Five (OCEAN) Personality Traits
2. Communication Style Preferences
3. Core Values and Decision-Making Patterns
4. Knowledge, Expertise, and Interests
5. Writing Sample Analysis

Usage:
    python create_engram.py                    # Interactive mode
    python create_engram.py --name "Your Name" # Start with name
    python create_engram.py --analyze text.txt # Analyze writing sample
"""

import argparse
import os
import sys
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from personality.engram_builder import (
    EngramBuilder, Engram, OceanTraits, CommunicationStyle,
    ValueSystem, DecisionMakingStyle, KnowledgeBase, LinguisticPatterns
)


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_section(text: str):
    """Print a section header"""
    print(f"\n--- {text} ---\n")


def get_scale_input(prompt: str, min_val: int = 1, max_val: int = 5) -> int:
    """Get a numeric input within a range"""
    while True:
        try:
            value = input(f"{prompt} ({min_val}-{max_val}): ").strip()
            if not value:
                return (min_val + max_val) // 2  # Default to middle
            num = int(value)
            if min_val <= num <= max_val:
                return num
            print(f"Please enter a number between {min_val} and {max_val}")
        except ValueError:
            print("Please enter a valid number")


def get_list_input(prompt: str) -> List[str]:
    """Get a comma-separated list input"""
    print(prompt)
    value = input("(comma-separated): ").strip()
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def get_choice_input(prompt: str, options: List[str]) -> str:
    """Get a choice from options"""
    print(f"{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    
    while True:
        try:
            value = input("Enter number or name: ").strip().lower()
            if not value:
                return options[0]  # Default to first
            
            # Try numeric
            try:
                num = int(value)
                if 1 <= num <= len(options):
                    return options[num - 1]
            except ValueError:
                pass
            
            # Try name match
            for opt in options:
                if opt.lower() == value or opt.lower().startswith(value):
                    return opt
            
            print(f"Please choose from: {', '.join(options)}")
        except Exception:
            print("Invalid input, please try again")


def run_ocean_questionnaire(builder: EngramBuilder) -> OceanTraits:
    """Run the OCEAN personality questionnaire"""
    print_header("Part 1: Personality Traits (OCEAN Model)")
    print("Rate each question on a scale of 1-5")
    print("1 = Strongly disagree/Never, 5 = Strongly agree/Always\n")
    
    questionnaire = builder.get_ocean_questionnaire()
    responses: Dict[str, List[int]] = {}
    
    for section in questionnaire:
        trait = section['trait']
        print_section(trait.replace('_', ' ').title())
        
        scores = []
        for q in section['questions']:
            score = get_scale_input(q)
            scores.append(score)
        
        responses[trait] = scores
    
    return builder.process_ocean_responses(responses)


def run_communication_questionnaire(builder: EngramBuilder) -> CommunicationStyle:
    """Run the communication style questionnaire"""
    print_header("Part 2: Communication Style")
    
    style = CommunicationStyle()
    
    style.formality = (get_scale_input("How formal is your communication style? (1=casual, 5=formal)") - 1) * 25
    style.verbosity = (get_scale_input("How detailed are your explanations? (1=brief, 5=elaborate)") - 1) * 25
    style.directness = (get_scale_input("How direct are you? (1=diplomatic, 5=blunt)") - 1) * 25
    style.humor_level = (get_scale_input("How often do you use humor? (1=rarely, 5=constantly)") - 1) * 25
    
    style.humor_style = get_choice_input(
        "What type of humor do you prefer?",
        ["dry", "witty", "sarcastic", "puns", "observational", "self-deprecating"]
    )
    
    style.sentence_length_preference = get_choice_input(
        "What's your preferred sentence length?",
        ["short", "medium", "long", "varied"]
    )
    
    style.technical_jargon_comfort = (get_scale_input("Comfort with technical jargon? (1=avoid, 5=love it)") - 1) * 25
    
    style.favorite_expressions = get_list_input("What phrases do you commonly use?")
    
    style.greeting_style = get_choice_input(
        "How do you typically greet people?",
        ["formal", "casual", "warm", "professional"]
    )
    
    if builder.current_engram:
        builder.current_engram.communication_style = style
    
    return style


def run_values_questionnaire(builder: EngramBuilder) -> ValueSystem:
    """Run the values and priorities questionnaire"""
    print_header("Part 3: Values & Decision Making")
    
    values = ValueSystem()
    
    values.core_values = get_list_input("What are your top 5 core values? (e.g., honesty, creativity, family)")
    values.deal_breakers = get_list_input("What are your non-negotiables/deal-breakers?")
    values.motivators = get_list_input("What motivates you most?")
    
    values.work_life_balance_priority = (get_scale_input("Work-life balance: (1=work-focused, 5=life-focused)") - 1) * 25
    values.autonomy_preference = (get_scale_input("How much do you value independence? (1=like guidance, 5=fiercely independent)") - 1) * 25
    values.data_vs_intuition = (get_scale_input("Decision style: (1=trust gut, 5=need data)") - 1) * 25
    values.risk_tolerance = (get_scale_input("Risk tolerance: (1=risk averse, 5=risk seeking)") - 1) * 25
    
    if builder.current_engram:
        builder.current_engram.value_system = values
    
    return values


def run_decision_questionnaire(builder: EngramBuilder) -> DecisionMakingStyle:
    """Run the decision-making style questionnaire"""
    print_section("Decision Making Style")
    
    dm = DecisionMakingStyle()
    
    dm.problem_solving_style = get_choice_input(
        "What's your problem-solving approach?",
        ["analytical", "intuitive", "collaborative", "experimental"]
    )
    
    dm.when_stuck_behavior = get_choice_input(
        "When you're stuck, what do you do?",
        ["research", "ask_others", "trial_error", "step_away"]
    )
    
    dm.failure_response = get_choice_input(
        "How do you respond to failure?",
        ["analyze", "learn", "move_on", "dwell"]
    )
    
    dm.analysis_paralysis_tendency = (get_scale_input("Do you overthink decisions? (1=quick decider, 5=overthinker)") - 1) * 25
    
    if builder.current_engram:
        builder.current_engram.decision_making = dm
    
    return dm


def run_knowledge_questionnaire(builder: EngramBuilder) -> KnowledgeBase:
    """Run the knowledge and background questionnaire"""
    print_header("Part 4: Knowledge & Background")
    
    kb = KnowledgeBase()
    
    kb.expertise_areas = get_list_input("What are your areas of expertise?")
    kb.interests = get_list_input("What are your hobbies and interests?")
    kb.background_facts = get_list_input("Key background facts (career, education, experiences)")
    kb.pet_peeves = get_list_input("What are your pet peeves?")
    
    # Optional: specific preferences
    print("\nOptional: Any specific preferences?")
    pref_categories = ["coding style", "music", "food", "work environment"]
    for cat in pref_categories:
        pref = input(f"  {cat.title()} preference (or press Enter to skip): ").strip()
        if pref:
            kb.preferences[cat] = pref
    
    if builder.current_engram:
        builder.current_engram.knowledge_base = kb
    
    return kb


def analyze_writing_sample(builder: EngramBuilder, filepath: str) -> LinguisticPatterns:
    """Analyze a writing sample file"""
    print_header("Analyzing Writing Sample")
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return LinguisticPatterns()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"Analyzing {len(text)} characters...")
    patterns = builder.analyze_writing_sample(text)
    
    print("\nExtracted Patterns:")
    print(f"  Vocabulary complexity: {patterns.vocabulary_complexity}/100")
    print(f"  Sentence style: {patterns.sentence_length_preference}")
    print(f"  Contraction usage: {patterns.contraction_usage}%")
    print(f"  Active voice tendency: {patterns.active_vs_passive}%")
    print(f"  Common words: {', '.join(patterns.common_words[:10])}")
    
    return patterns


def run_interactive_creation():
    """Run the full interactive engram creation process"""
    print_header("🧠 ENGRAM CREATOR - Digital Personality Clone Builder")
    print("""
Welcome! This tool will create an accurate digital model of your personality.

The process takes about 10-15 minutes and covers:
• Personality traits (OCEAN model)
• Communication style
• Values and decision-making
• Knowledge and interests
• Optional: Writing sample analysis

Your answers help create a system that thinks and responds like you would.
Press Enter to use default values, or type 'q' to quit at any time.
""")
    
    # Get name
    name = input("What name should your digital clone use? ").strip()
    if not name:
        name = "User"
    if name.lower() == 'q':
        print("Exiting...")
        return
    
    # Initialize builder
    builder = EngramBuilder()
    engram = builder.start_new_engram(name)
    
    print(f"\nGreat! Let's create {name}'s engram.\n")
    
    try:
        # Run questionnaires
        run_ocean_questionnaire(builder)
        run_communication_questionnaire(builder)
        run_values_questionnaire(builder)
        run_decision_questionnaire(builder)
        run_knowledge_questionnaire(builder)
        
        # Optional writing analysis
        print_section("Writing Sample Analysis (Optional)")
        sample_path = input("Path to a text file with your writing (or press Enter to skip): ").strip()
        if sample_path and os.path.exists(sample_path):
            analyze_writing_sample(builder, sample_path)
        
        # Save engram
        print_header("Saving Your Engram")
        filepath = builder.save_engram()
        print(f"✓ Engram saved to: {filepath}")
        
        # Generate and show system prompt
        print_header("Generated System Prompt Preview")
        prompt = builder.generate_system_prompt()
        print(prompt[:1000])
        if len(prompt) > 1000:
            print(f"\n... ({len(prompt) - 1000} more characters)")
        
        # Update brain_clone.yaml
        print_section("Updating Personality Configuration")
        export_data = builder.export_for_brain_clone()
        
        import yaml
        config_path = "config/brain_clone.yaml"
        os.makedirs("config", exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        print(f"✓ Configuration updated: {config_path}")
        
        print_header("🎉 Engram Creation Complete!")
        print(f"""
Your digital personality clone has been created!

Files created:
• Engram data: {filepath}
• Config file: {config_path}

To use your new personality:
1. Restart the Abby server
2. Or set ENGRAM_PATH environment variable to: {filepath}

Your AI will now respond with your personality traits, communication style,
and decision-making patterns!
""")
        
    except KeyboardInterrupt:
        print("\n\nEngram creation cancelled.")
    except Exception as e:
        print(f"\nError: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Create a personality engram for your digital clone",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_engram.py                     # Interactive mode
  python create_engram.py --name "John Doe"   # Start with a name
  python create_engram.py --analyze emails.txt # Analyze writing sample
  python create_engram.py --questionnaire     # Print full questionnaire
        """
    )
    
    parser.add_argument('--name', help='Name for the engram subject')
    parser.add_argument('--analyze', metavar='FILE', help='Analyze a writing sample file')
    parser.add_argument('--questionnaire', action='store_true', help='Print full questionnaire')
    parser.add_argument('--output', metavar='FILE', help='Output file path')
    
    args = parser.parse_args()
    
    if args.questionnaire:
        builder = EngramBuilder()
        builder.start_new_engram("User")
        from personality.engram_builder import InteractiveEngramCreator
        creator = InteractiveEngramCreator()
        print(creator.get_all_questions_formatted())
        return
    
    if args.analyze:
        builder = EngramBuilder()
        analyze_writing_sample(builder, args.analyze)
        return
    
    # Run interactive mode
    run_interactive_creation()


if __name__ == '__main__':
    main()
