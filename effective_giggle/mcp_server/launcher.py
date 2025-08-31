#!/usr/bin/env python3
"""MCP Server Launcher for Effective Giggle Pipeline

This script provides an easy way to start the MCP server for development
and production use. It handles configuration, logging setup, and graceful
shutdown.

Usage:
    python -m effective_giggle.mcp_server.launcher
    
    Or directly:
    python effective_giggle/mcp_server/launcher.py

The server will start on localhost:8000 by default and can be configured
via environment variables or command line arguments.
"""

import argparse
import asyncio
import logging
import signal
import sys
from typing import Optional

from .server import EffectiveGiggleMCPServer


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging for the MCP server.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('mcp_server.log')
        ]
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for the MCP server.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Start the Effective Giggle MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Start server with default settings
    python -m effective_giggle.mcp_server.launcher
    
    # Start with debug logging
    python -m effective_giggle.mcp_server.launcher --log-level DEBUG
    
    # Start on custom host/port
    python -m effective_giggle.mcp_server.launcher --host 0.0.0.0 --port 9000
        """
    )
    
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host address to bind the server (default: localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number to bind the server (default: 8000)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Check configuration and exit without starting server"
    )
    
    return parser.parse_args()


async def main() -> None:
    """
    Main entry point for the MCP server launcher.
    
    This function:
    1. Parses command line arguments
    2. Sets up logging
    3. Validates configuration
    4. Starts the MCP server
    5. Handles graceful shutdown
    """
    args = parse_arguments()
    
    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger("effective_giggle.mcp_server.launcher")
    
    logger.info("Starting Effective Giggle MCP Server Launcher")
    logger.info(f"Configuration: host={args.host}, port={args.port}, log_level={args.log_level}")
    
    # Check configuration if requested
    if args.check_config:
        logger.info("Checking configuration...")
        try:
            from ..core.settings import get_settings
            settings = get_settings()
            
            # Validate required settings
            required_settings = [
                ("openai_api_key", "OpenAI API key"),
                ("notion_api_key", "Notion API key"), 
                ("notion_database_id", "Notion database ID")
            ]
            
            missing_settings = []
            for setting_name, description in required_settings:
                if not getattr(settings, setting_name, None):
                    missing_settings.append(f"  - {setting_name}: {description}")
            
            if missing_settings:
                logger.error("Missing required configuration:")
                for setting in missing_settings:
                    logger.error(setting)
                logger.error("Please check your .env file and ensure all required settings are provided")
                sys.exit(1)
            else:
                logger.info("✅ Configuration check passed - all required settings are present")
                sys.exit(0)
                
        except Exception as e:
            logger.error(f"Configuration check failed: {e}")
            sys.exit(1)
    
    # Create and configure the MCP server
    server: Optional[EffectiveGiggleMCPServer] = None
    
    try:
        logger.info("Initializing MCP server...")
        server = EffectiveGiggleMCPServer(host=args.host, port=args.port)
        
        # Display server information
        tool_info = server.get_tool_info()
        logger.info(f"Server initialized with {tool_info['total_tools']} tools:")
        for tool_name, tool_data in tool_info['tools'].items():
            logger.info(f"  - {tool_name}: {tool_data['description']}")
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            if server:
                asyncio.create_task(server.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the server
        logger.info("🚀 Starting MCP server...")
        await server.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        if server:
            await server.stop()
        logger.info("MCP server launcher finished")


if __name__ == "__main__":
    # Run the launcher
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
