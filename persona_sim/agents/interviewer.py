"""
Interviewer agent implementation with knowledge base access.
"""

import logging
from typing import Optional

from .base_agent import BaseAgent
from ..models import Conversation, Persona, CommunicationStrategy
from ..knowledge import KnowledgeBase

logger = logging.getLogger(__name__)


class InterviewerAgent(BaseAgent):
    """
    Agent that conducts the interview and tries to convince the interviewee.
    Has access to a knowledge base for product information.
    """

    def __init__(
        self,
        strategy: CommunicationStrategy,
        knowledge_base: Optional[KnowledgeBase] = None,
        persona: Optional[Persona] = None,
        product_name: str = "the product",
        product_description: str = "",
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize the interviewer agent.

        Args:
            strategy: Communication strategy to follow
            knowledge_base: Knowledge base for retrieving product info
            persona: Optional persona for the interviewer
            product_name: Name of the product
            product_description: Description of the product
            model: Anthropic model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            anthropic_api_key: API key for Anthropic
        """
        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=anthropic_api_key,
        )

        self.strategy = strategy
        self.knowledge_base = knowledge_base
        self.persona = persona
        self.product_name = product_name
        self.product_description = product_description

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for the interviewer.

        Returns:
            System prompt string
        """
        prompt_parts = [
            f"You are an interviewer explaining and promoting {self.product_name}.",
            f"\nProduct Description: {self.product_description}",
            f"\n\n{self.strategy.to_prompt()}",
        ]

        if self.persona:
            prompt_parts.append(f"\n\nYour Persona:\n{self.persona.to_prompt()}")

        prompt_parts.append(
            "\n\nYour goal is to explain the product clearly, address questions and concerns, "
            "and convince the person you're speaking with to use or adopt the product. "
            "Follow the communication strategy closely. Be natural and conversational, but stay focused."
        )

        if self.knowledge_base:
            prompt_parts.append(
                "\n\nYou have access to a knowledge base about the product. When you need specific "
                "information, relevant context will be provided to you."
            )

        return "".join(prompt_parts)

    def _get_relevant_context(self, conversation_history: str) -> str:
        """
        Get relevant context from the knowledge base based on conversation.

        Args:
            conversation_history: Current conversation history

        Returns:
            Relevant context string
        """
        if not self.knowledge_base:
            return ""

        # Extract the last few messages to understand current topic
        last_messages = conversation_history.split("\n\n")[-3:]
        query = " ".join(last_messages)

        try:
            context = self.knowledge_base.get_context_for_query(query, k=3)
            if context and context != "No relevant information found.":
                return f"\n\nRelevant Information from Knowledge Base:\n{context}"
        except Exception as e:
            logger.warning(f"Error retrieving context from knowledge base: {e}")

        return ""

    def __call__(
        self,
        conversation_history: str,
        conversation: Conversation,
        **kwargs,
    ) -> str:
        """
        Generate the interviewer's response.

        Args:
            conversation_history: String representation of conversation history
            conversation: Full conversation object

        Returns:
            Generated response
        """
        # Build system prompt
        system_prompt = self._build_system_prompt()

        # Get relevant context from knowledge base
        context = self._get_relevant_context(conversation_history)

        # Build user message
        user_message = f"""Here is the conversation so far:

{conversation_history}

{context}

Please provide your next response as the interviewer. Remember to follow the communication strategy and work towards your goals."""

        # Generate response
        try:
            response = self.generate_response(
                system_prompt=system_prompt,
                user_message=user_message,
            )

            return response.strip()

        except Exception as e:
            logger.error(f"Error generating interviewer response: {e}")
            return "I apologize, but I'm having trouble formulating my response. Could we continue our discussion?"
