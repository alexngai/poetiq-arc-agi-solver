"""
Conversation engine for managing turn-based dialogues between agents.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Callable

from ..models import (
    Conversation,
    ConversationConfig,
    Message,
    MessageType,
    AgentRole,
)

logger = logging.getLogger(__name__)


class ConversationEngine:
    """
    Manages turn-based conversations between interviewer and interviewee agents.
    """

    def __init__(
        self,
        config: ConversationConfig,
        interviewer_agent: Optional[Callable] = None,
        interviewee_agent: Optional[Callable] = None,
    ):
        """
        Initialize the conversation engine.

        Args:
            config: Configuration for the conversation
            interviewer_agent: Callable that generates interviewer responses
            interviewee_agent: Callable that generates interviewee responses
        """
        self.config = config
        self.interviewer_agent = interviewer_agent
        self.interviewee_agent = interviewee_agent

        self.conversation = Conversation(
            id=str(uuid.uuid4()),
            config=config,
        )

    def add_message(
        self,
        role: AgentRole,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[dict] = None,
    ) -> Message:
        """
        Add a message to the conversation.

        Args:
            role: Role of the agent sending the message
            content: Content of the message
            message_type: Type of message
            metadata: Optional metadata

        Returns:
            The created message
        """
        message = Message(
            role=role,
            content=content,
            message_type=message_type,
            metadata=metadata or {},
        )

        self.conversation.add_message(message)
        return message

    def get_conversation_history(self, text_only: bool = True) -> str:
        """
        Get the conversation history as a formatted string.

        Args:
            text_only: If True, only include TEXT messages

        Returns:
            Formatted conversation history
        """
        messages = self.conversation.messages

        if text_only:
            messages = [m for m in messages if m.message_type == MessageType.TEXT]

        history = []
        for msg in messages:
            role_name = "Interviewer" if msg.role == AgentRole.INTERVIEWER else "Interviewee"
            history.append(f"{role_name}: {msg.content}")

        return "\n\n".join(history)

    def get_messages_for_role(self, role: AgentRole) -> list[Message]:
        """
        Get all messages from a specific role.

        Args:
            role: Agent role to filter by

        Returns:
            List of messages from that role
        """
        return [m for m in self.conversation.messages if m.role == role]

    def run_conversation(
        self,
        initial_message: Optional[str] = None,
        verbose: bool = True,
    ) -> Conversation:
        """
        Run the conversation simulation.

        Args:
            initial_message: Optional initial message from interviewer
            verbose: Whether to print conversation progress

        Returns:
            Completed conversation
        """
        if self.interviewer_agent is None or self.interviewee_agent is None:
            raise ValueError("Both interviewer and interviewee agents must be set")

        logger.info(f"Starting conversation {self.conversation.id}")

        # Start with interviewer's opening
        if initial_message is None:
            initial_message = f"Hi! I'd like to talk to you about {self.config.product_name}. {self.config.product_description}"

        if verbose:
            print(f"\n{'='*80}")
            print(f"CONVERSATION START - Max Turns: {self.config.max_turns}")
            print(f"{'='*80}\n")

        # Add initial message
        self.add_message(
            role=AgentRole.INTERVIEWER,
            content=initial_message,
        )

        if verbose:
            print(f"Interviewer: {initial_message}\n")

        # Run conversation turns
        current_role = AgentRole.INTERVIEWEE
        turn_count = 0

        while turn_count < self.config.max_turns:
            try:
                if current_role == AgentRole.INTERVIEWEE:
                    # Get interviewee response
                    response = self.interviewee_agent(
                        conversation_history=self.get_conversation_history(),
                        conversation=self.conversation,
                    )

                    self.add_message(
                        role=AgentRole.INTERVIEWEE,
                        content=response,
                    )

                    if verbose:
                        print(f"Interviewee: {response}\n")

                    current_role = AgentRole.INTERVIEWER

                else:
                    # Get interviewer response
                    response = self.interviewer_agent(
                        conversation_history=self.get_conversation_history(),
                        conversation=self.conversation,
                    )

                    self.add_message(
                        role=AgentRole.INTERVIEWER,
                        content=response,
                    )

                    if verbose:
                        print(f"Interviewer: {response}\n")

                    current_role = AgentRole.INTERVIEWEE

                turn_count += 1

            except Exception as e:
                logger.error(f"Error during conversation turn {turn_count}: {e}")
                break

        self.conversation.end_time = datetime.now()

        if verbose:
            print(f"\n{'='*80}")
            print(f"CONVERSATION END - Completed {turn_count} turns")
            print(f"{'='*80}\n")

        logger.info(
            f"Conversation {self.conversation.id} completed with {turn_count} turns"
        )

        return self.conversation

    def run_single_turn(
        self,
        role: AgentRole,
        verbose: bool = False,
    ) -> str:
        """
        Run a single conversation turn.

        Args:
            role: Role of the agent to generate response
            verbose: Whether to print the response

        Returns:
            Generated response
        """
        if role == AgentRole.INTERVIEWER:
            if self.interviewer_agent is None:
                raise ValueError("Interviewer agent not set")

            response = self.interviewer_agent(
                conversation_history=self.get_conversation_history(),
                conversation=self.conversation,
            )

        else:
            if self.interviewee_agent is None:
                raise ValueError("Interviewee agent not set")

            response = self.interviewee_agent(
                conversation_history=self.get_conversation_history(),
                conversation=self.conversation,
            )

        self.add_message(role=role, content=response)

        if verbose:
            role_name = "Interviewer" if role == AgentRole.INTERVIEWER else "Interviewee"
            print(f"{role_name}: {response}\n")

        return response

    def reset_conversation(self):
        """Reset the conversation to start over."""
        self.conversation = Conversation(
            id=str(uuid.uuid4()),
            config=self.config,
        )
        logger.info(f"Reset conversation to new ID: {self.conversation.id}")

    def get_turn_count(self) -> int:
        """Get the current turn count."""
        return self.conversation.get_turn_count()

    def export_conversation(self) -> dict:
        """
        Export the conversation to a dictionary.

        Returns:
            Dictionary representation of the conversation
        """
        return self.conversation.to_dict()
