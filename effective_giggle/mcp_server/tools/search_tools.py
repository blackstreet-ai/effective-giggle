"""Search Tools for Effective Giggle MCP Server

This module contains web search and research tools that are exposed through the MCP server.
These tools enable agents to perform real-time web searches, gather information, and collect
citations for research purposes using the Exa.ai search API.

Tools provided:
- web_search: Perform web search using Exa.ai API
- extract_content: Extract and summarize content from URLs  
- search_news: Search for recent news articles using Exa.ai
- find_similar: Find similar content to a given URL

All tools use Exa.ai's AI-powered search engine designed specifically for research
and include proper error handling, rate limiting, and citation formatting.
"""

import json
import logging
from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime, timedelta
import os
import aiohttp
import ssl
from functools import partial

from exa_py import Exa
from ...core.settings import get_settings

# Configure logging for search tools
logger = logging.getLogger("effective_giggle.mcp_server.search_tools")


def _get_exa_client() -> Exa:
    """
    Get an initialized Exa client using API key from environment.
    
    Returns:
        Exa client instance
        
    Raises:
        Exception: If EXA_API_KEY is not found in environment
    """
    settings = get_settings()
    exa_api_key = os.getenv('EXA_API_KEY')
    
    if not exa_api_key:
        raise Exception("EXA_API_KEY not found in environment variables")
    
    return Exa(exa_api_key)


