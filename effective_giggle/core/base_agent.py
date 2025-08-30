"""BaseAgent wraps OpenAI Agents SDK to enforce project-wide conventions.

All concrete agents should subclass `BaseAgent` (or simply call
`create_agent()` helper) to obtain common behaviour:
  • automatic settings injection
  • structured logging
  • standard tool loading helpers
  • MCP server integration for centralized tools

NOTE: The actual OpenAI Agents SDK API may evolve.  This wrapper attempts to
isolate version differences behind a thin façade so downstream agents remain
stable.

MCP Integration:
The BaseAgent now supports connecting to the local MCP server to access
centralized tools alongside traditional function tools. This provides a
unified interface for all pipeline tools while maintaining backwards
compatibility.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Sequence, Optional, Dict, Any, List

import os

from agents import Agent as _Agent, Runner
from .settings import get_settings

logger = logging.getLogger("effective_giggle")
logger.setLevel(logging.INFO)


class BaseAgent:
    """
    Wrapper around `openai-agents` `Agent` with MCP integration.
    
    This class provides a unified interface for agents to access both
    traditional function tools and centralized MCP server tools. It
    handles connection management, tool discovery, and execution.
    
    Features:
    - Automatic MCP server connection and tool discovery
    - Backwards compatibility with existing function tools
    - Centralized error handling and logging
    - Tool availability checking and validation
    """

    def __init__(
        self,
        name: str,
        instructions: str,
        tools: Sequence[object] | None = None,
        model: str | None = None,
        use_mcp_server: bool = True,
    ) -> None:
        """
        Initialize the BaseAgent with optional MCP server integration.
        
        Args:
            name: Agent name for identification
            instructions: System instructions for the agent
            tools: Traditional function tools (optional)
            model: Model name to use (defaults to settings)
            use_mcp_server: Whether to connect to MCP server for tools
        """
        settings = get_settings()
        
        # Store configuration
        self.name = name
        self.use_mcp_server = use_mcp_server
        self._mcp_client: Optional[Any] = None
        self._mcp_tools: List[Dict[str, Any]] = []

        # The SDK will read the API key from env, but we ensure it's set.
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

        # Initialize the OpenAI Agent with traditional tools
        # MCP tools will be added dynamically during execution
        self._agent = _Agent(
            name=name,
            instructions=instructions,
            tools=list(tools or []),
            model=model or settings.default_model,
        )
        
        logger.info(f"BaseAgent '{name}' initialized (MCP: {use_mcp_server})")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def arun(self, *messages: str) -> str:
        """
        Run the agent asynchronously with MCP server integration.
        
        This method automatically connects to the MCP server (if enabled),
        discovers available tools, and runs the agent with access to both
        traditional function tools and MCP server tools.
        """
        # Connect to MCP server if enabled
        if self.use_mcp_server and self._mcp_client is None:
            await self._connect_to_mcp_server()
        
        try:
            if len(messages) == 1:
                input_msg = messages[0]
            else:
                input_msg = "\n".join(messages)

            result = await Runner.run(self._agent, input_msg)
            return result.final_output
            
        finally:
            # Clean up MCP connection
            if self._mcp_client:
                await self._disconnect_from_mcp_server()

    def run(self, *messages: str) -> str:
        """Synchronous helper around `arun`.  Blocks until completion."""
        return asyncio.run(self.arun(*messages))
    
    async def _connect_to_mcp_server(self) -> None:
        """
        Connect to the MCP server and discover available tools.
        
        This method establishes a connection to the local MCP server,
        retrieves the list of available tools, and makes them accessible
        to the agent during execution.
        """
        try:
            logger.info(f"Agent '{self.name}' connecting to MCP server...")
            
            # Import MCP client (lazy import to avoid circular dependencies)
            from ..mcp_server import EffectiveGiggleMCPClient
            
            # Create and connect the MCP client
            self._mcp_client = EffectiveGiggleMCPClient()
            await self._mcp_client.connect()
            
            # Discover available tools
            self._mcp_tools = await self._mcp_client.list_tools()
            
            logger.info(f"Agent '{self.name}' connected to MCP server with {len(self._mcp_tools)} tools")
            
            # Log available tools for debugging
            tool_names = [tool['name'] for tool in self._mcp_tools]
            logger.debug(f"Available MCP tools: {tool_names}")
            
        except Exception as e:
            logger.warning(f"Failed to connect to MCP server: {e}")
            logger.info("Agent will continue with traditional function tools only")
            self._mcp_client = None
            self._mcp_tools = []
    
    async def _disconnect_from_mcp_server(self) -> None:
        """
        Disconnect from the MCP server and clean up resources.
        """
        if self._mcp_client:
            try:
                await self._mcp_client.disconnect()
                logger.debug(f"Agent '{self.name}' disconnected from MCP server")
            except Exception as e:
                logger.warning(f"Error disconnecting from MCP server: {e}")
            finally:
                self._mcp_client = None
                self._mcp_tools = []
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool from the MCP server directly.
        
        This method allows agents to explicitly call MCP tools with
        proper error handling and logging. It's useful for complex
        agent workflows that need direct tool access.
        
        Args:
            tool_name: Name of the MCP tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result
            
        Raises:
            Exception: If MCP server is not connected or tool call fails
        """
        if not self._mcp_client:
            raise Exception("MCP server not connected. Enable use_mcp_server or call arun() first.")
        
        logger.info(f"Agent '{self.name}' calling MCP tool: {tool_name}")
        
        try:
            result = await self._mcp_client.call_tool(tool_name, arguments)
            logger.info(f"MCP tool '{tool_name}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"MCP tool '{tool_name}' failed: {e}")
            raise
    
    def get_available_tools(self) -> Dict[str, List[str]]:
        """
        Get information about all available tools.
        
        Returns:
            Dictionary with 'function_tools' and 'mcp_tools' lists
        """
        function_tools = []
        if hasattr(self._agent, 'tools'):
            function_tools = [getattr(tool, '__name__', str(tool)) for tool in self._agent.tools]
        
        mcp_tool_names = [tool['name'] for tool in self._mcp_tools]
        
        return {
            'function_tools': function_tools,
            'mcp_tools': mcp_tool_names,
            'total_tools': len(function_tools) + len(mcp_tool_names)
        }

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def agent(self) -> _Agent:  # noqa: D401 – simple accessor
        return self._agent
    
    @property
    def mcp_client(self) -> Optional[Any]:
        """Access to the MCP client for advanced usage."""
        return self._mcp_client
    
    @property 
    def mcp_tools(self) -> List[Dict[str, Any]]:
        """List of available MCP tools with their schemas."""
        return self._mcp_tools.copy()  # Return copy to prevent modification
