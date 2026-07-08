"""Data schemas for search engine tool."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Single search result item."""

    href: str = Field(..., description="URL of the search result")
    title: str = Field(..., description="Title of the search result")
    abstract: str = Field(default="", description="Snippet or summary of the search result")


class SearchResponse(BaseModel):
    """Search API response."""

    query: str = Field(..., description="Original search query")
    provider: str = Field(..., description="Provider used (jina/tavily)")
    count: int = Field(..., description="Number of results returned")
    results: List[SearchResult] = Field(default_factory=list, description="Search results")


class ExtractResult(BaseModel):
    """Single extraction result."""

    url: str = Field(..., description="URL of the extracted content")
    content: str = Field(..., description="Extracted content")
    provider: str = Field(..., description="Provider used (jina/tavily)")


class WebSearchParams(BaseModel):
    """Parameters for web_search tool."""

    query: str = Field(..., description="Search query string")
    provider: str = Field(default="auto", description="Provider: auto/jina/tavily")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of results")
    search_depth: str = Field(default="basic", description="Search depth: basic/advanced")
    include_answer: bool = Field(default=False, description="Include AI-generated answer")


class WebExtractParams(BaseModel):
    """Parameters for web_extract tool."""

    url: str = Field(..., description="URL to extract content from")
    provider: str = Field(default="auto", description="Provider: auto/jina/tavily")