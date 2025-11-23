"""
Persona Simulation Framework

A multi-agent simulation system for optimizing customer communication strategies
through conversational AI simulations.
"""

from .models import (
    Persona,
    CommunicationStrategy,
    ConversationConfig,
    Conversation,
    Questionnaire,
    SimulationResult,
)
from .agents import InterviewerAgent, IntervieweeAgent
from .conversation import ConversationEngine
from .knowledge import KnowledgeBase, build_knowledge_base
from .evaluation import (
    QuestionnaireGenerator,
    QuestionnaireAdministrator,
    ConversationJudge,
)
from .optimization import StrategyOptimizer, OptimizationLoop
from .orchestrator import PersonaSimulator, cli_main

__version__ = "0.1.0"

__all__ = [
    "Persona",
    "CommunicationStrategy",
    "ConversationConfig",
    "Conversation",
    "Questionnaire",
    "SimulationResult",
    "InterviewerAgent",
    "IntervieweeAgent",
    "ConversationEngine",
    "KnowledgeBase",
    "build_knowledge_base",
    "QuestionnaireGenerator",
    "QuestionnaireAdministrator",
    "ConversationJudge",
    "StrategyOptimizer",
    "OptimizationLoop",
    "PersonaSimulator",
    "cli_main",
]
