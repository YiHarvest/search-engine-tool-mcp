"""Tests for provider implementations."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from search_engine_tool_mcp.providers.you import YouProvider
from search_engine_tool_mcp.providers.tavily import TavilyProvider
from search_engine_tool_mcp.schemas import SearchResult, ExtractResult


class TestYouProvider:
    """Test You.com provider."""

    def test_init_with_api_key(self):
        """Test You.com provider initialization with explicit API key."""
        provider = YouProvider(api_key="test-api-key")
        assert provider.api_key == "test-api-key"
        assert provider.search_url == "https://ydc-index.io/v1/search"
        assert "X-API-Key" in provider.headers

    def test_init_with_env_var(self, monkeypatch):
        """Test You.com provider initialization from environment."""
        monkeypatch.setenv("YDC_API_KEY", "env-test-key")
        provider = YouProvider()
        assert provider.api_key == "env-test-key"

    def test_init_without_api_key_raises(self, monkeypatch):
        """Test You.com provider raises error without API key."""
        monkeypatch.delenv("YDC_API_KEY", raising=False)

        with pytest.raises(ValueError, match="YDC_API_KEY is required"):
            YouProvider()

    @pytest.mark.asyncio
    async def test_search_success(self, monkeypatch):
        """Test successful search."""
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        provider = YouProvider()

        mock_response_data = {
            "results": {
                "web": [
                    {
                        "url": "https://example.com",
                        "title": "Example Title",
                        "description": "Example description",
                    }
                ]
            }
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

            assert len(results) == 1
            assert isinstance(results[0], SearchResult)
            assert results[0].href == "https://example.com"
            assert results[0].title == "Example Title"
            assert results[0].abstract == "Example description"

    @pytest.mark.asyncio
    async def test_search_error_raises(self, monkeypatch):
        """Test search error raises RuntimeError."""
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        provider = YouProvider()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=Exception("Network error"))
            MockClient.return_value = mock_client

            with pytest.raises(RuntimeError, match="You.com search failed"):
                await provider.search("test query")

    @pytest.mark.asyncio
    async def test_extract_not_implemented(self, monkeypatch):
        """Test You.com extraction raises NotImplementedError."""
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        provider = YouProvider()

        with pytest.raises(
            NotImplementedError, match="does not support URL extraction"
        ):
            await provider.extract("https://example.com")


class TestTavilyProvider:
    """Test Tavily provider."""

    def test_init_with_api_key(self):
        """Test Tavily provider initialization with explicit API key."""
        provider = TavilyProvider(api_key="test-key")
        assert provider.api_key == "test-key"

    def test_init_with_env_var(self, monkeypatch):
        """Test Tavily provider initialization from environment."""
        monkeypatch.setenv("TAVILY_API_KEY", "env-test-key")
        provider = TavilyProvider()
        assert provider.api_key == "env-test-key"

    def test_init_without_api_key_raises(self, monkeypatch):
        """Test Tavily provider raises error without API key."""
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        with pytest.raises(ValueError, match="Tavily API key is required"):
            TavilyProvider()

    @pytest.mark.asyncio
    async def test_search_success(self, monkeypatch):
        """Test successful Tavily search."""
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        provider = TavilyProvider()

        mock_response_data = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Example Title",
                    "content": "Example content",
                }
            ]
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            results = await provider.search("test query", max_results=5)

            assert len(results) == 1
            assert isinstance(results[0], SearchResult)
            assert results[0].href == "https://example.com"

    @pytest.mark.asyncio
    async def test_extract_success(self, monkeypatch):
        """Test successful Tavily extraction."""
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        provider = TavilyProvider()

        mock_response_data = {"results": [{"raw_content": "Extracted content here"}]}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            result = await provider.extract("https://example.com")

            assert isinstance(result, ExtractResult)
            assert result.url == "https://example.com"
            assert result.content == "Extracted content here"
            assert result.provider == "tavily"

    @pytest.mark.asyncio
    async def test_search_error_raises(self, monkeypatch):
        """Test Tavily search error raises RuntimeError."""
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        provider = TavilyProvider()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=Exception("API error"))
            MockClient.return_value = mock_client

            with pytest.raises(RuntimeError, match="Tavily search failed"):
                await provider.search("test query")
