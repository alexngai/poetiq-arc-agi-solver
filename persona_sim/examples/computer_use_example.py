"""
Example of using the Computer Use agent for enhanced product explanations.

This example demonstrates how the computer use agent can browse documentation,
search code, and gather information to provide more accurate and detailed
explanations during conversations.
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


def create_technical_persona() -> Persona:
    """Create a technically demanding persona."""
    return Persona(
        name="Morgan Technical",
        description="Senior software architect evaluating tools",
        background="Morgan is a senior software architect with 15 years of experience. "
        "Very detail-oriented and asks probing technical questions. Wants to understand "
        "exactly how things work before making decisions.",
        goals=[
            "Understand the technical implementation details",
            "Evaluate architectural fit with existing systems",
            "Identify potential limitations or edge cases",
        ],
        pain_points=[
            "Vendors who can't answer technical questions",
            "Marketing speak without substance",
            "Products that don't integrate well",
        ],
        communication_style="Direct and technical. Asks specific questions about "
        "implementation, scalability, and architecture. Values concrete examples and code.",
        technical_level="expert",
        key_characteristics=[
            "Asks deep technical questions",
            "Wants to see actual code and documentation",
            "Skeptical of marketing claims",
            "Values transparency about limitations",
        ],
        objections=[
            "How does it handle X edge case?",
            "What's the performance at scale?",
            "How does it integrate with our stack?",
        ],
        priorities=[
            "Technical correctness",
            "Scalability and performance",
            "Integration capabilities",
        ],
    )


def create_detailed_strategy() -> CommunicationStrategy:
    """Create a strategy for technical conversations."""
    return CommunicationStrategy(
        name="Technical Deep Dive Strategy",
        description="Engage with technical audiences by providing detailed, accurate "
        "information backed by actual documentation and code examples",
        approach="Listen to technical questions carefully, use tools to find accurate "
        "information from documentation and code, and provide detailed explanations with "
        "concrete examples",
        key_points=[
            "How the system actually works (architecture, algorithms)",
            "Specific code examples and API usage",
            "Performance characteristics and scalability",
            "Integration patterns and compatibility",
            "Known limitations and trade-offs",
        ],
        dos=[
            "Use tools to look up accurate technical details",
            "Show actual code examples from the repository",
            "Reference specific documentation sections",
            "Be honest about limitations and edge cases",
            "Provide architectural diagrams or explanations",
            "Discuss performance implications",
        ],
        donts=[
            "Don't guess or make up technical details",
            "Don't oversimplify complex topics",
            "Don't hide limitations",
            "Don't avoid technical questions",
        ],
        target_outcomes=[
            "Person understands the technical architecture",
            "Person has seen concrete code examples",
            "Person knows how it fits their use case",
            "Person feels confident in the technical details",
        ],
        emphasis_areas=[
            "Technical accuracy",
            "Concrete examples",
            "Integration story",
        ],
        example_phrases=[
            "Let me look up the exact implementation for you...",
            "Here's the specific code from our repository...",
            "According to our documentation on X...",
            "Let me show you how this works in practice...",
        ],
    )


def main():
    """Run a computer use agent example."""
    print("\n" + "=" * 80)
    print("COMPUTER USE AGENT EXAMPLE")
    print("=" * 80 + "\n")

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set!")
        print("Please set it with: export ANTHROPIC_API_KEY='your-key-here'")
        return

    # Create persona and strategy
    print("Creating technical persona and strategy...")
    persona = create_technical_persona()
    strategy = create_detailed_strategy()

    print(f"✓ Persona: {persona.name}")
    print(f"✓ Strategy: {strategy.name}\n")

    # Set allowed paths for the computer use agent
    # This limits which directories the agent can access
    allowed_paths = [
        str(Path(__file__).parent.parent),  # persona_sim directory
        str(Path(__file__).parent.parent.parent / "arc_agi"),  # arc_agi directory for demo
    ]

    print(f"Allowed paths for agent:")
    for path in allowed_paths:
        print(f"  - {path}")
    print()

    # Create simulator with computer use agent
    print("Initializing simulator with COMPUTER USE agent...")
    simulator = PersonaSimulator(
        product_name="Poetiq ARC-AGI Solver",
        product_description="A state-of-the-art AI reasoning system for solving "
        "ARC-AGI benchmark challenges, featuring advanced prompt engineering and "
        "multi-model support.",
        model="claude-sonnet-4-5-20250929",
        temperature=0.7,
    )
    print("✓ Simulator ready\n")

    # Run simulation with computer use agent
    print("Running simulation with COMPUTER USE agent (max 15 turns)...")
    print("The agent can browse files, search code, and read documentation!")
    print("-" * 80 + "\n")

    result = simulator.run_simulation(
        strategy=strategy,
        persona=persona,
        max_turns=15,
        verbose=True,
        interviewer_agent_type="computer_use",  # Use computer use agent!
        allowed_paths=allowed_paths,
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
    print(f"  - Understanding Score: {result.interviewee_eval.questionnaire_score:.1f}/100")

    print("\n" + "=" * 80)
    print("\nKey Difference: The computer use agent can actually browse and read")
    print("files from the repository to answer technical questions accurately!")
    print("\nCompare this to the simple agent which only has knowledge base access.\n")


if __name__ == "__main__":
    main()
