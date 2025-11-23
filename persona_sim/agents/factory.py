"""
Agent factory for creating different types of agents.
"""

import logging
from typing import Optional, List, Dict, Any, Type

from .base_agent import BaseAgent
from .interviewer import InterviewerAgent
from .computer_use_agent import ComputerUseInterviewerAgent
from .agent_types import AgentType
from ..models import Persona, CommunicationStrategy
from ..knowledge import KnowledgeBase

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating interviewer agents of different types.
    """

    # Registry of agent types
    _agent_registry: Dict[str, Type[BaseAgent]] = {
        AgentType.SIMPLE: InterviewerAgent,
        AgentType.COMPUTER_USE: ComputerUseInterviewerAgent,
    }

    @classmethod
    def register_agent_type(cls, agent_type: str, agent_class: Type[BaseAgent]):
        """
        Register a custom agent type.

        Args:
            agent_type: Name of the agent type
            agent_class: Agent class to register

        Example:
            >>> class MyCustomAgent(BaseAgent):
            ...     pass
            >>> AgentFactory.register_agent_type("my_custom", MyCustomAgent)
        """
        cls._agent_registry[agent_type] = agent_class
        logger.info(f"Registered custom agent type: {agent_type}")

    @classmethod
    def create_interviewer(
        cls,
        agent_type: str = AgentType.SIMPLE,
        strategy: Optional[CommunicationStrategy] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
        persona: Optional[Persona] = None,
        product_name: str = "the product",
        product_description: str = "",
        allowed_paths: Optional[List[str]] = None,
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        anthropic_api_key: Optional[str] = None,
        **kwargs,
    ) -> BaseAgent:
        """
        Create an interviewer agent of the specified type.

        Args:
            agent_type: Type of agent to create (simple, computer_use, or custom)
            strategy: Communication strategy for the agent
            knowledge_base: Optional knowledge base for RAG
            persona: Optional persona for the interviewer
            product_name: Name of the product
            product_description: Description of the product
            allowed_paths: List of allowed paths for computer use agents
            model: Anthropic model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            anthropic_api_key: API key for Anthropic
            **kwargs: Additional arguments passed to agent constructor

        Returns:
            Initialized agent instance

        Raises:
            ValueError: If agent_type is not registered
        """
        if agent_type not in cls._agent_registry:
            raise ValueError(
                f"Unknown agent type: {agent_type}. "
                f"Available types: {list(cls._agent_registry.keys())}"
            )

        agent_class = cls._agent_registry[agent_type]

        # Build common arguments
        common_args = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "anthropic_api_key": anthropic_api_key,
        }

        # Add interviewer-specific arguments
        if agent_type in [AgentType.SIMPLE, AgentType.COMPUTER_USE]:
            common_args.update({
                "strategy": strategy,
                "knowledge_base": knowledge_base,
                "persona": persona,
                "product_name": product_name,
                "product_description": product_description,
            })

        # Add computer use specific arguments
        if agent_type == AgentType.COMPUTER_USE:
            common_args["allowed_paths"] = allowed_paths

        # Merge with any additional kwargs
        common_args.update(kwargs)

        # Create and return agent
        try:
            agent = agent_class(**common_args)
            logger.info(f"Created {agent_type} interviewer agent")
            return agent

        except Exception as e:
            logger.error(f"Error creating agent of type {agent_type}: {e}")
            raise

    @classmethod
    def get_available_types(cls) -> List[str]:
        """
        Get list of available agent types.

        Returns:
            List of registered agent type names
        """
        return list(cls._agent_registry.keys())

    @classmethod
    def get_agent_info(cls, agent_type: str) -> Dict[str, Any]:
        """
        Get information about an agent type.

        Args:
            agent_type: Type of agent

        Returns:
            Dictionary with agent information
        """
        if agent_type not in cls._agent_registry:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent_class = cls._agent_registry[agent_type]

        return {
            "type": agent_type,
            "class": agent_class.__name__,
            "module": agent_class.__module__,
            "description": agent_class.__doc__ or "No description available",
        }


# Convenience function
def create_interviewer_agent(
    agent_type: str = AgentType.SIMPLE,
    **kwargs,
) -> BaseAgent:
    """
    Convenience function to create an interviewer agent.

    Args:
        agent_type: Type of agent to create
        **kwargs: Arguments passed to AgentFactory.create_interviewer

    Returns:
        Initialized agent instance
    """
    return AgentFactory.create_interviewer(agent_type=agent_type, **kwargs)
