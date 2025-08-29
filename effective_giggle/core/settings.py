"""Global project settings.

Uses Pydantic's `BaseSettings` to pull configuration from environment variables or
`.env` files.  This centralises secrets / runtime configuration for all agents
and tools.
"""

from __future__ import annotations

import pathlib
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# ---------------------------------------------------------------------------
# Load .env (if present) from project root.  This is safe because `load_dotenv`
# only overrides env-vars that are *not* already set.
# ---------------------------------------------------------------------------

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)


class Settings(BaseSettings):
    """Central configuration model.

    Environment variables are looked up automatically.  Prefix variables with
    ``EG_`` (Effective Giggle) to avoid collisions, e.g. ``EG_OPENAI_API_KEY``.
    """
    
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        case_sensitive=False,
        extra="ignore"
    )

    # OpenAI
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")

    # Notion
    notion_api_key: str = Field(..., alias="NOTION_API_KEY")
    notion_database_id: str = Field(..., alias="EG_NOTION_DB_ID")

    # Model backend
    default_model: str = Field("gpt-4o-mini", alias="EG_DEFAULT_MODEL")


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
