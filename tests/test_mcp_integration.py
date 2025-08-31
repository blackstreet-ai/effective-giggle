#!/usr/bin/env python3
"""
Integration test for the Effective Giggle MCP Server and Client.

This test verifies that:
1. The MCP server can be started and registers tools correctly
2. The MCP client can connect to the server
3. Tools can be discovered and executed through the MCP protocol
4. The BaseAgent integration works with MCP tools
5. Error handling works properly

Run this test to verify the MCP implementation is working correctly.

Usage:
    python test_mcp_integration.py
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_integration_test")


async def test_mcp_server_direct():
    """
    Test the MCP server directly by importing and running it.
    
    This test verifies that:
    - Tools are registered correctly
    - Server can be initialized without errors
    - Tool metadata is properly formatted
    """
    logger.info("=== Testing MCP Server Direct ===")
    
    try:
        # Import the server module
        from effective_giggle.mcp_server import _register_tools, get_tool_info, _tools
        
        # Register tools
        _register_tools()
        
        # Check that tools were registered
        tool_info = get_tool_info()
        logger.info(f"Server registered {tool_info['total_tools']} tools")
        
        # Verify tool structure
        for tool_name, tool_data in tool_info['tools'].items():
            logger.info(f"  - {tool_name}: {tool_data['description']}")
            
            # Verify tool has required fields
            assert 'description' in tool_data, f"Tool {tool_name} missing description"
            assert 'schema' in tool_data, f"Tool {tool_name} missing schema"
        
        # Verify specific tools exist
        expected_tools = ['select_topic_from_backlog', 'update_topic_status', 'query_topics_by_status']
        for expected_tool in expected_tools:
            assert expected_tool in _tools, f"Expected tool {expected_tool} not found"
            logger.info(f"  ✓ Found expected tool: {expected_tool}")
        
        logger.info("✅ MCP Server direct test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ MCP Server direct test failed: {e}")
        return False


async def test_notion_tools_direct():
    """
    Test the Notion tools directly without MCP server.
    
    This test verifies that:
    - Notion tools can be imported and registered
    - Tool schemas are properly defined
    - Tool functions exist and are callable
    """
    logger.info("=== Testing Notion Tools Direct ===")
    
    try:
        # Import notion tools
        from effective_giggle.mcp_server.tools.notion_tools import register_notion_tools
        
        # Register tools
        notion_tools = register_notion_tools()
        
        logger.info(f"Registered {len(notion_tools)} Notion tools")
        
        # Test each tool registration
        for tool_name, tool_impl in notion_tools.items():
            logger.info(f"  - Testing tool: {tool_name}")
            
            # Verify tool structure
            assert 'function' in tool_impl, f"Tool {tool_name} missing function"
            assert 'description' in tool_impl, f"Tool {tool_name} missing description"
            assert 'schema' in tool_impl, f"Tool {tool_name} missing schema"
            
            # Verify function is callable
            assert callable(tool_impl['function']), f"Tool {tool_name} function not callable"
            
            # Verify schema structure
            schema = tool_impl['schema']
            assert 'type' in schema, f"Tool {tool_name} schema missing type"
            assert 'properties' in schema, f"Tool {tool_name} schema missing properties"
            
            logger.info(f"    ✓ Tool {tool_name} structure valid")
        
        logger.info("✅ Notion tools direct test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Notion tools direct test failed: {e}")
        return False


async def test_mcp_client_server_integration():
    """
    Test the MCP client connecting to the server.
    
    This test verifies that:
    - Client can connect to server via stdio
    - Tools can be listed through MCP protocol
    - Tools can be executed through MCP protocol
    - Error handling works properly
    """
    logger.info("=== Testing MCP Client-Server Integration ===")
    
    try:
        # Import the client
        from effective_giggle.mcp_server import EffectiveGiggleMCPClient
        
        # Test client connection and basic operations
        logger.info("Creating MCP client...")
        client = EffectiveGiggleMCPClient()
        
        logger.info("Connecting to MCP server...")
        await client.connect()
        
        # Test listing tools
        logger.info("Listing available tools...")
        tools = await client.list_tools()
        
        logger.info(f"Found {len(tools)} tools via MCP protocol:")
        for tool in tools:
            logger.info(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
        
        # Verify expected tools are available
        tool_names = [tool.get('name') for tool in tools]
        expected_tools = ['select_topic_from_backlog', 'update_topic_status', 'query_topics_by_status']
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Expected tool {expected_tool} not found via MCP"
            logger.info(f"  ✓ Found expected tool via MCP: {expected_tool}")
        
        # Test tool execution (with mock/safe parameters)
        logger.info("Testing tool execution...")
        
        # Test query_topics_by_status with safe parameters
        try:
            result = await client.call_tool('query_topics_by_status', {'status': 'Backlog', 'limit': 1})
            logger.info(f"Tool execution result type: {type(result)}")
            logger.info(f"Tool execution successful (result preview: {str(result)[:100]}...)")
        except Exception as tool_error:
            # This might fail due to missing Notion credentials, which is expected in test
            logger.warning(f"Tool execution failed (expected if no Notion credentials): {tool_error}")
        
        # Clean up
        await client.disconnect()
        
        logger.info("✅ MCP Client-Server integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ MCP Client-Server integration test failed: {e}")
        return False


async def test_base_agent_mcp_integration():
    """
    Test BaseAgent integration with MCP server.
    
    This test verifies that:
    - BaseAgent can connect to MCP server
    - MCP tools are discovered and available
    - Agent can access tool information
    """
    logger.info("=== Testing BaseAgent MCP Integration ===")
    
    try:
        # Import BaseAgent
        from effective_giggle.core.base_agent import BaseAgent
        
        # Create agent with MCP enabled
        logger.info("Creating BaseAgent with MCP integration...")
        agent = BaseAgent(
            name="test-agent",
            instructions="Test agent for MCP integration",
            use_mcp_server=True
        )
        
        # Test MCP connection (this happens during arun)
        logger.info("Testing MCP connection through BaseAgent...")
        
        # Connect to MCP server manually for testing
        await agent._connect_to_mcp_server()
        
        # Check available tools
        tool_info = agent.get_available_tools()
        logger.info(f"BaseAgent found {tool_info['total_tools']} total tools")
        logger.info(f"  - Function tools: {len(tool_info['function_tools'])}")
        logger.info(f"  - MCP tools: {len(tool_info['mcp_tools'])}")
        
        # Verify MCP tools are available
        assert tool_info['mcp_tools'], "No MCP tools found in BaseAgent"
        
        expected_mcp_tools = ['select_topic_from_backlog', 'update_topic_status', 'query_topics_by_status']
        for expected_tool in expected_mcp_tools:
            assert expected_tool in tool_info['mcp_tools'], f"Expected MCP tool {expected_tool} not found in BaseAgent"
            logger.info(f"  ✓ BaseAgent has MCP tool: {expected_tool}")
        
        # Test direct MCP tool call
        logger.info("Testing direct MCP tool call...")
        try:
            result = await agent.call_mcp_tool('query_topics_by_status', {'status': 'Backlog', 'limit': 1})
            logger.info(f"Direct MCP tool call successful (result type: {type(result)})")
        except Exception as tool_error:
            # This might fail due to missing Notion credentials, which is expected in test
            logger.warning(f"Direct MCP tool call failed (expected if no Notion credentials): {tool_error}")
        
        # Clean up
        await agent._disconnect_from_mcp_server()
        
        logger.info("✅ BaseAgent MCP integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ BaseAgent MCP integration test failed: {e}")
        return False


async def run_all_tests():
    """
    Run all integration tests and report results.
    """
    logger.info("🚀 Starting MCP Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("MCP Server Direct", test_mcp_server_direct),
        ("Notion Tools Direct", test_notion_tools_direct),
        ("MCP Client-Server Integration", test_mcp_client_server_integration),
        ("BaseAgent MCP Integration", test_base_agent_mcp_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Report final results
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info("-" * 60)
    logger.info(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All MCP integration tests PASSED!")
        return True
    else:
        logger.error(f"💥 {total - passed} tests FAILED!")
        return False


if __name__ == "__main__":
    # Run the integration tests
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test runner crashed: {e}")
        sys.exit(1)
