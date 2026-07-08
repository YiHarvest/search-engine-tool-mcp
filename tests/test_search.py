"""Tests for web_search functionality."""

import pytest
from unittest.mock import AsyncMock, patch
from search_engine_tool_mcp.search import web_search, _resolve_provider
from search_engine_tool_mcp.schemas import SearchResponse, SearchResult


class TestResolveProvider:
    """Test provider resolution logic."""

    def test_resolve_searxng(self):
        """Test explicit searxng provider."""
        result = _resolve_provider("searxng")
        assert result == "searxng"

    def test_resolve_you(self):
        """Test explicit you provider."""
        result = _resolve_provider("you")
        assert result == "you"

    def test_resolve_tavily(self):
        """Test explicit tavily provider."""
        result = _resolve_provider("tavily")
        assert result == "tavily"

    def test_resolve_auto_prioritizes_searxng(self, monkeypatch):
        """Test auto provider with SEARXNG_BASE_URL prioritizes SearXNG."""
        monkeypatch.setenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        monkeypatch.setenv("YDC_API_KEY", "test-you-key")
        result = _resolve_provider("auto")
        assert result == "searxng"

    def test_resolve_auto_only_searxng(self, monkeypatch):
        """Test auto provider with only SEARXNG_BASE_URL."""
        monkeypatch.setenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        monkeypatch.delenv("YDC_API_KEY", raising=False)
        result = _resolve_provider("auto")
        assert result == "searxng"

    def test_resolve_auto_only_tavily_key(self, monkeypatch):
        """Test auto provider with only TAVILY_API_KEY."""
        monkeypatch.delenv("SEARXNG_BASE_URL", raising=False)
        monkeypatch.delenv("YDC_API_KEY", raising=False)
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
        result = _resolve_provider("auto")
        assert result == "tavily"

    def test_resolve_auto_only_you_key(self, monkeypatch):
        """Test auto provider with only YDC_API_KEY."""
        monkeypatch.delenv("SEARXNG_BASE_URL", raising=False)
        monkeypatch.setenv("YDC_API_KEY", "test-you-key")
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        result = _resolve_provider("auto")
        assert result == "you"

    def test_resolve_auto_no_keys_raises(self, monkeypatch):
        """Test auto provider without any API keys raises error."""
        monkeypatch.delenv("SEARXNG_BASE_URL", raising=False)
        monkeypatch.delenv("YDC_API_KEY", raising=False)
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        with pytest.raises(ValueError, match="No search provider configured"):
            _resolve_provider("auto")

    def test_resolve_invalid_provider(self):
        """Test invalid provider raises error."""
        with pytest.raises(ValueError, match="Invalid provider"):
            _resolve_provider("invalid")


