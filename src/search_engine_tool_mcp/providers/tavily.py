"""Tavily provider for search and extraction."""

from typing import List, Optional
import os
import httpx
from ..schemas import SearchResult, ExtractResult


class TavilyProvider:
    """Tavily provider implementation (requires TAVILY_API_KEY)."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily provider.

        Args:
            api_key: Tavily API key. If not provided, reads from TAVILY_API_KEY env var.

        Raises:
            ValueError: If API key is not provided and not found in environment
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Tavily API key is required. Set TAVILY_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.base_url = "https://api.tavily.com"

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_answer: bool = False
    ) -> List[SearchResult]:
        """
        Search using Tavily API.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            search_depth: Search depth (basic/advanced)
            include_answer: Whether to include AI-generated answer

        Returns:
            List of SearchResult objects
        """
        url = f"{self.base_url}/search"

        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": include_answer
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("results", []):
                    results.append(SearchResult(
                        href=item.get("url", ""),
                        title=item.get("title", ""),
                        abstract=item.get("content", "")
                    ))
                return results
            except Exception as e:
                raise RuntimeError(f"Tavily search failed: {str(e)}")

    async def extract(self, url: str) -> ExtractResult:
        """
        Extract content from a URL using Tavily Extract API.

        Args:
            url: URL to extract content from

        Returns:
            ExtractResult object
        """
        extract_url = f"{self.base_url}/extract"

        payload = {
            "api_key": self.api_key,
            "urls": [url]
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(extract_url, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                if results and len(results) > 0:
                    content = results[0].get("raw_content", "")
                else:
                    content = ""

                return ExtractResult(
                    url=url,
                    content=content,
                    provider="tavily"
                )
            except Exception as e:
                raise RuntimeError(f"Tavily extraction failed: {str(e)}")