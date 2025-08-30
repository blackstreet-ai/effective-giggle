"""MCP Client for Effective Giggle Pipeline

This module provides a client wrapper that agents can use to connect to
the local MCP server and access tools. The client handles connection
management, tool discovery, and execution with proper error handling.

The client is designed to be used by BaseAgent and individual agent
implementations to access centralized tools through the MCP protocol.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging for the MCP client
logger = logging.getLogger("effective_giggle.mcp_client")


class EffectiveGiggleMCPClient:
    """
    MCP Client for connecting to the Effective Giggle MCP Server.
    
    This client provides a simple interface for agents to discover and
    execute tools from the centralized MCP server. It handles connection
    management, error handling, and tool result formatting.
    
    Usage:
        async with EffectiveGiggleMCPClient() as client:
            # List available tools
            tools = await client.list_tools()
            
            # Execute a tool
            result = await client.call_tool("select_topic_from_backlog", {})
    """
    
    def __init__(self, server_command: Optional[List[str]] = None):
        """
        Initialize the MCP client.
        
        Args:
            server_command: Command to start the MCP server process.
                          If None, uses the default server command.
        """
        # Default command to run the MCP server
        self.server_command = server_command or [
            sys.executable, "-m", "effective_giggle.mcp_server.server"
        ]
        
        self.session: Optional[ClientSession] = None
        self._read_stream = None
        self._write_stream = None
        self._stdio_context = None
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        
        logger.info("MCP Client initialized")
    
    async def connect(self) -> None:
        """
        Connect to the MCP server.
        
        This method starts the server process and establishes a connection
        using stdio transport. The connection will be maintained until
        disconnect() is called.
        
        Raises:
            Exception: If connection fails or server cannot be started
        """
        if self.session is not None:
            logger.warning("Client is already connected")
            return
        
        try:
            logger.info("Connecting to MCP server...")
            
            # Create server parameters for stdio connection
            server_params = StdioServerParameters(
                command=self.server_command[0],
                args=self.server_command[1:] if len(self.server_command) > 1 else [],
                env=dict(os.environ)  # Inherit environment
            )
            
            # Connect using stdio client
            self._stdio_context = stdio_client(server_params)
            self._read_stream, self._write_stream = await self._stdio_context.__aenter__()
            
            # Create session
            self.session = ClientSession(self._read_stream, self._write_stream)
            await self.session.__aenter__()
            
            # Initialize the session
            await self.session.initialize()
            
            logger.info("Successfully connected to MCP server")
            
            # Cache available tools
            await self._refresh_tools_cache()
                    
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            await self.disconnect()
            raise Exception(f"MCP connection failed: {e}")
    
    async def disconnect(self) -> None:
        """
        Disconnect from the MCP server and clean up resources.
        
        This method closes the session and cleans up the stdio connection.
        """
        logger.info("Disconnecting from MCP server...")
        
        try:
            # Clean up session
            if self.session:
                await self.session.__aexit__(None, None, None)
                self.session = None
            
            # Clean up stdio context
            if self._stdio_context:
                await self._stdio_context.__aexit__(None, None, None)
                self._stdio_context = None
            
            self._read_stream = None
            self._write_stream = None
            self._tools_cache = None
            
        except Exception as e:
            logger.warning(f"Error during disconnect cleanup: {e}")
        
        logger.info("Disconnected from MCP server")
    
    async def list_tools(self, refresh_cache: bool = False) -> List[Dict[str, Any]]:
        """
        List all available tools from the MCP server.
        
        Args:
            refresh_cache: If True, refresh the tools cache from server
            
        Returns:
            List of tool dictionaries with name, description, and schema
            
        Raises:
            Exception: If not connected or server request fails
        """
        if not self.session:
            raise Exception("Not connected to MCP server. Call connect() first.")
        
        if self._tools_cache is None or refresh_cache:
            await self._refresh_tools_cache()
        
        return self._tools_cache or []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result
            
        Raises:
            Exception: If not connected, tool not found, or execution fails
        """
        if not self.session:
            raise Exception("Not connected to MCP server. Call connect() first.")
        
        logger.info(f"Calling tool: {tool_name} with args: {arguments}")
        
        try:
            # Execute the tool using the MCP session
            result = await self.session.call_tool(tool_name, arguments)
            
            # Extract content from the result
            if hasattr(result, 'content') and result.content:
                # Handle different content types
                content = result.content[0]
                if hasattr(content, 'text'):
                    # Try to parse as JSON first, fall back to string
                    try:
                        return json.loads(content.text)
                    except json.JSONDecodeError:
                        return content.text
                else:
                    return str(content)
            
            logger.info(f"Tool {tool_name} executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            raise Exception(f"Tool '{tool_name}' execution failed: {e}")
    
    async def _refresh_tools_cache(self) -> None:
        """
        Refresh the internal tools cache from the server.
        
        This method queries the server for available tools and caches
        the result for faster subsequent access.
        """
        if not self.session:
            return
        
        try:
            logger.debug("Refreshing tools cache...")
            
            # List tools from the server
            tools_result = await self.session.list_tools()
            
            # Convert tools to dictionary format
            self._tools_cache = []
            if hasattr(tools_result, 'tools'):
                for tool in tools_result.tools:
                    tool_dict = {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    }
                    self._tools_cache.append(tool_dict)
            
            logger.info(f"Cached {len(self._tools_cache)} tools from server")
            
        except Exception as e:
            logger.warning(f"Failed to refresh tools cache: {e}")
            self._tools_cache = []
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the JSON schema for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool schema dictionary or None if tool not found
        """
        tools = await self.list_tools()
        
        for tool in tools:
            if tool.get("name") == tool_name:
                return tool.get("inputSchema", {})
        
        return None
    
    async def _refresh_tools_cache(self) -> None:
        """
        Refresh the internal tools cache from the server.
        
        This method queries the server for available tools and caches
        the result for faster subsequent access.
        """
        if not self.session:
            return
        
        try:
            logger.debug("Refreshing tools cache...")
            
            # List tools from the server
            tools_result = await self.session.list_tools()
            
            # Convert tools to dictionary format
            self._tools_cache = []
            if hasattr(tools_result, 'tools'):
                for tool in tools_result.tools:
                    tool_dict = {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    }
                    self._tools_cache.append(tool_dict)
            
            logger.info(f"Cached {len(self._tools_cache)} tools from server")
            
        except Exception as e:
            logger.warning(f"Failed to refresh tools cache: {e}")
            self._tools_cache = []
    
    def is_connected(self) -> bool:
        """
        Check if the client is currently connected to the server.
        
        Returns:
            True if connected, False otherwise
        """
        return self.session is not None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


# Convenience function for creating and using the client
async def create_mcp_client() -> EffectiveGiggleMCPClient:
    """
    Create and connect an MCP client instance.
    
    Returns:
        Connected MCP client ready for use
    """
    client = EffectiveGiggleMCPClient()
    await client.connect()
    return client


# Example usage for testing
async def test_mcp_client():
    """
    Test function to demonstrate MCP client usage.
    
    This function can be used for development and testing to verify
    that the client can connect to the server and execute tools.
    """
    logger.info("Testing MCP client...")
    
    async with EffectiveGiggleMCPClient() as client:
        # List available tools
        tools = await client.list_tools()
        logger.info(f"Available tools: {[t['name'] for t in tools]}")
        
        # Test a simple tool call (if available)
        if any(tool['name'] == 'select_topic_from_backlog' for tool in tools):
            try:
                result = await client.call_tool('select_topic_from_backlog', {})
                logger.info(f"Tool result: {result}")
            except Exception as e:
                logger.error(f"Tool test failed: {e}")
    
    logger.info("MCP client test completed")


if __name__ == "__main__":
    # Run the test if executed directly
    asyncio.run(test_mcp_client())
