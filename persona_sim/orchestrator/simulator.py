"""
Main simulator orchestrator that coordinates all components.
"""

import logging
import os
import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from ..models import (
    ConversationConfig,
    Persona,
    CommunicationStrategy,
    Questionnaire,
    SimulationResult,
)
from ..agents import IntervieweeAgent, create_interviewer_agent
from ..conversation import ConversationEngine
from ..knowledge import KnowledgeBase, build_knowledge_base
from ..evaluation import (
    QuestionnaireGenerator,
    QuestionnaireAdministrator,
    ConversationJudge,
)

logger = logging.getLogger(__name__)


class PersonaSimulator:
    """
    Main orchestrator for persona-based conversation simulations.
    """

    def __init__(
        self,
        product_name: str,
        product_description: str,
        knowledge_base: Optional[KnowledgeBase] = None,
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.7,
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize the persona simulator.

        Args:
            product_name: Name of the product
            product_description: Description of the product
            knowledge_base: Optional knowledge base for product information
            model: Anthropic model to use
            temperature: Temperature for generation
            anthropic_api_key: API key for Anthropic
        """
        self.product_name = product_name
        self.product_description = product_description
        self.knowledge_base = knowledge_base
        self.model = model
        self.temperature = temperature
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")

        # Initialize components
        self.questionnaire_generator = QuestionnaireGenerator(
            model=model,
            anthropic_api_key=self.anthropic_api_key,
        )

        self.questionnaire_admin = QuestionnaireAdministrator(
            model=model,
            anthropic_api_key=self.anthropic_api_key,
        )

        self.judge = ConversationJudge(
            model=model,
            anthropic_api_key=self.anthropic_api_key,
        )

    def run_simulation(
        self,
        strategy: CommunicationStrategy,
        persona: Persona,
        max_turns: int = 20,
        questionnaire: Optional[Questionnaire] = None,
        verbose: bool = True,
        interviewer_agent_type: str = "simple",
        allowed_paths: Optional[List[str]] = None,
    ) -> SimulationResult:
        """
        Run a single conversation simulation.

        Args:
            strategy: Communication strategy for interviewer
            persona: Persona for interviewee
            max_turns: Maximum conversation turns
            questionnaire: Optional pre-defined questionnaire
            verbose: Whether to print conversation progress
            interviewer_agent_type: Type of interviewer agent ("simple", "computer_use", etc.)
            allowed_paths: Allowed paths for computer use agents

        Returns:
            Simulation result
        """
        logger.info(f"Starting simulation with persona: {persona.name}")
        logger.info(f"Using interviewer agent type: {interviewer_agent_type}")

        # Create conversation configuration
        config = ConversationConfig(
            max_turns=max_turns,
            interviewee_persona=persona,
            strategy=strategy,
            product_name=self.product_name,
            product_description=self.product_description,
            temperature=self.temperature,
            model=self.model,
            interviewer_agent_type=interviewer_agent_type,
            allowed_paths=allowed_paths,
        )

        # Create agents using factory
        interviewer = create_interviewer_agent(
            agent_type=interviewer_agent_type,
            strategy=strategy,
            knowledge_base=self.knowledge_base,
            product_name=self.product_name,
            product_description=self.product_description,
            allowed_paths=allowed_paths,
            model=self.model,
            temperature=self.temperature,
            anthropic_api_key=self.anthropic_api_key,
        )

        interviewee = IntervieweeAgent(
            persona=persona,
            product_name=self.product_name,
            model=self.model,
            temperature=self.temperature,
            anthropic_api_key=self.anthropic_api_key,
        )

        # Create conversation engine
        engine = ConversationEngine(
            config=config,
            interviewer_agent=interviewer,
            interviewee_agent=interviewee,
        )

        # Run conversation
        conversation = engine.run_conversation(verbose=verbose)

        # Generate or use provided questionnaire
        if questionnaire is None:
            questionnaire = self.questionnaire_generator.generate_questionnaire(
                product_name=self.product_name,
                product_description=self.product_description,
                key_concepts=strategy.key_points,
                num_questions=8,
            )

        # Administer questionnaire
        questionnaire_response = self.questionnaire_admin.administer_questionnaire(
            questionnaire=questionnaire,
            conversation=conversation,
            persona=persona,
        )

        # Evaluate interviewer
        interviewer_eval = self.judge.evaluate_interviewer(
            conversation=conversation,
            strategy=strategy,
        )

        # Evaluate interviewee
        interviewee_eval = self.judge.evaluate_interviewee(
            conversation=conversation,
            persona=persona,
            questionnaire_response=questionnaire_response,
            questionnaire=questionnaire,
        )

        # Create simulation result
        result = SimulationResult(
            conversation=conversation,
            questionnaire_response=questionnaire_response,
            interviewer_eval=interviewer_eval,
            interviewee_eval=interviewee_eval,
        )

        logger.info(
            f"Simulation complete. Interviewer score: {interviewer_eval.overall_score:.1f}, "
            f"Interviewee understanding: {interviewee_eval.questionnaire_score:.1f}"
        )

        return result

    def run_batch_simulations(
        self,
        strategy: CommunicationStrategy,
        personas: List[Persona],
        max_turns: int = 20,
        verbose: bool = False,
        interviewer_agent_type: str = "simple",
        allowed_paths: Optional[List[str]] = None,
    ) -> List[SimulationResult]:
        """
        Run simulations with multiple personas.

        Args:
            strategy: Communication strategy
            personas: List of personas to simulate
            max_turns: Maximum conversation turns
            verbose: Whether to print progress
            interviewer_agent_type: Type of interviewer agent to use
            allowed_paths: Allowed paths for computer use agents

        Returns:
            List of simulation results
        """
        results = []

        for i, persona in enumerate(personas, 1):
            logger.info(f"Running simulation {i}/{len(personas)} with {persona.name}")

            try:
                result = self.run_simulation(
                    strategy=strategy,
                    persona=persona,
                    max_turns=max_turns,
                    verbose=verbose,
                    interviewer_agent_type=interviewer_agent_type,
                    allowed_paths=allowed_paths,
                )
                results.append(result)

            except Exception as e:
                logger.error(f"Error in simulation with {persona.name}: {e}")
                continue

        return results

    def save_results(
        self,
        results: List[SimulationResult],
        output_dir: str = "./results",
        run_name: Optional[str] = None,
    ):
        """
        Save simulation results to files.

        Args:
            results: List of simulation results
            output_dir: Directory to save results
            run_name: Optional name for this run
        """
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create run-specific directory
        if run_name is None:
            run_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        run_path = output_path / run_name
        run_path.mkdir(exist_ok=True)

        # Save each result
        for i, result in enumerate(results):
            result_file = run_path / f"result_{i+1}.json"

            with open(result_file, "w") as f:
                json.dump(result.to_dict(), f, indent=2, default=str)

        # Save summary
        summary = self._create_summary(results)
        summary_file = run_path / "summary.json"

        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"Results saved to {run_path}")

        return run_path

    def _create_summary(self, results: List[SimulationResult]) -> Dict:
        """
        Create a summary of simulation results.

        Args:
            results: List of simulation results

        Returns:
            Summary dictionary
        """
        if not results:
            return {}

        avg_interviewer_score = sum(r.interviewer_eval.overall_score for r in results) / len(
            results
        )
        avg_interviewee_score = sum(r.interviewee_eval.overall_score for r in results) / len(
            results
        )
        avg_understanding = sum(r.interviewee_eval.questionnaire_score for r in results) / len(
            results
        )

        # Collect all strengths and weaknesses
        all_strengths = []
        all_weaknesses = []

        for result in results:
            all_strengths.extend(result.interviewer_eval.strengths)
            all_weaknesses.extend(result.interviewer_eval.weaknesses)

        return {
            "num_simulations": len(results),
            "avg_interviewer_score": avg_interviewer_score,
            "avg_interviewee_score": avg_interviewee_score,
            "avg_understanding_score": avg_understanding,
            "common_strengths": list(set(all_strengths)),
            "common_weaknesses": list(set(all_weaknesses)),
            "personas_tested": [r.conversation.config.interviewee_persona.name for r in results],
        }
