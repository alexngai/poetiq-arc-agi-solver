"""
Command-line interface for persona simulation.
"""

import argparse
import logging
import json
import yaml
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..models import Persona, CommunicationStrategy
from ..knowledge import build_knowledge_base
from ..optimization import StrategyOptimizer, OptimizationLoop
from .simulator import PersonaSimulator

console = Console()
logger = logging.getLogger(__name__)


def load_personas_from_file(file_path: str) -> List[Persona]:
    """
    Load personas from a YAML or JSON file.

    Args:
        file_path: Path to the file

    Returns:
        List of personas
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Persona file not found: {file_path}")

    with open(path, "r") as f:
        if path.suffix in [".yaml", ".yml"]:
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    personas = []
    for persona_data in data.get("personas", []):
        personas.append(Persona(**persona_data))

    return personas


def load_strategy_from_file(file_path: str) -> CommunicationStrategy:
    """
    Load communication strategy from a YAML or JSON file.

    Args:
        file_path: Path to the file

    Returns:
        Communication strategy
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Strategy file not found: {file_path}")

    with open(path, "r") as f:
        if path.suffix in [".yaml", ".yml"]:
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    return CommunicationStrategy(**data)


def run_simulations(args):
    """Run conversation simulations."""
    console.print("\n[bold blue]Starting Persona Simulations[/bold blue]\n")

    # Load configuration
    personas = load_personas_from_file(args.personas)
    strategy = load_strategy_from_file(args.strategy)

    console.print(f"[green]✓[/green] Loaded {len(personas)} personas")
    console.print(f"[green]✓[/green] Loaded strategy: {strategy.name}\n")

    # Build knowledge base if provided
    knowledge_base = None
    if args.knowledge_dir:
        console.print(f"[yellow]Building knowledge base from {args.knowledge_dir}...[/yellow]")
        knowledge_base = build_knowledge_base(
            source_paths=[args.knowledge_dir],
            persist_directory=args.kb_persist_dir,
            is_directory=True,
        )
        console.print("[green]✓[/green] Knowledge base ready\n")

    # Create simulator
    simulator = PersonaSimulator(
        product_name=args.product_name,
        product_description=args.product_description,
        knowledge_base=knowledge_base,
        model=args.model,
        temperature=args.temperature,
    )

    # Run simulations
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Running {len(personas)} simulations...", total=len(personas)
        )

        results = []
        for persona in personas:
            progress.update(task, description=f"Simulating with {persona.name}...")

            result = simulator.run_simulation(
                strategy=strategy,
                persona=persona,
                max_turns=args.max_turns,
                verbose=args.verbose,
                interviewer_agent_type=args.agent_type,
                allowed_paths=args.allowed_paths,
            )
            results.append(result)

            progress.advance(task)

    # Display results
    console.print("\n[bold green]Simulation Results[/bold green]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Persona")
    table.add_column("Interviewer Score", justify="right")
    table.add_column("Understanding Score", justify="right")
    table.add_column("Turns", justify="right")

    for result in results:
        persona_name = result.conversation.config.interviewee_persona.name
        interviewer_score = f"{result.interviewer_eval.overall_score:.1f}"
        understanding_score = f"{result.interviewee_eval.questionnaire_score:.1f}"
        turns = str(result.conversation.get_turn_count())

        table.add_row(persona_name, interviewer_score, understanding_score, turns)

    console.print(table)

    # Calculate averages
    avg_interviewer = sum(r.interviewer_eval.overall_score for r in results) / len(results)
    avg_understanding = sum(r.interviewee_eval.questionnaire_score for r in results) / len(
        results
    )

    console.print(f"\n[bold]Average Interviewer Score:[/bold] {avg_interviewer:.1f}/100")
    console.print(f"[bold]Average Understanding Score:[/bold] {avg_understanding:.1f}/100\n")

    # Save results
    output_path = simulator.save_results(results, args.output_dir, args.run_name)
    console.print(f"[green]✓[/green] Results saved to {output_path}\n")


