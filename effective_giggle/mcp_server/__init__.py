"""MCP Server for Effective Giggle Pipeline

This module provides a local Model Context Protocol (MCP) server that serves
tools and resources for the effective-giggle content creation pipeline.

The server exposes tools for:
- Notion database operations (topic management)
- Web research and citation gathering
- Future: Content generation, TTS, video rendering, YouTube upload

All agents in the pipeline can connect to this server to access shared tools
and maintain consistent interfaces across the system.
"""

from .server import server, run_server, get_tool_info, _register_tools, _tools
from .client import EffectiveGiggleMCPClient

__all__ = [
    "server", 
    "run_server", 
    "get_tool_info", 
    "_register_tools", 
    "_tools",
    "EffectiveGiggleMCPClient"
]