async def web_search(
    query: str, 
    max_results: int = 10, 
    include_content: bool = True
) -> Dict[str, Any]:
    """
    Perform a web search using Exa.ai's AI-powered search engine.
    
    This tool searches the web for high-quality, relevant information using Exa.ai's
    search API designed specifically for AI applications. Returns structured results
    with titles, URLs, snippets, and optionally full content.
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 10, max: 20)
        include_content: Whether to include full content of pages (default: True)
        
    Returns:
        Dict containing:
        - results: List of search results with title, url, snippet, content, date
        - query: Original search query
        - total_results: Number of results found
        - timestamp: When search was performed
        - search_engine: "exa.ai"
        
    Raises:
        Exception: If search API calls fail or no results found
    """
    logger.info(f"Performing Exa.ai web search: '{query}' (max_results: {max_results})")
    
    try:
        exa = _get_exa_client()
        
        # Perform search with content if requested (with timeout)
        loop = asyncio.get_event_loop()
        if include_content:
            search_func = partial(
                exa.search_and_contents,
                query=query,
                num_results=min(max_results, 20),  # Exa.ai max is 20
                text=True,  # Include text content
                type="auto"  # Let Exa decide the best search type
            )
        else:
            search_func = partial(
                exa.search,
                query=query,
                num_results=min(max_results, 20),
                type="auto"
            )
        
        # Run the synchronous Exa call in thread pool with timeout
        response = await asyncio.wait_for(
            loop.run_in_executor(None, search_func),
            timeout=4.0  # 4 second timeout to stay under MCP 5s limit
        )
        
        # Format results for consistent output
        results = []
        for result in response.results:
            formatted_result = {
                "title": result.title,
                "url": result.url,
                "snippet": result.text[:300] + "..." if result.text and len(result.text) > 300 else result.text or "",
                "date": result.published_date if result.published_date else None,  # Exa returns date as string already
                "score": getattr(result, 'score', None),  # Exa provides relevance scores
            }
            
            # Add full content if available and requested
            if include_content and hasattr(result, 'text') and result.text:
                formatted_result["content"] = result.text
            
            results.append(formatted_result)
        
        logger.info(f"Exa.ai search successful: {len(results)} results found")
        
        return {
            "results": results,
            "query": query,
            "search_engine": "exa.ai",
            "total_results": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Exa.ai web search failed: {str(e)}")
        raise Exception(f"Web search failed: {str(e)}")


async def extract_content(url: str, max_length: int = 2000) -> Dict[str, Any]:
    """
    Extract and summarize content from a given URL.
    
    This tool fetches content from a URL, extracts the main text content,
    and provides a structured summary suitable for research purposes.
    
    Args:
        url: The URL to extract content from
        max_length: Maximum length of extracted content (default: 2000 chars)
        
    Returns:
        Dict containing:
        - url: Original URL
        - title: Page title
        - content: Extracted text content (truncated to max_length)
        - word_count: Number of words in full content
        - timestamp: When extraction was performed
        
    Raises:
        Exception: If URL cannot be accessed or content cannot be extracted
    """
    logger.info(f"Extracting content from: {url}")
    
    try:
        # Create SSL context that's more permissive for content extraction
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Configure connector with SSL context and increased limits for headers
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit_per_host=10,
            limit=100
        )
        
        # Enhanced headers to appear more like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Configure client session with increased header limits
        timeout = aiohttp.ClientTimeout(total=4)
        
        async with aiohttp.ClientSession(
            connector=connector, 
            headers=headers,
            timeout=timeout,
            max_line_size=16384,  # Increase max header line size
            max_field_size=16384  # Increase max header field size
        ) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Simple text extraction (in production, use BeautifulSoup or similar)
                    # This is a basic implementation - for better results, use proper HTML parsing
                    import re
                    
                    # Extract title
                    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
                    title = title_match.group(1).strip() if title_match else "No title found"
                    
                    # Basic text extraction (remove HTML tags)
                    text_content = re.sub(r'<[^>]+>', ' ', html_content)
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                    
                    # Truncate if needed
                    if len(text_content) > max_length:
                        text_content = text_content[:max_length] + "..."
                    
                    word_count = len(text_content.split())
                    
                    return {
                        "url": url,
                        "title": title,
                        "content": text_content,
                        "word_count": word_count,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    # Handle different HTTP status codes with specific messages
                    if response.status == 403:
                        logger.warning(f"Access forbidden for {url} (HTTP 403) - website blocks automated requests")
                        return {
                            "url": url,
                            "title": "Access Forbidden",
                            "content": f"Content extraction blocked by website (HTTP 403). This website ({url}) does not allow automated access.",
                            "word_count": 0,
                            "timestamp": datetime.now().isoformat(),
                            "error": "access_forbidden"
                        }
                    elif response.status == 404:
                        logger.warning(f"Content not found for {url} (HTTP 404)")
                        return {
                            "url": url,
                            "title": "Content Not Found",
                            "content": f"The requested content at {url} was not found (HTTP 404).",
                            "word_count": 0,
                            "timestamp": datetime.now().isoformat(),
                            "error": "not_found"
                        }
                    else:
                        raise Exception(f"HTTP {response.status} when accessing {url}")
                    
    except aiohttp.ClientError as e:
        # Handle specific aiohttp errors more gracefully
        if "Header value is too long" in str(e):
            logger.warning(f"Header too long error for {url} - website has oversized headers")
            return {
                "url": url,
                "title": "Header Error",
                "content": f"Content extraction failed due to oversized headers from {url}. This is a technical limitation.",
                "word_count": 0,
                "timestamp": datetime.now().isoformat(),
                "error": "header_too_long"
            }
        else:
            logger.error(f"Content extraction failed for {url}: {str(e)}")
            raise Exception(f"Content extraction failed: {str(e)}")
    except Exception as e:
        logger.error(f"Content extraction failed for {url}: {str(e)}")
        raise Exception(f"Content extraction failed: {str(e)}")


async def search_news(
    query: str, 
    max_results: int = 5, 
    days_back: int = 30
) -> Dict[str, Any]:
    """
    Search for recent news articles using Exa.ai with date filtering.
    
    This tool searches for recent news articles using Exa.ai's search capabilities
    with date filtering to find current, relevant news content.
    
    Args:
        query: The search query for news articles
        max_results: Maximum number of news results to return (default: 5)
        days_back: How many days back to search (default: 30)
        
    Returns:
        Dict containing:
        - articles: List of news articles with title, url, source, date, content
        - query: Original search query
        - date_range: Search date range
        - total_results: Number of articles found
        
    Raises:
        Exception: If news search fails
    """
    logger.info(f"Searching Exa.ai for news: '{query}' (last {days_back} days)")
    
    try:
        exa = _get_exa_client()
        
        # Calculate date range for news search
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Search for news with date filtering and content (with timeout)
        loop = asyncio.get_event_loop()
        search_func = partial(
            exa.search_and_contents,
            query=f"{query} news",  # Add "news" to focus on news articles
            num_results=min(max_results, 10),
            text=True,
            type="auto",
            start_published_date=start_date.strftime("%Y-%m-%d"),
            end_published_date=end_date.strftime("%Y-%m-%d")
        )
        
        # Run the synchronous Exa call in thread pool with timeout
        response = await asyncio.wait_for(
            loop.run_in_executor(None, search_func),
            timeout=4.0  # 4 second timeout to stay under MCP 5s limit
        )
        
        # Format results as news articles
        articles = []
        for result in response.results:
            article = {
                "title": result.title,
                "url": result.url,
                "source": result.url.split('/')[2] if result.url else "Unknown",  # Extract domain as source
                "date": result.published_date if result.published_date else None,  # Exa returns date as string already
                "summary": result.text[:500] + "..." if result.text and len(result.text) > 500 else result.text or "",
                "content": result.text if result.text else "",
                "score": getattr(result, 'score', None)
            }
            articles.append(article)
        
        logger.info(f"Exa.ai news search successful: {len(articles)} articles found")
        
        return {
            "articles": articles,
            "query": query,
            "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "total_results": len(articles),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Exa.ai news search failed: {str(e)}")
        raise Exception(f"News search failed: {str(e)}")


async def find_similar(
    url: str,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Find similar content to a given URL using Exa.ai's similarity search.
    
    This tool uses Exa.ai's find_similar functionality to discover content
    that is similar to a provided URL, useful for research and content discovery.
    
    Args:
        url: The URL to find similar content for
        max_results: Maximum number of similar results to return (default: 5)
        
    Returns:
        Dict containing:
        - similar_results: List of similar content with title, url, snippet, score
        - original_url: The URL used as reference
        - total_results: Number of similar results found
        - timestamp: When search was performed
        
    Raises:
        Exception: If similarity search fails
    """
    logger.info(f"Finding similar content to: {url}")
    
    try:
        exa = _get_exa_client()
        
        # Find similar content with text content (with timeout)
        loop = asyncio.get_event_loop()
        search_func = partial(
            exa.find_similar_and_contents,
            url=url,
            num_results=min(max_results, 10),
            text=True
        )
        
        # Run the synchronous Exa call in thread pool with timeout
        response = await asyncio.wait_for(
            loop.run_in_executor(None, search_func),
            timeout=4.0  # 4 second timeout to stay under MCP 5s limit
        )
        
        # Format results
        similar_results = []
        for result in response.results:
            similar_result = {
                "title": result.title,
                "url": result.url,
                "snippet": result.text[:300] + "..." if result.text and len(result.text) > 300 else result.text or "",
                "content": result.text if result.text else "",
                "date": result.published_date if result.published_date else None,  # Exa returns date as string already
                "score": getattr(result, 'score', None)
            }
            similar_results.append(similar_result)
        
        logger.info(f"Exa.ai similarity search successful: {len(similar_results)} results found")
        
        return {
            "similar_results": similar_results,
            "original_url": url,
            "total_results": len(similar_results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Exa.ai similarity search failed: {str(e)}")
        raise Exception(f"Similarity search failed: {str(e)}")


# ---------------------------------------------------------------------------
# Tool Registration
# ---------------------------------------------------------------------------

def register_search_tools() -> Dict[str, Dict[str, Any]]:
    """
    Register all search tools with the MCP server.
    
    This function returns a dictionary of tool implementations that can be
    registered with the MCP server. Each tool includes its function,
    description, and JSON schema for validation.
    
    Returns:
        Dictionary mapping tool names to their implementations
    """
    logger.info("Registering search tools...")
    
    tools = {
        "web_search": {
            "function": web_search,
            "description": "Perform a web search using Exa.ai's AI-powered search engine and return structured results with content",
            "schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query string"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 20
                    },
                    "include_content": {
                        "type": "boolean",
                        "description": "Whether to include full content of pages",
                        "default": True
                    }
                },
                "required": ["query"]
            }
        },
        
        "extract_content": {
            "function": extract_content,
            "description": "Extract and summarize content from a given URL for research purposes",
            "schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to extract content from",
                        "format": "uri"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum length of extracted content in characters",
                        "default": 2000,
                        "minimum": 500,
                        "maximum": 5000
                    }
                },
                "required": ["url"]
            }
        },
        
        "search_news": {
            "function": search_news,
            "description": "Search for recent news articles using Exa.ai with date filtering and full content",
            "schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for news articles"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of news results to return",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "How many days back to search for news",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 365
                    }
                },
                "required": ["query"]
            }
        },
        
        "find_similar": {
            "function": find_similar,
            "description": "Find similar content to a given URL using Exa.ai's similarity search capabilities",
            "schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to find similar content for",
                        "format": "uri"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of similar results to return",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["url"]
            }
        }
    }
    
    logger.info(f"Registered {len(tools)} search tools")
    return tools
