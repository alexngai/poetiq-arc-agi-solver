"""Main orchestrator for persona simulation."""

from .simulator import PersonaSimulator
from .cli import main as cli_main

__all__ = ["PersonaSimulator", "cli_main"]
