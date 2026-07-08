"""TalorData 提供者测试"""

import pytest
import os
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from search_engine_tool_mcp.providers.talordata import TalorDataProvider
from search_engine_tool_mcp.schemas import SearchResult


@pytest.mark.asyncio
async def test_talordata_organic_field_mapping():
    """测试 organic 字段映射"""
    mock_response_data = {
        "code": 0,
        "data": {
            "search_metadata": {"status": "Success"},
            "organic": [
                {
                    "link": "https://example.com/1",
                    "title": "Example 1",
                    "description": "Description 1",
                    "position": 1,
                    "source": "Example Source",
                    "display_link": "example.com",
                },
                {
                    "link": "https://example.com/2",
                    "title": "Example 2",
                    "snippet": "Snippet 2",
                    "position": 2,
                },
            ],
        },
    }

    provider = TalorDataProvider(api_key="test_key")

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        results, answer = await provider.search("test query", max_results=2, search_depth="basic")

        assert len(results) == 2
        assert results[0].href == "https://example.com/1"
        assert results[0].title == "Example 1"
        assert results[0].abstract == "Description 1"
        assert results[0].position == 1
        assert results[0].source == "Example Source"
        assert results[0].display_link == "example.com"

        assert results[1].href == "https://example.com/2"
        assert results[1].title == "Example 2"
        assert results[1].abstract == "Snippet 2"
        assert results[1].position == 2


@pytest.mark.asyncio
async def test_talordata_ai_overview_mapping():
    """测试 ai_overview 映射到 answer"""
    mock_response_data = {
        "code": 0,
        "data": {
            "search_metadata": {"status": "Success"},
            "organic": [
                {
                    "link": "https://example.com",
                    "title": "Example",
                    "description": "Description",
                }
            ],
            "ai_overview": {
                "content": "AI generated answer for the query"
            },
        },
    }

    provider = TalorDataProvider(api_key="test_key")

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        results, answer = await provider.search("test query", search_depth="basic", include_answer=True)

        assert answer == "AI generated answer for the query"


@pytest.mark.asyncio
async def test_talordata_missing_api_key():
    """测试 TALORDATA_API_KEY 缺失时报错"""
    # 清除环境变量
    if "TALORDATA_API_KEY" in os.environ:
        del os.environ["TALORDATA_API_KEY"]

    with pytest.raises(ValueError) as exc_info:
        TalorDataProvider()

    assert "TalorData API key is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_talordata_empty_organic():
    """测试 organic 为空时返回空列表"""
    mock_response_data = {
        "code": 0,
        "data": {
            "search_metadata": {"status": "Success"},
            "organic": [],
        },
    }

    provider = TalorDataProvider(api_key="test_key")

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        results, answer = await provider.search("test query", search_depth="basic")

        assert len(results) == 0
        assert answer is None


@pytest.mark.asyncio
async def test_talordata_status_not_success():
    """测试 status 不是 Success 时返回明确错误"""
    mock_response_data = {
        "code": 0,
        "data": {
            "search_metadata": {"status": "Error"},
            "organic": [],
        },
    }

    provider = TalorDataProvider(api_key="test_key")

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        with pytest.raises(ValueError) as exc_info:
            await provider.search("test query", search_depth="basic")

        assert "TalorData API returned status: Error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_auto_priority_with_talordata():
    """测试 auto 优先级：TalorData -> SearXNG -> You -> Tavily"""
    from search_engine_tool_mcp.search import _resolve_provider

    # 测试 1: 只有 TALORDATA_API_KEY
    os.environ["TALORDATA_API_KEY"] = "test_key"
    if "SEARXNG_BASE_URL" in os.environ:
        del os.environ["SEARXNG_BASE_URL"]
    if "TAVILY_API_KEY" in os.environ:
        del os.environ["TAVILY_API_KEY"]
    if "YDC_API_KEY" in os.environ:
        del os.environ["YDC_API_KEY"]

    provider = _resolve_provider("auto")
    assert provider == "talordata"

    # 清理环境变量
    if "TALORDATA_API_KEY" in os.environ:
        del os.environ["TALORDATA_API_KEY"]


@pytest.mark.asyncio
async def test_talordata_with_base_url_override():
    """测试自定义 base_url"""
    custom_url = "https://custom.talordata.net/api"
    provider = TalorDataProvider(api_key="test_key", base_url=custom_url)

    assert provider.base_url == custom_url


@pytest.mark.asyncio
async def test_talordata_description_fallback_to_snippet():
    """测试 description 缺失时使用 snippet"""
    mock_response_data = {
        "code": 0,
        "data": {
            "search_metadata": {"status": "Success"},
            "organic": [
                {
                    "link": "https://example.com",
                    "title": "Example",
                    "snippet": "Snippet text",
                }
            ],
        },
    }

    provider = TalorDataProvider(api_key="test_key")

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        results, answer = await provider.search("test query", search_depth="basic")

        assert results[0].abstract == "Snippet text"


@pytest.mark.asyncio
async def test_talordata_no_answer_when_include_answer_false():
    """测试 include_answer=False 时不提取 ai_overview"""
    mock_response_data = {
        "code": 0,
        "data": {
            "search_metadata": {"status": "Success"},
            "organic": [
                {
                    "link": "https://example.com",
                    "title": "Example",
                    "description": "Description",
                }
            ],
            "ai_overview": {
                "content": "AI answer"
            },
        },
    }

    provider = TalorDataProvider(api_key="test_key")

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        results, answer = await provider.search("test query", search_depth="basic", include_answer=False)

        assert answer is None