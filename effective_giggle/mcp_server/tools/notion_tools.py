"""Notion Tools for Effective Giggle MCP Server

This module contains all Notion-related tools that are exposed through the MCP server.
These tools handle topic management, database operations, and content workflow states.

Migrated from the original notion_db.py function_tool implementation to provide
centralized access through the MCP server architecture.

Tools provided:
- select_topic_from_backlog: Select and promote a topic from backlog to candidate status
- update_topic_status: Update the status of a specific topic
- query_topics_by_status: Query topics filtered by their current status
- get_topic_details: Get detailed information about a specific topic

All tools use the Notion API with proper error handling and logging.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import requests

from ...core.settings import get_settings

# Configure logging for Notion tools
logger = logging.getLogger("effective_giggle.mcp_server.notion_tools")


async def select_topic_from_backlog() -> Dict[str, Any]:
    """
    Select a single topic from the backlog and promote it to Candidate status.
    
    This tool queries the Notion database for topics with "Backlog" status,
    selects the first available topic, and updates its status to "Candidate".
    This is typically used by the topic_selector agent to choose the next
    topic for research and content creation.
    
    Returns:
        Dict containing topic properties (Topic, Angle, Stance, etc.)
        Returns empty dict if no backlog topics are found
        
    Raises:
        Exception: If Notion API calls fail or configuration is invalid
    """
    logger.info("Selecting topic from backlog...")
    
    settings = get_settings()
    
    # Prepare Notion API headers
    headers = {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    
    # Step 1: Query database for backlog topics
    query_url = f"https://api.notion.com/v1/databases/{settings.notion_database_id}/query"
    payload = {
        "filter": {
            "property": "Status",
            "select": {"equals": "Backlog"},
        },
        "page_size": 1,  # Only need a single topic
    }
    
    try:
        logger.debug(f"Querying Notion database: {query_url}")
        resp = requests.post(
            query_url, 
            headers=headers, 
            data=json.dumps(payload), 
            timeout=30
        )
        resp.raise_for_status()
    except Exception as exc:
        logger.error(f"Failed to query Notion database: {exc}")
        raise Exception(f"Notion query failed: {exc}")
    
    # Parse response and check for results
    results: List[Dict[str, Any]] = resp.json().get("results", [])
    if not results:
        logger.info("No backlog topics found in Notion database")
        return {}
    
    # Extract the first topic
    page = results[0]
    page_id: str = page["id"]
    logger.info(f"Found backlog topic with ID: {page_id}")
    
    # Extract topic properties using helper function
    props = _extract_topic_properties(page["properties"])
    
    # Step 2: Update the topic's status to "Candidate"
    update_url = f"https://api.notion.com/v1/pages/{page_id}"
    update_payload = {
        "properties": {
            "Status": {
                "select": {"name": "Candidate"},
            }
        }
    }
    
    try:
        logger.debug(f"Updating topic status to Candidate: {update_url}")
        update_resp = requests.patch(
            update_url, 
            headers=headers, 
            data=json.dumps(update_payload), 
            timeout=30
        )
        update_resp.raise_for_status()
        logger.info(f"Successfully promoted topic {page_id} to Candidate status")
    except Exception as exc:
        logger.warning(f"Failed to update topic status for {page_id}: {exc}")
        # Don't raise here - we still want to return the topic data
    
    return props


async def update_topic_status(topic_id: str, new_status: str) -> Dict[str, Any]:
    """
    Update the status of a specific topic in the Notion database.
    
    Args:
        topic_id: The Notion page ID of the topic to update
        new_status: The new status value (e.g., "Research", "Complete", etc.)
        
    Returns:
        Dict containing success status and updated topic information
        
    Raises:
        Exception: If the update operation fails
    """
    logger.info(f"Updating topic {topic_id} status to {new_status}")
    
    settings = get_settings()
    
    headers = {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    
    update_url = f"https://api.notion.com/v1/pages/{topic_id}"
    payload = {
        "properties": {
            "Status": {
                "select": {"name": new_status},
            }
        }
    }
    
    try:
        resp = requests.patch(
            update_url, 
            headers=headers, 
            data=json.dumps(payload), 
            timeout=30
        )
        resp.raise_for_status()
        
        logger.info(f"Successfully updated topic {topic_id} to status {new_status}")
        return {
            "success": True,
            "topic_id": topic_id,
            "new_status": new_status,
            "message": f"Topic status updated to {new_status}"
        }
        
    except Exception as exc:
        logger.error(f"Failed to update topic status: {exc}")
        raise Exception(f"Status update failed: {exc}")


async def query_topics_by_status(status: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Query topics from the Notion database filtered by status.
    
    Args:
        status: The status to filter by (e.g., "Backlog", "Candidate", "Research")
        limit: Maximum number of topics to return (default: 10)
        
    Returns:
        List of topic dictionaries with their properties
        
    Raises:
        Exception: If the query operation fails
    """
    logger.info(f"Querying topics with status: {status} (limit: {limit})")
    
    settings = get_settings()
    
    headers = {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    
    query_url = f"https://api.notion.com/v1/databases/{settings.notion_database_id}/query"
    payload = {
        "filter": {
            "property": "Status",
            "select": {"equals": status},
        },
        "page_size": min(limit, 100),  # Notion API limit is 100
    }
    
    try:
        resp = requests.post(
            query_url, 
            headers=headers, 
            data=json.dumps(payload), 
            timeout=30
        )
        resp.raise_for_status()
        
        results = resp.json().get("results", [])
        topics = []
        
        for page in results:
            topic_props = _extract_topic_properties(page["properties"])
            topic_props["page_id"] = page["id"]  # Include page ID for reference
            topics.append(topic_props)
        
        logger.info(f"Found {len(topics)} topics with status {status}")
        return topics
        
    except Exception as exc:
        logger.error(f"Failed to query topics by status: {exc}")
        raise Exception(f"Topic query failed: {exc}")


def _extract_topic_properties(raw_properties: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract and normalize topic properties from Notion API response.
    
    This helper function converts Notion's complex property format into
    a simple dictionary with string values for easier consumption by agents.
    
    Args:
        raw_properties: Raw properties dict from Notion API
        
    Returns:
        Normalized dictionary with topic properties
    """
    
    def _normalize_property_value(prop_value: Any) -> str:
        """
        Convert a Notion property value to a plain string.
        
        Handles different Notion property types:
        - Rich text: Extracts plain text content
        - Select: Gets the selected option name
        - Title: Extracts title text
        - Multi-select: Joins multiple selections
        """
        if prop_value is None:
            return ""
        
        if isinstance(prop_value, list):
            return ", ".join(_normalize_property_value(v) for v in prop_value)
        
        if isinstance(prop_value, dict):
            # Handle Notion select properties
            if "name" in prop_value:
                return prop_value["name"]
            
            # Handle rich text properties
            if prop_value.get("type") == "rich_text":
                rich_text_list = prop_value.get("rich_text", [])
                return "".join(rt.get("plain_text", "") for rt in rich_text_list)
            
            # Handle title properties
            if prop_value.get("type") == "title":
                title_list = prop_value.get("title", [])
                return "".join(rt.get("plain_text", "") for rt in title_list)
        
        return str(prop_value)
    
    # Define the topic properties we want to extract
    # These correspond to the columns in the Notion database
    desired_properties = [
        "Topic",        # Main topic/title
        "Angle",        # Content angle or perspective
        "Stance",       # Editorial stance to take
        "Audience",     # Target audience
        "Must Hit",     # Key points that must be covered
        "Red lines",    # Things to avoid or not mention
        "Geo Focus",    # Geographic focus area
        "Time Window",  # Relevant time period or deadline
    ]
    
    # Extract and normalize each property
    normalized_props = {}
    for prop_name in desired_properties:
        raw_value = raw_properties.get(prop_name)
        normalized_props[prop_name] = _normalize_property_value(raw_value)
    
    return normalized_props


def register_notion_tools() -> Dict[str, Dict[str, Any]]:
    """
    Register all Notion tools with the MCP server.
    
    This function returns a dictionary of tool implementations that can be
    registered with the MCP server. Each tool includes its function,
    description, and JSON schema for validation.
    
    Returns:
        Dictionary mapping tool names to their implementations
    """
    logger.info("Registering Notion tools...")
    
    tools = {
        "select_topic_from_backlog": {
            "function": select_topic_from_backlog,
            "description": "Select a topic from the backlog and promote it to candidate status",
            "schema": {
                "type": "object",
                "properties": {},
                "required": [],
                "description": "No parameters required. Selects the first available backlog topic."
            }
        },
        
        "update_topic_status": {
            "function": update_topic_status,
            "description": "Update the status of a specific topic in the database",
            "schema": {
                "type": "object",
                "properties": {
                    "topic_id": {
                        "type": "string",
                        "description": "The Notion page ID of the topic to update"
                    },
                    "new_status": {
                        "type": "string",
                        "description": "The new status value (e.g., Research, Complete, etc.)",
                        "enum": ["Backlog", "Candidate", "Research", "Writing", "Complete", "Archived"]
                    }
                },
                "required": ["topic_id", "new_status"]
            }
        },
        
        "query_topics_by_status": {
            "function": query_topics_by_status,
            "description": "Query topics from the database filtered by their current status",
            "schema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "The status to filter by",
                        "enum": ["Backlog", "Candidate", "Research", "Writing", "Complete", "Archived"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of topics to return (default: 10)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10
                    }
                },
                "required": ["status"]
            }
        }
    }
    
    logger.info(f"Registered {len(tools)} Notion tools")
    return tools
