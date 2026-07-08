"""Web search functionality with provider routing."""

import os
from typing import List
from .schemas import SearchResult, SearchResponse
from .providers import YouProvider, TavilyProvider


async def web_search(
    query: str,
    provider: str = "auto",
    max_results: int = 5,
    search_depth: str = "basic",
    include_answer: bool = False
) -> SearchResponse:
    """
    Perform web search with automatic provider selection.

    Args:
        query: Search query string
        provider: Provider to use (auto/you/tavily)
        max_results: Maximum number of results to return
        search_depth: Search depth (basic/advanced) - Tavily only
        include_answer: Include AI-generated answer - Tavily only

    Returns:
        SearchResponse object with results

    Raises:
        ValueError: If invalid provider specified
    """
    # Determine which provider to use
    actual_provider = _resolve_provider(provider)

    # Execute search based on provider
    results: List[SearchResult] = []

    if actual_provider == "you":
        you = YouProvider()
        results = await you.search(query, max_results)
    elif actual_provider == "tavily":
        tavily = TavilyProvider()  # Will raise ValueError if no API key
        results = await tavily.search(
            query,
            max_results,
            search_depth,
            include_answer
        )
    else:
        raise ValueError(f"Unknown provider: {actual_provider}")

    return SearchResponse(
        query=query,
        provider=actual_provider,
        count=len(results),
        results=results
    )


def _resolve_provider(provider: str) -> str:
    """
    Resolve provider based on setting and environment.

    Args:
        provider: Provider string (auto/you/tavily)

    Returns:
        Resolved provider name (you/tavily)

    Raises:
        ValueError: If invalid provider specified or no API key available
    """
    if provider == "you":
        # Will fail later in YouProvider if no API key
        return "you"
    elif provider == "tavily":
        # Will fail later in TavilyProvider if no API key
        return "tavily"
    elif provider == "auto":
        # Auto-select: prioritize You.com, then Tavily
        if os.getenv("YDC_API_KEY"):
            return "you"
        elif os.getenv("TAVILY_API_KEY"):
            return "tavily"
        else:
            raise ValueError(
                "Either YDC_API_KEY or TAVILY_API_KEY is required. "
                "Set one of these environment variables to use the search functionality."
            )
    else:
        raise ValueError(f"Invalid provider: {provider}. Must be 'auto', 'you', or 'tavily'")