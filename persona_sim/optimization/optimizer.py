"""
DSPy-based optimization framework for improving communication strategies.
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import dspy
from dspy.teleprompt import BootstrapFewShot

from ..models import (
    CommunicationStrategy,
    SimulationResult,
    OptimizationMetrics,
    OptimizationResult,
)

logger = logging.getLogger(__name__)


class StrategyImprover(dspy.Signature):
    """
    DSPy signature for improving communication strategies based on feedback.
    """

    original_strategy = dspy.InputField(desc="The original communication strategy")
    feedback = dspy.InputField(desc="Evaluation feedback and performance metrics")
    product_context = dspy.InputField(desc="Context about the product and goals")

    improved_strategy = dspy.OutputField(
        desc="An improved version of the communication strategy with specific, actionable changes"
    )
    reasoning = dspy.OutputField(desc="Explanation of what was changed and why")


class StrategyOptimizer:
    """
    Optimizer for communication strategies using DSPy.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize the strategy optimizer.

        Args:
            model: Anthropic model to use
            anthropic_api_key: API key for Anthropic
        """
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        # Configure DSPy to use Anthropic
        lm = dspy.LM(
            model=f"anthropic/{model}",
            api_key=api_key,
            temperature=0.7,
        )
        dspy.configure(lm=lm)

        self.improver = dspy.ChainOfThought(StrategyImprover)

    def improve_strategy(
        self,
        current_strategy: CommunicationStrategy,
        simulation_results: List[SimulationResult],
        product_name: str,
        product_description: str,
    ) -> Tuple[CommunicationStrategy, str]:
        """
        Improve a communication strategy based on simulation results.

        Args:
            current_strategy: The current communication strategy
            simulation_results: Results from recent simulations
            product_name: Name of the product
            product_description: Description of the product

        Returns:
            Tuple of (improved strategy, reasoning)
        """
        # Aggregate feedback from simulation results
        feedback = self._aggregate_feedback(simulation_results)

        # Build product context
        product_context = f"""Product: {product_name}
Description: {product_description}

Target Outcomes:
{chr(10).join(f"- {outcome}" for outcome in current_strategy.target_outcomes)}"""

        # Use DSPy to generate improved strategy
        try:
            result = self.improver(
                original_strategy=current_strategy.to_prompt(),
                feedback=feedback,
                product_context=product_context,
            )

            # Parse the improved strategy
            improved_strategy = self._parse_improved_strategy(
                result.improved_strategy,
                current_strategy,
            )

            return improved_strategy, result.reasoning

        except Exception as e:
            logger.error(f"Error improving strategy: {e}")
            # Return original strategy if improvement fails
            return current_strategy, f"Error during optimization: {e}"

    def _aggregate_feedback(self, results: List[SimulationResult]) -> str:
        """
        Aggregate feedback from multiple simulation results.

        Args:
            results: List of simulation results

        Returns:
            Aggregated feedback string
        """
        if not results:
            return "No simulation results available."

        # Calculate average scores
        avg_interviewer_score = sum(r.interviewer_eval.overall_score for r in results) / len(
            results
        )
        avg_interviewee_understanding = sum(
            r.interviewee_eval.questionnaire_score for r in results
        ) / len(results)
        avg_strategy_adherence = sum(
            r.interviewer_eval.strategy_adherence_score for r in results
        ) / len(results)

        # Collect common strengths and weaknesses
        all_strengths = []
        all_weaknesses = []
        all_suggestions = []

        for result in results:
            all_strengths.extend(result.interviewer_eval.strengths)
            all_weaknesses.extend(result.interviewer_eval.weaknesses)
            all_suggestions.extend(result.interviewer_eval.suggestions)

        # Count frequencies
        strength_counts = {}
        weakness_counts = {}
        suggestion_counts = {}

        for s in all_strengths:
            strength_counts[s] = strength_counts.get(s, 0) + 1
        for w in all_weaknesses:
            weakness_counts[w] = weakness_counts.get(w, 0) + 1
        for sg in all_suggestions:
            suggestion_counts[sg] = suggestion_counts.get(sg, 0) + 1

        # Get top items
        top_strengths = sorted(strength_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_weaknesses = sorted(weakness_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_suggestions = sorted(suggestion_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        feedback = f"""PERFORMANCE METRICS (across {len(results)} simulations):
