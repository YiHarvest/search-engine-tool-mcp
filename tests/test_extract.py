"""Tests for web_extract functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from search_engine_tool_mcp.extract import web_extract, _resolve_provider
from search_engine_tool_mcp.schemas import ExtractResult


class TestResolveProvider:
    """Test provider resolution logic for extract."""

    def test_resolve_local(self):
        """Test explicit local provider."""
        result = _resolve_provider("local")
        assert result == "local"

    def test_resolve_tavily(self):
        """Test explicit tavily provider."""
        result = _resolve_provider("tavily")
        assert result == "tavily"

    def test_resolve_auto(self):
        """Test auto provider defaults to local."""
        result = _resolve_provider("auto")
        assert result == "local"

    def test_resolve_invalid_provider(self):
        """Test invalid provider raises error."""
        with pytest.raises(ValueError, match="Invalid provider"):
            _resolve_provider("invalid")

    def test_resolve_you_not_supported(self):
        """Test you provider raises error for extract."""
        with pytest.raises(ValueError, match="Invalid provider"):
            _resolve_provider("you")


class TestLocalExtractProvider:
    """Test LocalExtractProvider."""

    @pytest.mark.asyncio
    async def test_extract_simple_html(self):
        """Test provider='local' can extract simple HTML."""
        mock_html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <main>
                <h1>Hello World</h1>
                <p>This is test content.</p>
            </main>
        </body>
        </html>
        """

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = mock_html
            mock_response.raise_for_status = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            result = await web_extract("https://example.com", provider="local")

            assert isinstance(result, ExtractResult)
            assert result.url == "https://example.com"
            assert result.provider == "local"
            assert len(result.content) > 0
            # Content should contain the extracted text
            assert "Hello World" in result.content or "test content" in result.content

    @pytest.mark.asyncio
    async def test_extract_auto_uses_local(self):
        """Test provider='auto' defaults to local."""
        mock_html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <article>
                <p>This is auto test content.</p>
            </article>
        </body>
        </html>
        """

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = mock_html
            mock_response.raise_for_status = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            result = await web_extract("https://example.com", provider="auto")

            assert result.provider == "local"

    @pytest.mark.asyncio
    async def test_extract_non_http_url_raises(self):
        """Test non http/https URL raises error."""
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            await web_extract("file:///etc/passwd", provider="local")

        with pytest.raises(ValueError, match="Invalid URL scheme"):
            await web_extract("ftp://example.com/file", provider="local")

    @pytest.mark.asyncio
    async def test_extract_localhost_url_raises(self):
        """Test localhost URL raises error."""
        with pytest.raises(ValueError, match="Access to localhost"):
            await web_extract("http://localhost/test", provider="local")

        with pytest.raises(ValueError, match="Access to localhost"):
            await web_extract("http://127.0.0.1/test", provider="local")

    @pytest.mark.asyncio
    async def test_extract_private_ip_raises(self):
        """Test private/internal IP addresses raise error."""
        # 192.168.x.x
        with pytest.raises(ValueError, match="Access to internal networks"):
            await web_extract("http://192.168.1.1/test", provider="local")

        # 10.x.x.x
        with pytest.raises(ValueError, match="Access to internal networks"):
            await web_extract("http://10.0.0.1/test", provider="local")

        # 172.16-31.x.x
        with pytest.raises(ValueError, match="Access to internal networks"):
            await web_extract("http://172.16.0.1/test", provider="local")

    @pytest.mark.asyncio
    async def test_extract_timeout_error(self):
        """Test timeout raises RuntimeError."""
        import httpx

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            MockClient.return_value = mock_client

            with pytest.raises(RuntimeError, match="timed out"):
                await web_extract("https://example.com", provider="local")


class TestTavilyExtract:
    """Test Tavily provider for extract."""

    @pytest.mark.asyncio
    async def test_extract_tavily_without_api_key_raises(self, monkeypatch):
        """Test provider='tavily' without TAVILY_API_KEY raises error."""
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        with pytest.raises(ValueError, match="Tavily API key is required"):
            await web_extract("https://example.com", provider="tavily")

    @pytest.mark.asyncio
    async def test_extract_tavily_success(self, monkeypatch):
        """Test successful Tavily extraction."""
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")

        mock_response_data = {
            "results": [
                {
                    "raw_content": "Tavily extracted content"
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

            result = await web_extract("https://example.com", provider="tavily")

            assert result.provider == "tavily"
            assert result.content == "Tavily extracted content"


class TestAutoFallback:
    """Test auto provider fallback logic."""

    @pytest.mark.asyncio
    async def test_auto_fallback_to_tavily(self, monkeypatch):
        """Test auto provider falls back to Tavily when local fails."""
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")

        # Mock local extraction to fail
        with patch("search_engine_tool_mcp.extract.LocalExtractProvider") as MockLocal:
            local_instance = MockLocal.return_value
            local_instance.extract = AsyncMock(side_effect=RuntimeError("Local extraction failed"))

            # Mock Tavily extraction to succeed
            mock_response_data = {
                "results": [
                    {
                        "raw_content": "Tavily fallback content"
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

                result = await web_extract("https://example.com", provider="auto")

                assert result.provider == "tavily"

    @pytest.mark.asyncio
    async def test_auto_fails_without_tavily_key(self, monkeypatch):
        """Test auto provider fails when local fails and no Tavily key."""
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        # Mock local extraction to fail
        with patch("search_engine_tool_mcp.extract.LocalExtractProvider") as MockLocal:
            local_instance = MockLocal.return_value
            local_instance.extract = AsyncMock(side_effect=RuntimeError("Local extraction failed"))

            with pytest.raises(RuntimeError, match="no Tavily fallback available"):
                await web_extract("https://example.com", provider="auto")