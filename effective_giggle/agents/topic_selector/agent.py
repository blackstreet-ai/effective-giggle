"""Topic Selector agent factory.

Selects a Notion row where *Status == Backlog*, promotes it to *Candidate*, and
returns the row's key properties.
"""

from __future__ import annotations

from ...core.base_agent import BaseAgent
from ...tools import notion_db

# ---------------------------------------------------------------------------
# Prompt & tool registration
# ---------------------------------------------------------------------------

INSTRUCTIONS = (
    "You are a strategic content agent. When invoked you must choose exactly "
    "one topic from the backlog, promote its status to *Candidate* via the "
    "Notion tool, and then return all of the row's properties as JSON in your "
    "final message. Output only valid JSON."
)

# Using function tools directly
TOOLS = [notion_db.select_topic_from_backlog]


def create() -> BaseAgent:
    """Factory for discovery via `effective_giggle.agents.get_agent_factory`."""

    return BaseAgent(
        name="topic_selector",
        instructions=INSTRUCTIONS,
        tools=TOOLS,
    )
