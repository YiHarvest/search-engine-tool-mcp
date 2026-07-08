"""You.com provider for search and extraction."""

import os
from typing import List, Optional
import httpx
from ..schemas import SearchResult, ExtractResult


class YouProvider:
    """You.com provider implementation (requires YDC_API_KEY)."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize You.com provider.

        Args:
            api_key: You.com API key. If not provided, reads from YDC_API_KEY env var.

        Raises:
            ValueError: If API key is not provided and not found in environment
        """
        self.api_key = api_key or os.getenv("YDC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "YDC_API_KEY is required for You.com provider. "
                "Set YDC_API_KEY environment variable or pass api_key parameter. "
                "Get your API key at https://you.com/platform"
            )
        
        self.search_url = "https://ydc-index.io/v1/search"
        self.headers = {
            "X-API-Key": self.api_key,
            "User-Agent": "SearchEngineToolMCP/0.2.0"
        }

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Search using You.com Search API.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of SearchResult objects
        """
        params = {
            "query": query,
            "count": max_results
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.search_url,
                    params=params,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                results = []
                # Parse response from You.com API
                web_results = data.get("results", {}).get("web", [])
                
                for item in web_results[:max_results]:
                    # Combine description and snippets for abstract
                    description = item.get("description", "")
                    snippets = item.get("snippets", [])
                    abstract = description or (snippets[0] if snippets else "")
                    
                    results.append(SearchResult(
                        href=item.get("url", ""),
                        title=item.get("title", ""),
                        abstract=abstract
                    ))
                
                return results
            except Exception as e:
                raise RuntimeError(f"You.com search failed: {str(e)}")

    async def extract(self, url: str) -> ExtractResult:
        """
        Extract content from a URL using You.com Contents API.

        Note: You.com doesn't have a direct extraction endpoint like Jina's r.jina.ai,
        but we can use the search API with livecrawl parameter for basic extraction.
        For full extraction, recommend using Jina Reader or Tavily.

        Args:
            url: URL to extract content from

        Returns:
            ExtractResult object
        """
        # You.com doesn't provide a standalone extraction endpoint
        # We recommend using Jina Reader or Tavily for extraction
        raise NotImplementedError(
            "You.com provider does not support URL extraction. "
            "Please use Jina (r.jina.ai) or Tavily for content extraction, "
            "or switch provider to 'auto', 'jina', or 'tavily' for web_extract tool."
        )