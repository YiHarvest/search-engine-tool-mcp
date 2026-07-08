"""Tests for web_search functionality."""

import pytest
from unittest.mock import AsyncMock, patch
from search_engine_tool_mcp.search import web_search, _resolve_provider
from search_engine_tool_mcp.schemas import SearchResponse, SearchResult


class TestResolveProvider:
    """Test provider resolution logic."""

    def test_resolve_you(self):
        """Test explicit you provider."""
        result = _resolve_provider("you")
        assert result == "you"

    def test_resolve_tavily(self):
        """Test explicit tavily provider."""
        result = _resolve_provider("tavily")
        assert result == "tavily"

    def test_resolve_auto_both_keys_prioritizes_you(self, monkeypatch):
        """Test auto provider with both keys set prioritizes You.com."""
        monkeypatch.setenv("YDC_API_KEY", "test-you-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        result = _resolve_provider("auto")
        assert result == "you"

    def test_resolve_auto_only_you_key(self, monkeypatch):
        """Test auto provider with only YDC_API_KEY."""
        monkeypatch.setenv("YDC_API_KEY", "test-you-key")
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        result = _resolve_provider("auto")
        assert result == "you"

    def test_resolve_auto_only_tavily_key(self, monkeypatch):
        """Test auto provider with only TAVILY_API_KEY."""
        monkeypatch.delenv("YDC_API_KEY", raising=False)
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        result = _resolve_provider("auto")
        assert result == "tavily"

    def test_resolve_auto_no_keys_raises(self, monkeypatch):
        """Test auto provider without any API keys raises error."""
        monkeypatch.delenv("YDC_API_KEY", raising=False)
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        with pytest.raises(
            ValueError, match="Either YDC_API_KEY or TAVILY_API_KEY is required"
        ):
            _resolve_provider("auto")

    def test_resolve_invalid_provider(self):
        """Test invalid provider raises error."""
        with pytest.raises(ValueError, match="Invalid provider"):
            _resolve_provider("invalid")


class TestWebSearch:
    """Test web_search function."""

    @pytest.mark.asyncio
    async def test_search_with_you(self, monkeypatch):
        """Test search with explicit you provider."""
        monkeypatch.setenv("YDC_API_KEY", "test-you-key")

        mock_results = [
            {
                "href": "https://example.com",
                "title": "Example",
                "abstract": "Example result",
            }
        ]

        with patch("search_engine_tool_mcp.search.YouProvider") as MockYou:
            you_instance = MockYou.return_value
            you_instance.search = AsyncMock(
                return_value=[
                    SearchResult(
                        href=r["href"], title=r["title"], abstract=r["abstract"]
                    )
                    for r in mock_results
                ]
            )

            result = await web_search("test query", provider="you")

            assert isinstance(result, SearchResponse)
            assert result.provider == "you"
            assert result.query == "test query"

    @pytest.mark.asyncio
    async def test_search_auto_without_any_api_key_raises(self, monkeypatch):
        """Test auto provider raises error without any API key."""
        monkeypatch.delenv("YDC_API_KEY", raising=False)
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        with pytest.raises(
            ValueError, match="Either YDC_API_KEY or TAVILY_API_KEY is required"
        ):
            await web_search("test query", provider="auto")

    @pytest.mark.asyncio
    async def test_search_you_without_api_key_raises(self, monkeypatch):
        """Test you provider raises error without API key."""
        monkeypatch.delenv("YDC_API_KEY", raising=False)

        with pytest.raises(ValueError, match="YDC_API_KEY is required"):
            await web_search("test query", provider="you")

    @pytest.mark.asyncio
    async def test_search_tavily_without_api_key_raises(self, monkeypatch):
        """Test tavily provider raises error without API key."""
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        with pytest.raises(ValueError, match="Tavily API key is required"):
            await web_search("test query", provider="tavily")

    @pytest.mark.asyncio
    async def test_search_with_max_results(self, monkeypatch):
        """Test search with custom max_results."""
        monkeypatch.setenv("YDC_API_KEY", "test-you-key")

        with patch("search_engine_tool_mcp.search.YouProvider") as MockYou:
            you_instance = MockYou.return_value
            you_instance.search = AsyncMock(return_value=[])

            await web_search("test query", provider="you", max_results=10)

            you_instance.search.assert_called_once_with("test query", 10)
