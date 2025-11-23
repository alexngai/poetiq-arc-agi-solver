"""
Agent type definitions for the factory pattern.
"""

from enum import Enum


class AgentType(str, Enum):
    """Types of interviewer agents available."""
    SIMPLE = "simple"  # Basic agent with knowledge base access
    COMPUTER_USE = "computer_use"  # Agent with computer use and tool capabilities
    CUSTOM = "custom"  # Custom agent implementation
