"""Content Creation Pipeline - Main Entry Point

This script demonstrates the proper OpenAI Agents SDK usage pattern for running
a multi-agent workflow from topic selection through research.

Usage:
    python main.py

The pipeline:
1. Topic Selector - selects a topic from Notion backlog and promotes to candidate
2. Researcher - researches the selected topic and produces digest + citations
"""

import asyncio
from agents import Agent, Runner

from effective_giggle.core.settings import get_settings
from effective_giggle.agents.topic_selector.agent import create as create_topic_selector
from effective_giggle.agents.researcher.agent import create as create_researcher


async def main():
    """Run the content creation pipeline end-to-end."""
    
    print("🚀 Starting Content Creation Pipeline")
    print("=" * 50)
    
    # Create agents following SDK patterns
    topic_selector = create_topic_selector().agent
    researcher = create_researcher().agent
    
    # Set up handoffs - topic_selector hands off to researcher
    topic_selector.handoffs = [researcher]
    
    # Update instructions to include handoff behavior
    topic_selector.instructions = (
        "You are a strategic content agent. When invoked you must:\n"
        "1. Choose exactly one topic from the backlog using the Notion tool\n"
        "2. Promote its status to 'Candidate'\n"
        "3. Hand off to the researcher with the selected topic data\n\n"
        "Always hand off to the researcher after selecting a topic."
    )
    
    try:
        print("📋 Step 1: Selecting topic from Notion backlog...")
        
        # Start the pipeline with the topic selector
        result = await Runner.run(
            topic_selector, 
            "Select a topic from the backlog and hand it off for research",
            max_turns=15  # Allow for handoffs and tool calls
        )
        
        print("\n✅ Pipeline completed successfully!")
        print("=" * 50)
        print("Final Result:")
        print(result.final_output)
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        print("Check your .env file has valid OPENAI_API_KEY, NOTION_API_KEY, and EG_NOTION_DB_ID")


if __name__ == "__main__":
    # Ensure we have required settings
    settings = get_settings()
    print(f"Using model: {settings.default_model}")
    print(f"Notion DB ID: {settings.notion_database_id[:8]}...")
    print()
    
    # Run the async pipeline
    asyncio.run(main())
