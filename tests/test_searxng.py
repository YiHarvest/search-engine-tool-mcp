"""Tests for SearXNG provider."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from search_engine_tool_mcp.providers.searxng import SearXNGProvider
from search_engine_tool_mcp.schemas import SearchResult


class TestSearXNGProvider:
    """Test SearXNG provider."""

    def test_init_with_base_url(self):
        """Test SearXNG provider initialization with explicit base URL."""
        provider = SearXNGProvider(base_url="http://127.0.0.1:8080")
        assert provider.base_url == "http://127.0.0.1:8080"

    def test_init_with_env_var(self, monkeypatch):
        """Test SearXNG provider initialization from environment."""
        monkeypatch.setenv("SEARXNG_BASE_URL", "http://localhost:8888")
        provider = SearXNGProvider()
        assert provider.base_url == "http://localhost:8888"

    def test_init_without_base_url_raises(self, monkeypatch):
        """Test SearXNG provider raises error without base URL."""
        monkeypatch.delenv("SEARXNG_BASE_URL", raising=False)

        with pytest.raises(ValueError, match="SearXNG base URL is required"):
            SearXNGProvider()

    def test_base_url_strip_slash(self):
        """Test base URL trailing slash is removed."""
        provider = SearXNGProvider(base_url="http://127.0.0.1:8080/")
        assert provider.base_url == "http://127.0.0.1:8080"

    @pytest.mark.asyncio
    async def test_search_success(self, monkeypatch):
        """Test successful SearXNG search."""
        monkeypatch.setenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")
        provider = SearXNGProvider()

        mock_response_data = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Example Title",
                    "content": "Example content",
                },
                {
                    "url": "https://example2.com",
                    "title": "Example Title 2",
                    "content": "Example content 2",
                },
            ]
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            results = await provider.search("test query", max_results=5)

            assert len(results) == 2
            assert isinstance(results[0], SearchResult)
            assert results[0].href == "https://example.com"
            assert results[0].title == "Example Title"
            assert results[0].abstract == "Example content"

    @pytest.mark.asyncio
    async def test_search_with_engines(self, monkeypatch):
        """Test SearXNG search with custom engines."""
        monkeypatch.setenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")
        provider = SearXNGProvider()

        mock_response_data = {"results": []}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            await provider.search("test query", engines="bing")

            # Verify engines parameter was passed
            call_args = mock_client.get.call_args
            assert "engines" in call_args[1]["params"]
            assert call_args[1]["params"]["engines"] == "bing"

    @pytest.mark.asyncio
    async def test_search_empty_content(self, monkeypatch):
        """Test SearXNG search with missing content field."""
        monkeypatch.setenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")
        provider = SearXNGProvider()

        mock_response_data = {
            "results": [{"url": "https://example.com", "title": "Example Title"}]
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            results = await provider.search("test query")

            assert len(results) == 1
            assert results[0].abstract == ""

    @pytest.mark.asyncio
    async def test_search_timeout_raises(self, monkeypatch):
        """Test SearXNG search timeout raises RuntimeError."""
        monkeypatch.setenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")
        provider = SearXNGProvider()

        import httpx

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            MockClient.return_value = mock_client

            with pytest.raises(RuntimeError, match="SearXNG search timeout"):
                await provider.search("test query")

    @pytest.mark.asyncio
    async def test_search_error_raises(self, monkeypatch):
        """Test SearXNG search error raises RuntimeError."""
        monkeypatch.setenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080")
        provider = SearXNGProvider()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=Exception("Network error"))
            MockClient.return_value = mock_client

            with pytest.raises(RuntimeError, match="SearXNG search failed"):
                await provider.search("test query")
