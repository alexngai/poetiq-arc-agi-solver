"""
Computer Use agent with tool capabilities for enhanced information gathering.
"""

import logging
from typing import Optional, List, Dict, Any
from anthropic import Anthropic

from .base_agent import BaseAgent
from .tools import ToolExecutor, get_tools
from ..models import Conversation, Persona, CommunicationStrategy
from ..knowledge import KnowledgeBase

logger = logging.getLogger(__name__)


class ComputerUseInterviewerAgent(BaseAgent):
    """
    Interviewer agent with computer use capabilities.
    Can use tools to browse documentation, search code, and gather information.
    """

    def __init__(
        self,
        strategy: CommunicationStrategy,
        knowledge_base: Optional[KnowledgeBase] = None,
        persona: Optional[Persona] = None,
        product_name: str = "the product",
        product_description: str = "",
        allowed_paths: Optional[List[str]] = None,
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize the computer use interviewer agent.

        Args:
            strategy: Communication strategy to follow
            knowledge_base: Optional knowledge base for RAG
            persona: Optional persona for the interviewer
            product_name: Name of the product
            product_description: Description of the product
            allowed_paths: List of allowed paths for file operations
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

        # Initialize tool executor
        self.tool_executor = ToolExecutor(allowed_paths=allowed_paths)
        self.tools = get_tools()

        # Convert tools to Anthropic format
        self.anthropic_tools = [tool.to_anthropic_tool() for tool in self.tools]

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for the interviewer with tool usage instructions.

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

        # Add tool usage instructions
        prompt_parts.append(
            "\n\n## Tool Usage\n\n"
            "You have access to tools that let you browse documentation, search code, and gather information. "
            "Use these tools when you need specific technical details, examples, or documentation to support your explanations.\n\n"
            "**When to use tools:**\n"
            "- When asked about specific features or technical details\n"
            "- To find concrete examples or code snippets\n"
            "- To look up documentation or API references\n"
            "- To verify information before sharing it\n\n"
            "**Important:**\n"
            "- Use tools proactively to provide accurate, detailed information\n"
            "- Don't make up information - look it up using the tools\n"
            "- After using a tool, explain the information naturally in your response\n"
            "- Don't overwhelm with tool use - use them when genuinely helpful"
        )

        if self.knowledge_base:
            prompt_parts.append(
                "\n\nYou also have access to a knowledge base via RAG. "
                "Use your tools for browsing and exploration, and the knowledge base will provide "
                "relevant context automatically."
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
        Generate the interviewer's response using computer use capabilities.

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

Please provide your next response as the interviewer. Remember to follow the communication strategy and work towards your goals.

You can use the available tools to look up information, browse documentation, or find specific examples to support your explanation."""

        # Generate response with tool use
        try:
            response_text = self._generate_with_tools(
                system_prompt=system_prompt,
                user_message=user_message,
            )

            return response_text.strip()

        except Exception as e:
            logger.error(f"Error generating interviewer response: {e}")
            return "I apologize, but I'm having trouble formulating my response. Could we continue our discussion?"

    def _generate_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        max_iterations: int = 5,
    ) -> str:
        """
        Generate response with tool use capabilities.

        Args:
            system_prompt: System prompt
            user_message: User message
            max_iterations: Maximum tool use iterations

        Returns:
            Final response text
        """
        messages = [{"role": "user", "content": user_message}]

        for iteration in range(max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages,
                tools=self.anthropic_tools if iteration == 0 else self.anthropic_tools,
            )

            # Check if we're done or need to use tools
            if response.stop_reason == "end_turn":
                # Extract text response
                text_content = []
                for block in response.content:
                    if block.type == "text":
                        text_content.append(block.text)
                return "\n".join(text_content)

            elif response.stop_reason == "tool_use":
                # Add assistant's response to messages
                messages.append({"role": "assistant", "content": response.content})

                # Execute tools and collect results
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        logger.info(f"Executing tool: {block.name}")

                        # Execute the tool
                        result = self.tool_executor.execute_tool(
                            tool_name=block.name,
                            tool_input=block.input,
                        )

                        logger.info(f"Tool {block.name} result: {result[:200]}...")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                # Add tool results to messages
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})

                # Continue the loop to get the next response
                continue

            else:
                # Unexpected stop reason, return what we have
                logger.warning(f"Unexpected stop reason: {response.stop_reason}")
                text_content = []
                for block in response.content:
                    if block.type == "text":
                        text_content.append(block.text)
                return "\n".join(text_content) if text_content else "I apologize, I encountered an issue."

        # Max iterations reached
        logger.warning("Max tool use iterations reached")
        return "I apologize, but I'm having difficulty gathering all the information. Let me share what I know so far."
