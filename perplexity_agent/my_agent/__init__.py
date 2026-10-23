"""Gemini Agent Modul."""

from .agent import (
    create_agent,
    call_agent_async,
    call_agent_sync,
    AGENT_CONFIGS,
)

__version__ = "0.2.0"
__all__ = [
    "create_agent",
    "call_agent_async",
    "call_agent_sync",
    "AGENT_CONFIGS",
]
