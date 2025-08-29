"""Researcher agent factory.

Takes a selected topic and researches it, producing a bulleted digest with citations.
"""

from __future__ import annotations

from ...core.base_agent import BaseAgent

# ---------------------------------------------------------------------------
# Prompt & tool registration
# ---------------------------------------------------------------------------

INSTRUCTIONS = (
    "You are a research specialist. When you receive topic information, conduct "
    "thorough research and produce a structured output with:\n"
    "1. A bulleted digest of key findings\n"
    "2. A citation list with URLs and titles\n\n"
    "Format your response as JSON with 'digest' and 'citations' fields."
)

# TODO: Add web search tools when implementing
TOOLS = []


def create() -> BaseAgent:
    """Factory for discovery via `effective_giggle.agents.get_agent_factory`."""

    return BaseAgent(
        name="researcher",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
    )