def run_optimization(args):
    """Run strategy optimization."""
    console.print("\n[bold blue]Starting Strategy Optimization[/bold blue]\n")

    # Load configuration
    personas = load_personas_from_file(args.personas)
    strategy = load_strategy_from_file(args.strategy)

    console.print(f"[green]✓[/green] Loaded {len(personas)} personas")
    console.print(f"[green]✓[/green] Loaded initial strategy: {strategy.name}\n")

    # Build knowledge base if provided
    knowledge_base = None
    if args.knowledge_dir:
        console.print(f"[yellow]Building knowledge base from {args.knowledge_dir}...[/yellow]")
        knowledge_base = build_knowledge_base(
            source_paths=[args.knowledge_dir],
            persist_directory=args.kb_persist_dir,
            is_directory=True,
        )
        console.print("[green]✓[/green] Knowledge base ready\n")

    # Create simulator and optimizer
    simulator = PersonaSimulator(
        product_name=args.product_name,
        product_description=args.product_description,
        knowledge_base=knowledge_base,
        model=args.model,
        temperature=args.temperature,
    )

    optimizer = StrategyOptimizer(model=args.model)
    opt_loop = OptimizationLoop(optimizer=optimizer, simulator=simulator)

    # Run optimization
    console.print(
        f"[yellow]Running {args.iterations} optimization iterations "
        f"with {args.sims_per_iteration} simulations each...[/yellow]\n"
    )

    result = opt_loop.run_optimization(
        initial_strategy=strategy,
        personas=personas,
        product_name=args.product_name,
        product_description=args.product_description,
        num_iterations=args.iterations,
        sims_per_iteration=args.sims_per_iteration,
    )

    # Display results
    console.print("\n[bold green]Optimization Results[/bold green]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Iteration", justify="right")
    table.add_column("Avg Effectiveness", justify="right")
    table.add_column("Strategy Version")

    for metrics in result.metrics_history:
        table.add_row(
            str(metrics.iteration + 1),
            f"{metrics.avg_overall_effectiveness:.1f}",
            metrics.strategy_version,
        )

    console.print(table)

    console.print(
        f"\n[bold]Improvement:[/bold] {result.improvement_percentage:+.1f}%"
    )
    console.print(f"[bold]Best Iteration:[/bold] {result.best_iteration + 1}\n")

    # Save optimized strategy
    if args.output_strategy:
        output_path = Path(args.output_strategy)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            if output_path.suffix in [".yaml", ".yml"]:
                yaml.dump(result.optimized_strategy.model_dump(), f, indent=2)
            else:
                json.dump(result.optimized_strategy.model_dump(), f, indent=2)

        console.print(f"[green]✓[/green] Optimized strategy saved to {output_path}\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Persona-based conversation simulation and optimization"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Simulate command
    sim_parser = subparsers.add_parser("simulate", help="Run conversation simulations")
    sim_parser.add_argument(
        "--personas",
        required=True,
        help="Path to personas YAML/JSON file",
    )
    sim_parser.add_argument(
        "--strategy",
        required=True,
        help="Path to communication strategy YAML/JSON file",
    )
    sim_parser.add_argument(
        "--product-name",
        required=True,
        help="Name of the product",
    )
    sim_parser.add_argument(
        "--product-description",
        required=True,
        help="Description of the product",
    )
    sim_parser.add_argument(
        "--knowledge-dir",
        help="Directory containing knowledge base documents",
    )
    sim_parser.add_argument(
        "--kb-persist-dir",
        default="./chroma_db",
        help="Directory to persist knowledge base",
    )
    sim_parser.add_argument(
        "--max-turns",
        type=int,
        default=20,
        help="Maximum conversation turns",
    )
    sim_parser.add_argument(
        "--output-dir",
        default="./results",
        help="Output directory for results",
    )
    sim_parser.add_argument(
        "--run-name",
        help="Name for this run",
    )
    sim_parser.add_argument(
        "--model",
        default="claude-sonnet-4-5-20250929",
        help="Anthropic model to use",
    )
    sim_parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature for generation",
    )
    sim_parser.add_argument(
        "--agent-type",
        default="simple",
        choices=["simple", "computer_use"],
        help="Type of interviewer agent (simple or computer_use)",
    )
    sim_parser.add_argument(
        "--allowed-paths",
        nargs="+",
        help="Allowed paths for computer use agents (space-separated list)",
    )
    sim_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print conversations",
    )

    # Optimize command
    opt_parser = subparsers.add_parser("optimize", help="Optimize communication strategy")
    opt_parser.add_argument(
        "--personas",
        required=True,
        help="Path to personas YAML/JSON file",
    )
    opt_parser.add_argument(
        "--strategy",
        required=True,
        help="Path to initial communication strategy YAML/JSON file",
    )
    opt_parser.add_argument(
        "--product-name",
        required=True,
        help="Name of the product",
    )
    opt_parser.add_argument(
        "--product-description",
        required=True,
        help="Description of the product",
    )
    opt_parser.add_argument(
        "--knowledge-dir",
        help="Directory containing knowledge base documents",
    )
    opt_parser.add_argument(
        "--kb-persist-dir",
        default="./chroma_db",
        help="Directory to persist knowledge base",
    )
    opt_parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of optimization iterations",
    )
    opt_parser.add_argument(
        "--sims-per-iteration",
        type=int,
        default=3,
        help="Simulations per iteration",
    )
    opt_parser.add_argument(
        "--output-strategy",
        help="Path to save optimized strategy",
    )
    opt_parser.add_argument(
        "--model",
        default="claude-sonnet-4-5-20250929",
        help="Anthropic model to use",
    )
    opt_parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature for generation",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Route to appropriate handler
    if args.command == "simulate":
        run_simulations(args)
    elif args.command == "optimize":
        run_optimization(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
