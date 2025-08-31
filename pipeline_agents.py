"""Simplified agents using OpenAI Agents SDK with native MCP integration.

This module contains clean agent implementations that leverage the SDK's built-in
MCP server support, eliminating the need for custom wrappers and manual orchestration.
"""

from agents import Agent
from agents.mcp import MCPServerStdio, create_static_tool_filter, ToolFilterContext
from pydantic import BaseModel
from typing import Optional


class TopicData(BaseModel):
    """Data structure for passing topic information between agents."""
    topic: str
    angle: str
    stance: str
    page_id: str
    audience: Optional[str] = None
    geo_focus: Optional[str] = None
    time_window: Optional[str] = None
    notion_url: Optional[str] = None


def create_context_aware_tool_filter(agent_type: str):
    """Create a dynamic tool filter based on agent context (SDK best practice).
    
    This provides more flexible tool access control than static filtering,
    allowing for context-aware decisions based on agent information.
    """
    def tool_filter(context: ToolFilterContext, tool) -> bool:
        """Context-aware tool filtering based on agent type and tool characteristics."""
        agent_name = context.agent.name
        
        # Define tool access rules based on agent type
        if agent_type == "topic_selector":
            # Topic selector should only access topic management tools
            allowed_tools = {
                "select_topic_from_backlog",
                "update_topic_status", 
                "query_topics_by_status"
            }
            return tool.name in allowed_tools
            
        elif agent_type == "researcher":
            # Researcher should only access research and content creation tools
            allowed_tools = {
                "web_search",
                "search_news", 
                "extract_content",
                "create_research_page",
                "update_topic_status"
            }
            return tool.name in allowed_tools
            
        # Default: deny access to unknown agent types
        return False
    
    return tool_filter


def create_mcp_server():
    """Create MCP server connection to our local effective-giggle MCP server."""
    return MCPServerStdio(
        params={
            "command": "python",
            "args": ["-m", "effective_giggle.mcp_server.server"],
        }
    )


def create_topic_selector() -> Agent:
    """Create topic selector agent with MCP tools for Notion operations."""
    
    # Create MCP server with context-aware tool filtering (SDK best practice)
    # Using dynamic filtering for more flexible access control
    mcp_server = MCPServerStdio(
        params={
            "command": "python3", 
            "args": ["-m", "effective_giggle.mcp_server.server"],
        },
        tool_filter=create_context_aware_tool_filter("topic_selector"),
        cache_tools_list=True  # Cache tool list for performance optimization
    )
    
    return Agent(
        name="TopicSelector",
        instructions="""You are a strategic content topic selector with access to Notion database tools.

Your job is to:
1. Use 'select_topic_from_backlog' to choose exactly one topic from the backlog
2. Extract all the topic details from the response
3. Hand off to the researcher with complete structured data

CRITICAL: When handing off to researcher, provide ALL fields:
- topic: The main topic title
- angle: The content angle/perspective  
- stance: The editorial stance to take
- page_id: The Notion page ID (CRUCIAL - must be exact UUID)
- audience: Target audience information
- geo_focus: Geographic focus area
- time_window: Relevant time period
- notion_url: Link to the Notion page

Always select a topic first, then immediately hand off to researcher with complete data.""",
        mcp_servers=[mcp_server]
    )


def create_researcher() -> Agent:
    """Create researcher agent with MCP tools for research and content creation."""
    
    # Create MCP server with context-aware tool filtering (SDK best practice)
    # Using dynamic filtering for more flexible access control
    mcp_server = MCPServerStdio(
        params={
            "command": "python3",
            "args": ["-m", "effective_giggle.mcp_server.server"],
        },
        tool_filter=create_context_aware_tool_filter("researcher"),
        cache_tools_list=True  # Cache tool list for performance optimization
    )
    
    return Agent(
        name="Researcher", 
        instructions="""You are a research specialist with access to web search and Notion tools.

When you receive a research assignment with topic data, execute this workflow:

1. **Start Research**: Update topic status to 'Research' using the provided page_id
2. **Web Search**: Search for comprehensive information on the topic and angle
3. **News Search**: Find recent developments and current events  
4. **Content Analysis**: Extract detailed content from the most relevant URLs
5. **Create Report**: Compile findings into a comprehensive research report
6. **Save Results**: Create a research page in Notion with your findings
7. **Complete**: Update topic status to 'Complete'

**Research Report Requirements:**
- Focus on the specific topic, angle, and stance provided
- Include actual findings, statistics, quotes, and concrete information
- Provide proper citations for all sources
- Extract real insights from search results (not generic statements)
- Create clean, well-formatted content for the Notion page

**Research Synthesis Requirements:**
When calling create_research_page, provide a comprehensive research_data JSON with:
- "executive_summary": A 5-6 sentence paragraph synthesizing all your research findings
- "key_findings": 4-6 bullet points of the most important discoveries
- "recent_developments": Current news and trends related to the topic
- "supporting_evidence": Statistics, quotes, and data points that support the angle
- "citations": All sources with titles, URLs, and brief descriptions

**Critical:** Always use the exact page_id provided in the research assignment.
Execute all steps in sequence and provide detailed, substantive research content with proper synthesis.""",
        mcp_servers=[mcp_server]
    )
