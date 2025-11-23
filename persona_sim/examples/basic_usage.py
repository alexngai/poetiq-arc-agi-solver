"""
Basic usage example for the Persona Simulation Framework.

This script demonstrates how to:
1. Create personas and strategies programmatically
2. Run a simple simulation
3. Access and display results
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from persona_sim import (
    PersonaSimulator,
    Persona,
    CommunicationStrategy,
)


def create_example_persona() -> Persona:
    """Create an example persona."""
    return Persona(
        name="Alex Developer",
        description="Full-stack developer at a startup",
        background="Alex is a full-stack developer with 5 years of experience, "
        "currently working at a fast-growing startup. Values efficiency and developer experience.",
        goals=[
            "Write cleaner, more maintainable code",
            "Reduce time spent on repetitive tasks",
            "Learn modern best practices",
        ],
        pain_points=[
            "Spending too much time on code reviews",
            "Inconsistent code quality across the team",
            "Context switching between different tools",
        ],
        communication_style="Technical and direct. Appreciates concrete examples and code snippets.",
        technical_level="intermediate",
        key_characteristics=[
            "Pragmatic and efficiency-focused",
            "Open to new tools if they save time",
            "Wants to see proof it works",
        ],
        objections=[
            "Another tool to learn?",
            "Will this slow down my workflow?",
            "What if it doesn't integrate with my existing setup?",
        ],
        priorities=[
            "Developer productivity",
            "Code quality",
            "Easy integration",
        ],
    )


def create_example_strategy() -> CommunicationStrategy:
    """Create an example communication strategy."""
    return CommunicationStrategy(
        name="Developer-First Approach",
        description="Focus on developer experience and practical benefits",
        approach="Lead with time savings and code quality improvements. "
        "Use technical examples and demonstrate concrete value.",
        key_points=[
            "How much time it saves developers",
            "Specific code quality improvements",
            "Integration with existing tools",
            "Easy onboarding process",
        ],
        dos=[
            "Show concrete code examples",
            "Quantify time savings when possible",
            "Address integration concerns upfront",
            "Demonstrate rather than just explain",
        ],
        donts=[
            "Don't be vague about benefits",
            "Don't ignore their existing workflow",
            "Don't oversell or exaggerate capabilities",
        ],
        target_outcomes=[
            "Developer understands time savings",
            "Developer sees how it fits their workflow",
            "Developer feels integration will be smooth",
        ],
        emphasis_areas=[
            "Developer experience",
            "Time to value",
            "Integration story",
        ],
        example_phrases=[
            "On average, developers save 2-3 hours per week on code reviews",
            "It integrates directly with VS Code and GitHub",
            "You can be up and running in under 5 minutes",
        ],
    )


def main():
    """Run a basic simulation example."""
    print("\n" + "=" * 80)
    print("PERSONA SIMULATION - BASIC EXAMPLE")
    print("=" * 80 + "\n")

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set!")
        print("Please set it with: export ANTHROPIC_API_KEY='your-key-here'")
        return

    # Create persona and strategy
    print("Creating persona and strategy...")
    persona = create_example_persona()
    strategy = create_example_strategy()

    print(f"✓ Persona: {persona.name}")
    print(f"✓ Strategy: {strategy.name}\n")

    # Create simulator
    print("Initializing simulator...")
    simulator = PersonaSimulator(
        product_name="CodeReview AI",
        product_description="An AI-powered code review assistant that automatically "
        "reviews pull requests, suggests improvements, and ensures code quality.",
        model="claude-sonnet-4-5-20250929",
        temperature=0.7,
    )
    print("✓ Simulator ready\n")

    # Run simulation
    print("Running simulation (max 10 turns)...")
    print("-" * 80 + "\n")

    result = simulator.run_simulation(
        strategy=strategy,
        persona=persona,
        max_turns=10,
        verbose=True,  # Print the conversation
    )

    print("\n" + "-" * 80)
    print("\nSIMULATION COMPLETE!\n")

    # Display results
    print("=" * 80)
    print("EVALUATION RESULTS")
    print("=" * 80 + "\n")

    print(f"Interviewer Performance: {result.interviewer_eval.overall_score:.1f}/100")
    print(f"  - Strategy Adherence: {result.interviewer_eval.strategy_adherence_score:.1f}/100")

    if result.interviewer_eval.strengths:
        print("\n  Strengths:")
        for strength in result.interviewer_eval.strengths:
            print(f"    • {strength}")

    if result.interviewer_eval.weaknesses:
        print("\n  Weaknesses:")
        for weakness in result.interviewer_eval.weaknesses:
            print(f"    • {weakness}")

    print(f"\nInterviewee Performance: {result.interviewee_eval.overall_score:.1f}/100")
    print(f"  - Persona Adherence: {result.interviewee_eval.persona_adherence_score:.1f}/100")
    print(f"  - Understanding Score: {result.interviewee_eval.questionnaire_score:.1f}/100")

    print("\n" + "=" * 80)
    print("QUESTIONNAIRE RESPONSES")
    print("=" * 80 + "\n")

    for q_id, answer in result.questionnaire_response.answers.items():
        print(f"Q: {q_id}")
        print(f"A: {answer}\n")

    print("=" * 80)
    print("\nExample complete! Check the conversation transcript above to see")
    print("how the interviewer and interviewee interacted.\n")

    # Optionally save results
    save = input("Save results to file? (y/n): ").strip().lower()
    if save == 'y':
        output_path = simulator.save_results(
            [result],
            output_dir="./example_results",
            run_name="basic_example",
        )
        print(f"\n✓ Results saved to {output_path}")


if __name__ == "__main__":
    main()
