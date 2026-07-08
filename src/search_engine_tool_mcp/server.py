"""MCP Server implementation for Search Engine Tool."""

import logging
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .search import web_search as _web_search_impl
from .extract import web_extract as _web_extract_impl
from .schemas import WebSearchParams, WebExtractParams

# Load .env file from project root directory
# Try multiple locations to find .env file
env_paths = [
    Path(__file__).parent.parent.parent / ".env",  # project root
    Path.cwd() / ".env",  # current working directory
    Path.home() / ".env",  # home directory
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        logging.info(f"Loaded environment variables from {env_path}")
        break

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("search-engine-tool-mcp")

# Create FastMCP instance
mcp = FastMCP("search-engine-tool-mcp")


@mcp.tool()
async def web_search(
    query: str,
    provider: str = "auto",
    max_results: int = 5,
    search_depth: str = "basic",
    include_answer: bool = False
) -> dict:
    """
    Search the web for information using multiple providers (You.com/Tavily).

    Args:
        query: Search query string
        provider: Provider to use: auto (default), you (requires YDC_API_KEY), or tavily (requires TAVILY_API_KEY)
        max_results: Maximum number of results to return (1-20)
        search_depth: Search depth (Tavily only): basic or advanced
        include_answer: Include AI-generated answer (Tavily only)

    Returns:
        Search results with query, provider, count, and results list
    """
    params = WebSearchParams(
        query=query,
        provider=provider,
        max_results=max_results,
        search_depth=search_depth,
        include_answer=include_answer
    )
    result = await _web_search_impl(
        query=params.query,
        provider=params.provider,
        max_results=params.max_results,
        search_depth=params.search_depth,
        include_answer=params.include_answer
    )
    return result.model_dump()


@mcp.tool()
async def web_extract(
    url: str,
    provider: str = "auto"
) -> dict:
    """
    Extract content from a specific URL.

    Provider options:
    - local: Free local extraction, no API key required
    - tavily: Tavily API extraction, requires TAVILY_API_KEY
    - auto: Default, tries local first, falls back to Tavily if available

    Args:
        url: URL to extract content from
        provider: Provider to use: auto (default), local, or tavily (requires TAVILY_API_KEY)

    Returns:
        Extracted content with url, content, and provider
    """
    params = WebExtractParams(url=url, provider=provider)
    result = await _web_extract_impl(
        url=params.url,
        provider=params.provider
    )
    return result.model_dump()


def run():
    """Entry point for command-line interface."""
    logger.info("Starting MCP Server...")
    mcp.run()  # FastMCP handles everything automatically


if __name__ == "__main__":
    run()