- Average Interviewer Score: {avg_interviewer_score:.1f}/100
- Average Strategy Adherence: {avg_strategy_adherence:.1f}/100
- Average Interviewee Understanding: {avg_interviewee_understanding:.1f}/100

TOP STRENGTHS:
{chr(10).join(f"- {s[0]} (mentioned {s[1]} times)" for s in top_strengths)}

TOP WEAKNESSES:
{chr(10).join(f"- {w[0]} (mentioned {w[1]} times)" for w in top_weaknesses)}

TOP SUGGESTIONS FOR IMPROVEMENT:
{chr(10).join(f"- {sg[0]} (mentioned {sg[1]} times)" for sg in top_suggestions)}

SPECIFIC ISSUES OBSERVED:
"""

        # Add specific examples from individual results
        for i, result in enumerate(results[:3], 1):  # Show first 3 examples
            persona_name = result.conversation.config.interviewee_persona.name
            feedback += f"\nExample {i} (with {persona_name}):\n"
            feedback += f"  Interviewer Score: {result.interviewer_eval.overall_score:.1f}\n"
            if result.interviewer_eval.weaknesses:
                feedback += f"  Key Issue: {result.interviewer_eval.weaknesses[0]}\n"

        return feedback

    def _parse_improved_strategy(
        self,
        improved_text: str,
        original_strategy: CommunicationStrategy,
    ) -> CommunicationStrategy:
        """
        Parse improved strategy text into a CommunicationStrategy object.

        Args:
            improved_text: Text description of improved strategy
            original_strategy: Original strategy to base improvements on

        Returns:
            Updated CommunicationStrategy
        """
        # This is a simplified parser - in practice, you might want more sophisticated parsing
        # For now, we'll use DSPy to help structure the output

        try:
            # Use another DSPy module to structure the strategy
            strategy_dict = self._extract_strategy_components(improved_text)

            return CommunicationStrategy(
                name=f"{original_strategy.name} (Optimized v{datetime.now().strftime('%Y%m%d%H%M')})",
                description=strategy_dict.get("description", original_strategy.description),
                key_points=strategy_dict.get("key_points", original_strategy.key_points),
                approach=strategy_dict.get("approach", original_strategy.approach),
                dos=strategy_dict.get("dos", original_strategy.dos),
                donts=strategy_dict.get("donts", original_strategy.donts),
                target_outcomes=original_strategy.target_outcomes,
                emphasis_areas=strategy_dict.get(
                    "emphasis_areas", original_strategy.emphasis_areas
                ),
                example_phrases=strategy_dict.get(
                    "example_phrases", original_strategy.example_phrases
                ),
            )

        except Exception as e:
            logger.warning(f"Error parsing improved strategy: {e}. Using original.")
            # Return slightly modified original if parsing fails
            return CommunicationStrategy(
                name=f"{original_strategy.name} (Attempted Optimization)",
                description=original_strategy.description + f"\n\nSuggested improvements: {improved_text[:200]}...",
                key_points=original_strategy.key_points,
                approach=original_strategy.approach,
                dos=original_strategy.dos,
                donts=original_strategy.donts,
                target_outcomes=original_strategy.target_outcomes,
                emphasis_areas=original_strategy.emphasis_areas,
                example_phrases=original_strategy.example_phrases,
            )

    def _extract_strategy_components(self, improved_text: str) -> Dict:
        """
        Extract structured components from improved strategy text.

        Args:
            improved_text: Text description of improved strategy

        Returns:
            Dictionary of strategy components
        """
        # Simple extraction based on common patterns
        components = {}

        # Try to extract different sections
        sections = {
            "description": ["description:", "overview:"],
            "approach": ["approach:", "method:"],
            "key_points": ["key points:", "main points:"],
            "dos": ["do:", "dos:", "should:"],
            "donts": ["don't:", "donts:", "avoid:", "shouldn't:"],
            "emphasis_areas": ["emphasize:", "focus on:", "highlight:"],
            "example_phrases": ["examples:", "phrases:", "say things like:"],
        }

        text_lower = improved_text.lower()

        for component, markers in sections.items():
            for marker in markers:
                if marker in text_lower:
                    # Find the section
                    start_idx = text_lower.index(marker)
                    # Find end (next section or end of text)
                    end_idx = len(improved_text)
                    for other_markers in sections.values():
                        for other_marker in other_markers:
                            if other_marker in text_lower[start_idx + len(marker):]:
                                potential_end = text_lower.index(
                                    other_marker, start_idx + len(marker)
                                )
                                if potential_end < end_idx:
                                    end_idx = potential_end

                    # Extract and clean the section
                    section_text = improved_text[start_idx + len(marker):end_idx].strip()

                    # Parse as list if it looks like a list
                    if "\n-" in section_text or "\n*" in section_text:
                        items = [
                            line.strip().lstrip("-*").strip()
                            for line in section_text.split("\n")
                            if line.strip() and line.strip()[0] in "-*"
                        ]
                        components[component] = items
                    else:
                        # Single string for description/approach
                        components[component] = section_text.split("\n")[0].strip()

                    break

        return components


class OptimizationLoop:
    """
    Manages the optimization loop for communication strategies.
    """

    def __init__(
        self,
        optimizer: StrategyOptimizer,
        simulator: any,  # Will be the main simulator
    ):
        """
        Initialize the optimization loop.

        Args:
            optimizer: Strategy optimizer
            simulator: Conversation simulator
        """
        self.optimizer = optimizer
        self.simulator = simulator
        self.metrics_history: List[OptimizationMetrics] = []

    def run_optimization(
        self,
        initial_strategy: CommunicationStrategy,
        personas: List,
        product_name: str,
        product_description: str,
        num_iterations: int = 5,
        sims_per_iteration: int = 3,
    ) -> OptimizationResult:
        """
        Run the optimization loop.

        Args:
            initial_strategy: Initial communication strategy
            personas: List of personas to test against
            product_name: Name of the product
            product_description: Description of the product
            num_iterations: Number of optimization iterations
            sims_per_iteration: Number of simulations per iteration

        Returns:
            Optimization result
        """
        current_strategy = initial_strategy
        best_strategy = initial_strategy
        best_score = 0.0
        best_iteration = 0

        logger.info(f"Starting optimization loop: {num_iterations} iterations")

        for iteration in range(num_iterations):
            logger.info(f"Optimization iteration {iteration + 1}/{num_iterations}")

            # Run simulations with current strategy
            results = []
            for persona in personas[:sims_per_iteration]:
                result = self.simulator.run_simulation(
                    strategy=current_strategy,
                    persona=persona,
                )
                results.append(result)

            # Calculate metrics
            avg_interviewer_score = sum(r.interviewer_eval.overall_score for r in results) / len(
                results
            )
            avg_understanding_score = sum(
                r.interviewee_eval.questionnaire_score for r in results
            ) / len(results)
            avg_effectiveness = (avg_interviewer_score + avg_understanding_score) / 2

            metrics = OptimizationMetrics(
                iteration=iteration,
                avg_interviewer_score=avg_interviewer_score,
                avg_interviewee_understanding_score=avg_understanding_score,
                avg_overall_effectiveness=avg_effectiveness,
                strategy_version=current_strategy.name,
            )
            self.metrics_history.append(metrics)

            logger.info(
                f"Iteration {iteration + 1} - Effectiveness: {avg_effectiveness:.1f}"
            )

            # Track best strategy
            if avg_effectiveness > best_score:
                best_score = avg_effectiveness
                best_strategy = current_strategy
                best_iteration = iteration

            # Improve strategy for next iteration (except on last iteration)
            if iteration < num_iterations - 1:
                improved_strategy, reasoning = self.optimizer.improve_strategy(
                    current_strategy=current_strategy,
                    simulation_results=results,
                    product_name=product_name,
                    product_description=product_description,
                )

                logger.info(f"Strategy improvement reasoning: {reasoning[:200]}...")
                current_strategy = improved_strategy

        # Calculate improvement
        initial_score = self.metrics_history[0].avg_overall_effectiveness
        final_score = self.metrics_history[-1].avg_overall_effectiveness
        improvement_pct = (
            ((final_score - initial_score) / initial_score * 100) if initial_score > 0 else 0
        )

        return OptimizationResult(
            initial_strategy=initial_strategy,
            optimized_strategy=best_strategy,
            metrics_history=self.metrics_history,
            improvement_percentage=improvement_pct,
            best_iteration=best_iteration,
        )
