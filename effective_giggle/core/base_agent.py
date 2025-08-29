"""BaseAgent wraps OpenAI Agents SDK to enforce project-wide conventions.

All concrete agents should subclass `BaseAgent` (or simply call
`create_agent()` helper) to obtain common behaviour:
  • automatic settings injection
  • structured logging
  • standard tool loading helpers

NOTE: The actual OpenAI Agents SDK API may evolve.  This wrapper attempts to
isolate version differences behind a thin façade so downstream agents remain
stable.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Sequence

import os

from agents import Agent as _Agent, Runner
from .settings import get_settings

logger = logging.getLogger("effective_giggle")
logger.setLevel(logging.INFO)


class BaseAgent:
    """Wrapper around `openai-agents` `Agent` with sync helper."""

    def __init__(
        self,
        name: str,
        instructions: str,
        tools: Sequence[object] | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()

        # The SDK will read the API key from env, but we ensure it's set.
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

        self._agent = _Agent(
            name=name,
            instructions=instructions,
            tools=list(tools or []),
            model=model or settings.default_model,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def arun(self, *messages: str) -> str:
        """Run the agent asynchronously and return final output."""

        if len(messages) == 1:
            input_msg = messages[0]
        else:
            input_msg = "\n".join(messages)

        result = await Runner.run(self._agent, input_msg)
        return result.final_output

    def run(self, *messages: str) -> str:
        """Synchronous helper around `arun`.  Blocks until completion."""

        return asyncio.run(self.arun(*messages))

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def agent(self) -> _Agent:  # noqa: D401 – simple accessor
        return self._agent
