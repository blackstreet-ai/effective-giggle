"""Notion MCP tool: query and mutate Topic database rows.

This module exposes one public callable:

* ``select_topic_from_backlog`` – returns a single backlog row as a dict and
  moves its *Status* to *Candidate*.

Actual HTTP calls to Notion are stubbed with TODO comments; for now the
function returns mocked data, making it safe to import without secrets.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, List, Any

import requests

from ..core.settings import get_settings
from agents import function_tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public function – registered as a Function Tool via decorator.
# ---------------------------------------------------------------------------


@function_tool  # let the SDK derive schema & description
def select_topic_from_backlog() -> Dict[str, str]:
    """Select a single topic row and promote it to *Candidate*.

    Returns a dictionary of all requested properties.  If no backlog rows are
    found, an empty dict is returned.
    """

    settings = get_settings()

    headers = {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    # ---------------------------------------------------------------------
    # 1. Query database for backlog rows
    # ---------------------------------------------------------------------
    query_url = f"https://api.notion.com/v1/databases/{settings.notion_database_id}/query"
    payload = {
        "filter": {
            "property": "Status",
            "select": {"equals": "Backlog"},
        },
        "page_size": 1,  # only need a single row
    }

    try:
        resp = requests.post(query_url, headers=headers, data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        logger.error("Notion query failed: %s", exc)
        return {}

    results: List[Dict[str, Any]] = resp.json().get("results", [])
    if not results:
        logger.info("No backlog topics found.")
        return {}

    page = results[0]
    page_id: str = page["id"]

    # Extract properties ---------------------------------------------------
    props = _extract_properties(page["properties"])

    # ---------------------------------------------------------------------
    # 2. Update the page's Status to Candidate
    # ---------------------------------------------------------------------
    update_url = f"https://api.notion.com/v1/pages/{page_id}"
    update_payload = {
        "properties": {
            "Status": {
                "select": {"name": "Candidate"},
            }
        }
    }

    try:
        requests.patch(update_url, headers=headers, data=json.dumps(update_payload), timeout=30).raise_for_status()
    except Exception as exc:
        logger.warning("Failed to update Notion row %s to Candidate: %s", page_id, exc)

    return props


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_properties(raw: Dict[str, Any]) -> Dict[str, str]:
    """Convert Notion property dict to {name: plain_text} mapping."""

    def plain(val: Any) -> str:
        if val is None:
            return ""
        if isinstance(val, list):
            return ", ".join(plain(v) for v in val)
        if isinstance(val, dict):
            # Handle Notion-rich text and select types
            if "name" in val:  # select
                return val["name"]
            if val.get("type") == "rich_text":
                return "".join(rt.get("plain_text", "") for rt in val.get("rich_text", []))
            if val.get("type") == "title":
                return "".join(rt.get("plain_text", "") for rt in val.get("title", []))
        return str(val)

    desired_keys = [
        "Topic",
        "Angle",
        "Stance",
        "Audience",
        "Must Hit",
        "Red lines",
        "Geo Focus",
        "Time Window",
    ]

    return {k: plain(raw.get(k)) for k in desired_keys}
