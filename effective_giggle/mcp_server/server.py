"""Main MCP Server implementation for Effective Giggle Pipeline

This module implements the core MCP server that exposes tools for the
effective-giggle content creation pipeline. The server provides a centralized
way for all agents to access shared functionality.

Key Features:
- Tool registration and discovery
- Standardized error handling and logging
- Automatic schema generation for tools
- Health checking and monitoring
- Future-ready architecture for pipeline expansion

Usage:
    server = EffectiveGiggleMCPServer()
    await server.start()
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Sequence

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from ..core.settings import get_settings

# Configure logging for the MCP server
logger = logging.getLogger("effective_giggle.mcp_server")
logger.setLevel(logging.INFO)


# Create the MCP server instance
server = Server("effective-giggle-mcp")

# Tool registry - will be populated during server initialization
_tools: Dict[str, Any] = {}


def _register_tools() -> None:
    """
    Register all available tools with the MCP server.
    
    This function imports and registers tools from different modules:
    - Notion tools for topic and database management
    - Research tools for web scraping and citation gathering (future)
    - Content tools for script writing and TTS (future)
    - YouTube tools for upload and metadata management (future)
    """
    global _tools
    logger.info("Registering MCP tools...")
    
    # Import and register Notion tools
    from .tools.notion_tools import register_notion_tools
    notion_tools = register_notion_tools()
    _tools.update(notion_tools)
    
    logger.info(f"Registered {len(_tools)} tools: {list(_tools.keys())}")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    Handle requests to list available tools.
    
    Returns a list of all registered tools with their schemas,
    allowing clients to discover what functionality is available.
    """
    tools = []
    
    for tool_name, tool_impl in _tools.items():
        # Each tool implementation should provide metadata
        tool_info = types.Tool(
            name=tool_name,
            description=tool_impl.get("description", f"Tool: {tool_name}"),
            inputSchema=tool_impl.get("schema", {
                "type": "object",
                "properties": {},
                "required": []
            })
        )
        tools.append(tool_info)
    
    logger.info(f"Listed {len(tools)} available tools")
    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Handle tool execution requests.
    
    Args:
        name: Name of the tool to execute
        arguments: Arguments to pass to the tool
        
    Returns:
        List of TextContent with tool execution results
    """
    logger.info(f"Executing tool: {name} with args: {arguments}")
    
    # Check if tool exists
    if name not in _tools:
        logger.error(f"Tool not found: {name}")
        raise ValueError(f"Tool '{name}' not found. Available tools: {list(_tools.keys())}")
    
    try:
        # Get the tool implementation
        tool_impl = _tools[name]
        tool_function = tool_impl["function"]
        
        # Execute the tool with provided arguments
        result = await tool_function(**arguments)
        
        # Format the result as MCP TextContent
        if isinstance(result, dict):
            import json
            content = json.dumps(result, indent=2)
        elif isinstance(result, str):
            content = result
        else:
            content = str(result)
        
        logger.info(f"Tool {name} executed successfully")
        return [types.TextContent(type="text", text=content)]
        
    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        raise ValueError(f"Tool execution failed: {str(e)}")


def get_tool_info() -> Dict[str, Any]:
    """
    Get information about all registered tools.
    
    Returns:
        Dictionary containing tool metadata and statistics
    """
    return {
        "total_tools": len(_tools),
        "tools": {
            name: {
                "description": impl.get("description", "No description"),
                "schema": impl.get("schema", {})
            }
            for name, impl in _tools.items()
        }
    }


async def run_server() -> None:
    """
    Run the MCP server using stdio transport.
    
    This function initializes tools, sets up the server, and runs it
    using the stdio transport for communication with MCP clients.
    """
    # Register tools before starting the server
    _register_tools()
    
    logger.info("Starting Effective Giggle MCP Server...")
    
    # Run the server with stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="effective-giggle-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    # Allow running the server directly for testing
    asyncio.run(run_server())
