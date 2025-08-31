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
    
    # Use the existing query_topics_by_status function to get current backlog
    # This ensures we're working with the actual current state
    # Use limit=100 to access all topics (not just first 10)
    backlog_topics = await query_topics_by_status("Backlog", limit=100)
    
    if not backlog_topics:
        logger.info("No backlog topics found in Notion database")
        return {}
    
    # Select the first topic (they're already sorted by created_time in query_topics_by_status)
    selected_topic = backlog_topics[0]
    page_id = selected_topic.get("page_id")
    
    if not page_id:
        logger.error("Selected topic has no page_id")
        raise Exception("Selected topic missing page_id")
    
    logger.info(f"Selected backlog topic with ID: {page_id}")
    
    # Update the topic's status to "Candidate"
    settings = get_settings()
    headers = {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    
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
            timeout=4
        )
        update_resp.raise_for_status()
        logger.info(f"Successfully promoted topic {page_id} to Candidate status")
    except Exception as exc:
        logger.warning(f"Failed to update topic status for {page_id}: {exc}")
        # Don't raise here - we still want to return the topic data
    
    # Prepare return data with all the topic properties
    result = {
        "page_id": page_id,
        "notion_url": f"https://www.notion.so/{page_id.replace('-', '')}",
        "Topic": selected_topic.get("Topic", ""),
        "Angle": selected_topic.get("Angle", ""),
        "Stance": selected_topic.get("Stance", ""),
        "Audience": selected_topic.get("Audience", ""),
        "Geo Focus": selected_topic.get("Geo Focus", ""),
        "Time Window": selected_topic.get("Time Window", ""),
    }
    
    logger.info(f"Returning topic data with page_id: {page_id}")
    return result


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
            timeout=4
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
            timeout=4
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


