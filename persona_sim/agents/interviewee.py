"""
Interviewee agent implementation with persona adherence.
"""

import logging
from typing import Optional

from .base_agent import BaseAgent
from ..models import Conversation, Persona

logger = logging.getLogger(__name__)


class IntervieweeAgent(BaseAgent):
    """
    Agent that participates in the interview while maintaining a specific persona.
    """

    def __init__(
        self,
        persona: Persona,
        product_name: str = "the product",
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize the interviewee agent.

        Args:
            persona: Persona to maintain during conversation
            product_name: Name of the product being discussed
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

        self.persona = persona
        self.product_name = product_name

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for the interviewee.

        Returns:
            System prompt string
        """
        prompt = f"""{self.persona.to_prompt()}

You are in a conversation about {self.product_name}. The interviewer is trying to explain the product and convince you to use it.

IMPORTANT INSTRUCTIONS:
- Stay completely in character as {self.persona.name}
- Respond naturally based on your persona's background, technical level, and communication style
- Express genuine interest, skepticism, or questions based on your persona's goals and pain points
- If something doesn't align with your priorities or you have concerns, voice them
- Ask questions that your persona would naturally ask
- React authentically to what the interviewer says
- Don't be overly agreeable - maintain your persona's perspective and objections when appropriate
- Keep responses conversational and natural (2-4 sentences typically)

Remember: You are NOT an AI assistant. You are {self.persona.name}, and you should respond exactly as this person would in a real conversation."""

        return prompt

    def __call__(
        self,
        conversation_history: str,
        conversation: Conversation,
        **kwargs,
    ) -> str:
        """
        Generate the interviewee's response.

        Args:
            conversation_history: String representation of conversation history
            conversation: Full conversation object

        Returns:
            Generated response
        """
        # Build system prompt
        system_prompt = self._build_system_prompt()

        # Build user message
        user_message = f"""Here is the conversation so far:

{conversation_history}

Provide your next response as {self.persona.name}. Stay in character and respond naturally based on your persona's characteristics, goals, and perspective."""

        # Generate response
        try:
            response = self.generate_response(
                system_prompt=system_prompt,
                user_message=user_message,
            )

            return response.strip()

        except Exception as e:
            logger.error(f"Error generating interviewee response: {e}")
            return "I'm not sure I understand. Could you explain that differently?"
