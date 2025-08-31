"""Simplified Content Creation Pipeline using OpenAI Agents SDK.

This demonstrates the proper usage of the OpenAI Agents SDK with native MCP integration.
No custom wrappers, no manual orchestration - just clean agent-to-agent handoffs.
"""

import asyncio
import pathlib
from dotenv import load_dotenv
from agents import Runner, handoff, RunContextWrapper

# Load .env file from project root to ensure environment variables are available
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env", override=False)

# Import from our local pipeline_agents.py file  
import pipeline_agents
TopicData = pipeline_agents.TopicData
create_topic_selector = pipeline_agents.create_topic_selector
create_researcher = pipeline_agents.create_researcher


async def on_research_handoff(ctx: RunContextWrapper[None], topic_data: TopicData):
    """Callback function executed when topic selector hands off to researcher."""
    print(f"🔍 Research handoff received!")
    print(f"📋 Topic: {topic_data.topic}")
    print(f"🎯 Angle: {topic_data.angle}")
    print(f"📄 Page ID: {topic_data.page_id}")
    
    # CRITICAL: Actually execute the researcher agent using proper OpenAI Agents SDK approach
    print(f"🚀 Starting researcher execution...")
    
    # Create researcher agent (fresh instance for this research task)
    researcher = create_researcher()
    
    # Connect MCP servers for researcher
    for server in researcher.mcp_servers:
        await server.connect()
    
    # Create detailed research assignment that the researcher agent will execute
    research_assignment = f"""**RESEARCH ASSIGNMENT**

You have received a research handoff with the following topic data:

- **Topic**: {topic_data.topic}
- **Angle**: {topic_data.angle}  
- **Stance**: {topic_data.stance}
- **Page ID**: {topic_data.page_id}
- **Audience**: {topic_data.audience}
- **Geo Focus**: {topic_data.geo_focus}
- **Time Window**: {topic_data.time_window}

Execute your complete research workflow as defined in your instructions:

1. Update topic status to 'Research' using the page_id
2. Conduct comprehensive web search on the topic and angle
3. Search for recent news and developments
4. Extract detailed content from the most relevant sources
5. Compile findings into a comprehensive research report
6. Save the research to a new Notion page
7. Update topic status to 'Complete'

Use your available MCP tools to execute each step. Focus on the specific topic, angle, and stance provided. Provide detailed, substantive research content with proper citations."""
    
    try:
        # Execute the researcher agent using the OpenAI Agents SDK
        print(f"🔬 Running researcher agent with topic: {topic_data.topic}")
        
        research_result = await Runner.run(
            researcher,
            research_assignment,
            max_turns=15  # Allow multiple turns for the complete workflow
        )
        
        print(f"✅ Research workflow completed successfully!")
        print(f"📊 Research result length: {len(research_result.final_output)} characters")
        print(f"🔄 Research took {len(research_result.new_items)} agent turns")
        
        # Clean up researcher MCP connections
        for server in researcher.mcp_servers:
            try:
                if hasattr(server, 'disconnect'):
                    await server.disconnect()
            except Exception:
                pass
        
        return f"Research completed successfully for topic: {topic_data.topic}. Research saved to Notion. Final result: {research_result.final_output[:200]}..."
        
    except Exception as e:
        print(f"❌ Research workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return f"Research failed for topic: {topic_data.topic}. Error: {str(e)}"


async def main():
    """Run the simplified content creation pipeline."""
    print("🚀 Starting Simplified Content Creation Pipeline")
    print("=" * 60)
    
    # Create agents using native OpenAI SDK with MCP integration
    topic_selector = create_topic_selector()
    researcher = create_researcher()
    
    # Collect all MCP servers for proper cleanup
    all_servers = topic_selector.mcp_servers + researcher.mcp_servers
    
    try:
        # Connect MCP servers
        print("🔌 Connecting to MCP servers...")
        for server in all_servers:
            await server.connect()
        print("✅ MCP servers connected")
        
        # Set up handoff from topic selector to researcher
        research_handoff = handoff(
            agent=researcher,
            input_type=TopicData,
            on_handoff=on_research_handoff,
            tool_description_override="Transfer to researcher with complete topic data"
        )
        topic_selector.handoffs = [research_handoff]
        
        print("📋 Starting pipeline with topic selection...")
        
        # Let the SDK handle everything - agent reasoning, tool calling, handoffs
        result = await Runner.run(
            topic_selector,
            "Select a topic from the backlog and hand it off to the researcher for comprehensive research."
        )
        
        print("✅ Pipeline completed successfully!")
        print("=" * 60)
        print("Final Result:")
        print(result.final_output)
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        print("Check your environment variables and MCP server setup")
        import traceback
        traceback.print_exc()
        
    finally:
        # Ensure proper cleanup of MCP server connections
        print("🔌 Cleaning up MCP servers...")
        for server in all_servers:
            try:
                # Check if server has disconnect method before calling
                if hasattr(server, 'disconnect'):
                    await server.disconnect()
                elif hasattr(server, '_client') and hasattr(server._client, 'close'):
                    # Try to close the underlying client connection
                    await server._client.close()
                else:
                    # For SDK-managed servers, let the SDK handle cleanup
                    pass
            except Exception as cleanup_error:
                # Suppress cleanup errors as they don't affect functionality
                pass
        print("✅ MCP server cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