async def create_research_page(topic_id: str, research_data: str) -> Dict[str, Any]:
    """
    Create a child page under a topic with research results.
    
    This tool creates a new child page under the specified topic page
    and populates it with the research findings. The research data should
    be a JSON string containing the research report.
    
    Args:
        topic_id: The Notion page ID of the parent topic
        research_data: JSON string containing the research report
        
    Returns:
        Dict containing the created page information
        
    Raises:
        Exception: If Notion API calls fail or data is invalid
    """
    logger.info(f"Creating research page for topic {topic_id}")
    
    settings = get_settings()
    
    # Parse research data
    try:
        research_json = json.loads(research_data)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in research_data: {e}")
        raise Exception(f"Invalid JSON format: {e}")
    
    # Prepare Notion API headers
    headers = {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    def _clean_text(text: str) -> str:
        """Clean text of markdown symbols and JSON artifacts for Notion display."""
        if not text:
            return ""
        
        # Remove common markdown symbols that don't translate well to Notion
        text = text.replace("####", "").replace("###", "").replace("##", "")
        text = text.replace("**", "").replace("*", "")
        text = text.replace("[Skip to content]", "")
        text = text.replace("[Sections]", "")
        text = text.replace("[Home]", "")
        
        # Clean up URLs in parentheses that appear as artifacts
        import re
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)  # Remove [text](url) patterns
        text = re.sub(r'\(https?://[^\s\)]+\)', '', text)  # Remove standalone (url) patterns
        
        # Clean up extra whitespace and newlines
        text = re.sub(r'\n\s*\n', '\n', text)  # Multiple newlines to single
        text = text.strip()
        
        return text
    
    def _extract_url_from_citation(citation_text: str) -> Optional[str]:
        """Extract URL from citation text for proper linking."""
        import re
        url_pattern = r'https?://[^\s\)\]]+(?:/[^\s\)\]]*)?'
        match = re.search(url_pattern, citation_text)
        return match.group(0) if match else None
    
    # Create page content from research data
    page_content = []
    
    # Add title with topic name
    topic_title = f"Research Digest — {research_json.get('topic_title', 'Research Report')}"
    page_content.append({
        "object": "block",
        "type": "heading_1",
        "heading_1": {
            "rich_text": [{"type": "text", "text": {"content": _clean_text(topic_title)}}]
        }
    })
    
    # Add executive summary as main content section
    if "executive_summary" in research_json and research_json["executive_summary"]:
        page_content.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Executive Summary"}}]
            }
        })
        
        summary_text = _clean_text(research_json["executive_summary"])
        if summary_text:
            page_content.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": summary_text}}]
                }
            })
    
    # Fallback to research_summary if executive_summary not provided
    elif "research_summary" in research_json and research_json["research_summary"]:
        page_content.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Research Summary"}}]
            }
        })
        
        summary_text = _clean_text(research_json["research_summary"])
        if summary_text:
            page_content.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": summary_text}}]
                }
            })
    
    # Add research methodology if available
    methodology_items = []
    if "research_methodology" in research_json:
        methodology_items = research_json["research_methodology"]
    elif "methodology" in research_json:
        methodology_items = research_json["methodology"]
    
    if methodology_items:
        for item in methodology_items:
            clean_item = _clean_text(str(item))
            if clean_item and len(clean_item) > 10:  # Only substantial content
                page_content.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": clean_item}}]
                    }
                })
    
    # Add key findings (new structured format)
    if "key_findings" in research_json and research_json["key_findings"]:
        page_content.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Key Findings"}}]
            }
        })
        
        for finding in research_json["key_findings"]:
            clean_finding = _clean_text(str(finding))
            if clean_finding and len(clean_finding) > 10:
                page_content.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": clean_finding}}]
                    }
                })
    
    # Fallback to key_insights if key_findings not provided
    elif "key_insights" in research_json and research_json["key_insights"]:
        page_content.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Key Insights"}}]
            }
        })
        
        for insight in research_json["key_insights"]:
            clean_insight = _clean_text(str(insight))
            if clean_insight and len(clean_insight) > 10:
                page_content.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": clean_insight}}]
                    }
                })
    
    # Add supporting evidence (new structured format)
    if "supporting_evidence" in research_json and research_json["supporting_evidence"]:
        page_content.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Supporting Evidence"}}]
            }
        })
        
        for evidence in research_json["supporting_evidence"]:
            clean_evidence = _clean_text(str(evidence))
            if clean_evidence and len(clean_evidence) > 10:
                page_content.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": clean_evidence}}]
                    }
                })
    
    # Add research digest (main findings) - fallback
    elif "digest" in research_json and research_json["digest"]:
        page_content.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Research Digest"}}]
            }
        })
        
        for item in research_json["digest"]:
            clean_item = _clean_text(str(item))
            if clean_item and len(clean_item) > 20:  # Only substantial findings
                page_content.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": clean_item}}]
                    }
                })
    
    # Add recent developments
    if "recent_developments" in research_json and research_json["recent_developments"]:
        page_content.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Recent Developments"}}]
            }
        })
        
        for development in research_json["recent_developments"]:
            clean_dev = _clean_text(str(development))
            if clean_dev and len(clean_dev) > 10:
                page_content.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": clean_dev}}]
                    }
                })
    
    # Add citations with proper formatting
    if "citations" in research_json and research_json["citations"]:
        page_content.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Citations"}}]
            }
        })
        
        for citation in research_json["citations"]:
            if isinstance(citation, dict):
                # Structured citation
                title = _clean_text(citation.get('title', 'Source'))
                url = citation.get('url', '')
                description = _clean_text(citation.get('description', ''))
                
                if title and url:
                    # Create rich text with link
                    rich_text = [
                        {"type": "text", "text": {"content": title, "link": {"url": url}}}
                    ]
                    if description:
                        rich_text.append({"type": "text", "text": {"content": f"\n{description}"}})
                    
                    page_content.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": rich_text}
                    })
            
            elif isinstance(citation, str):
                # String citation - try to extract URL and title
                clean_citation = _clean_text(citation)
                url = _extract_url_from_citation(clean_citation)
                
                if url and len(clean_citation) > len(url) + 10:
                    # Has both title and URL
                    title = clean_citation.replace(url, '').strip()
                    if title:
                        page_content.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {"type": "text", "text": {"content": title, "link": {"url": url}}}
                                ]
                            }
                        })
                    else:
                        page_content.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {"type": "text", "text": {"content": url, "link": {"url": url}}}
                                ]
                            }
                        })
                elif clean_citation:
                    # Just text, no URL
                    page_content.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": clean_citation}}]
                        }
                    })
    
    # Create the child page
    create_page_data = {
        "parent": {"page_id": topic_id},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": "Research Report"}}]
            }
        },
        "children": page_content
    }
    
    try:
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=create_page_data,
            timeout=4
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to create research page: {response.status_code} - {response.text}")
            raise Exception(f"Notion API error: {response.status_code} - {response.text}")
        
        page_data = response.json()
        logger.info(f"Successfully created research page: {page_data['id']}")
        
        return {
            "success": True,
            "page_id": page_data["id"],
            "url": page_data["url"],
            "message": "Research page created successfully"
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed when creating research page: {e}")
        raise Exception(f"Failed to create research page: {e}")


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
        },
        
        "create_research_page": {
            "function": create_research_page,
            "description": "Create a child page under a topic with research results",
            "schema": {
                "type": "object",
                "properties": {
                    "topic_id": {
                        "type": "string",
                        "description": "The Notion page ID of the parent topic"
                    },
                    "research_data": {
                        "type": "string",
                        "description": "JSON string containing the research report with digest, citations, insights, etc."
                    }
                },
                "required": ["topic_id", "research_data"]
            }
        }
    }
    
    logger.info(f"Registered {len(tools)} Notion tools")
    return tools