class TestWebSearch:
    """Test web_search function."""

    @pytest.mark.asyncio
    async def test_search_with_searxng(self, monkeypatch):
        """Test search with explicit searxng provider."""
        monkeypatch.setenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")

        mock_results = [
            SearchResult(
                href="https://example.com",
                title="Example",
                abstract="Example result",
            )
        ]

        with patch("search_engine_tool_mcp.search.SearXNGProvider") as MockSearXNG:
            searxng_instance = MockSearXNG.return_value
            searxng_instance.search = AsyncMock(return_value=mock_results)

            result = await web_search("test query", provider="searxng")

            assert isinstance(result, SearchResponse)
            assert result.provider == "searxng"
            assert result.query == "test query"
            assert len(result.results) == 1

    @pytest.mark.asyncio
    async def test_search_with_you(self, monkeypatch):
        """Test search with explicit you provider."""
        monkeypatch.setenv("YDC_API_KEY", "test-you-key")

        mock_results = [
            SearchResult(
                href="https://example.com",
                title="Example",
                abstract="Example result",
            )
        ]

        with patch("search_engine_tool_mcp.search.YouProvider") as MockYou:
            you_instance = MockYou.return_value
            you_instance.search = AsyncMock(return_value=mock_results)

            result = await web_search("test query", provider="you")

            assert isinstance(result, SearchResponse)
            assert result.provider == "you"
            assert result.query == "test query"

    @pytest.mark.asyncio
    async def test_search_searxng_without_base_url_raises(self, monkeypatch):
        """Test searxng provider raises error without SEARXNG_BASE_URL."""
        monkeypatch.delenv("SEARXNG_BASE_URL", raising=False)

        with pytest.raises(ValueError, match="SearXNG base URL is required"):
            await web_search("test query", provider="searxng")

    @pytest.mark.asyncio
    async def test_search_auto_without_any_api_key_raises(self, monkeypatch):
        """Test auto provider raises error without any API key."""
        monkeypatch.delenv("SEARXNG_BASE_URL", raising=False)
        monkeypatch.delenv("YDC_API_KEY", raising=False)
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        with pytest.raises(ValueError, match="No search provider configured"):
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
    async def test_search_auto_searxng_empty_results_fallback(self, monkeypatch):
        """Test auto provider fallback when SearXNG returns empty results."""
        monkeypatch.setenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")

        mock_empty_results = []
        mock_fallback_results = [
            SearchResult(
                href="https://example.com",
                title="Example",
                abstract="Example result",
            )
        ]

        with patch("search_engine_tool_mcp.search.SearXNGProvider") as MockSearXNG:
            with patch("search_engine_tool_mcp.search.TavilyProvider") as MockTavily:
                searxng_instance = MockSearXNG.return_value
                searxng_instance.search = AsyncMock(return_value=mock_empty_results)

                tavily_instance = MockTavily.return_value
                tavily_instance.search = AsyncMock(return_value=mock_fallback_results)

                result = await web_search("test query", provider="auto")

                # Should fallback to tavily
                assert result.provider == "tavily"
                assert len(result.results) == 1

    @pytest.mark.asyncio
    async def test_search_auto_searxng_timeout_fallback(self, monkeypatch):
        """Test auto provider fallback when SearXNG times out."""
        monkeypatch.setenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")

        mock_fallback_results = [
            SearchResult(
                href="https://example.com",
                title="Example",
                abstract="Example result",
            )
        ]

        with patch("search_engine_tool_mcp.search.SearXNGProvider") as MockSearXNG:
            with patch("search_engine_tool_mcp.search.TavilyProvider") as MockTavily:
                searxng_instance = MockSearXNG.return_value
                searxng_instance.search = AsyncMock(
                    side_effect=RuntimeError("SearXNG search timeout")
                )

                tavily_instance = MockTavily.return_value
                tavily_instance.search = AsyncMock(return_value=mock_fallback_results)

                result = await web_search("test query", provider="auto")

                # Should fallback to tavily
                assert result.provider == "tavily"
                assert len(result.results) == 1

    @pytest.mark.asyncio
    async def test_search_searxng_empty_results_no_fallback(self, monkeypatch):
        """Test explicit searxng provider with empty results does not fallback."""
        monkeypatch.setenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")

        mock_empty_results = []

        with patch("search_engine_tool_mcp.search.SearXNGProvider") as MockSearXNG:
            searxng_instance = MockSearXNG.return_value
            searxng_instance.search = AsyncMock(return_value=mock_empty_results)

            result = await web_search("test query", provider="searxng")

            # Should return empty results without fallback
            assert result.provider == "searxng"
            assert len(result.results) == 0

    @pytest.mark.asyncio
    async def test_search_with_max_results(self, monkeypatch):
        """Test search with custom max_results."""
        monkeypatch.setenv("YDC_API_KEY", "test-you-key")

        with patch("search_engine_tool_mcp.search.YouProvider") as MockYou:
            you_instance = MockYou.return_value
            you_instance.search = AsyncMock(return_value=[])

            await web_search("test query", provider="you", max_results=10)

            you_instance.search.assert_called_once_with("test query", 10)
