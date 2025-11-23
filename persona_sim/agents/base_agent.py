"""
Base agent implementation for the persona simulation.
"""

import os
from typing import Optional, List, Dict, Any
from anthropic import Anthropic
import logging

from ..models import Conversation, Persona, CommunicationStrategy

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Base class for agents in the persona simulation.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize the base agent.

        Args:
            model: Anthropic model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            anthropic_api_key: API key for Anthropic
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        self.client = Anthropic(api_key=api_key)

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generate a response using the Anthropic API.

        Args:
            system_prompt: System prompt for the agent
            user_message: User message to respond to
            conversation_history: Optional conversation history

        Returns:
            Generated response
        """
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current message
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages,
            )

            # Extract text content from response
            content = response.content[0].text if response.content else ""
            return content

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def __call__(self, **kwargs) -> str:
        """
        Make the agent callable. To be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement __call__")
