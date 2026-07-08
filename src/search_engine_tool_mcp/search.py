"""网络搜索功能，支持多提供者路由"""

import os
from typing import List
from .schemas import SearchResult, SearchResponse
from .providers import YouProvider, TavilyProvider, SearXNGProvider


async def web_search(
    query: str,
    provider: str = "auto",
    max_results: int = 5,
    search_depth: str = "basic",
    include_answer: bool = False,
) -> SearchResponse:
    """
    执行网络搜索，自动选择提供者。

    参数:
        query: 搜索查询字符串
        provider: 使用的提供者（auto/searxng/you/tavily）
        max_results: 返回结果的最大数量
        search_depth: 搜索深度（basic/advanced）- 仅 Tavily
        include_answer: 包含 AI 生成的答案 - 仅 Tavily

    返回:
        包含结果的 SearchResponse 对象

    异常:
        ValueError: 如果指定了无效的提供者
    """
    # 确定使用哪个提供者
    actual_provider = _resolve_provider(provider)

    # 根据提供者执行搜索
    results: List[SearchResult] = []

    if actual_provider == "searxng":
        try:
            searxng = SearXNGProvider()
            results = await searxng.search(query, max_results)

            # 如果 searxng 返回空结果且 provider=auto，fallback 到其他 provider
            if provider == "auto" and len(results) == 0:
                fallback_provider = _get_fallback_provider("searxng")
                if fallback_provider:
                    results = await _search_with_provider(
                        fallback_provider,
                        query,
                        max_results,
                        search_depth,
                        include_answer,
                    )
                    actual_provider = fallback_provider
        except Exception:
            # searxng 失败时，如果 provider=auto，fallback 到其他 provider
            if provider == "auto":
                fallback_provider = _get_fallback_provider("searxng")
                if fallback_provider:
                    results = await _search_with_provider(
                        fallback_provider,
                        query,
                        max_results,
                        search_depth,
                        include_answer,
                    )
                    actual_provider = fallback_provider
                else:
                    raise ValueError(
                        "No search provider configured after SearXNG failure"
                    )
            else:
                # provider=searxng 时直接抛出异常
                raise
    elif actual_provider in ["you", "tavily"]:
        results = await _search_with_provider(
            actual_provider, query, max_results, search_depth, include_answer
        )
    else:
        raise ValueError(f"Unknown provider: {actual_provider}")

    return SearchResponse(
        query=query, provider=actual_provider, count=len(results), results=results
    )


async def _search_with_provider(
    provider: str,
    query: str,
    max_results: int,
    search_depth: str = "basic",
    include_answer: bool = False,
) -> List[SearchResult]:
    """使用指定 provider 执行搜索"""
    if provider == "you":
        you = YouProvider()
        return await you.search(query, max_results)
    elif provider == "tavily":
        tavily = TavilyProvider()
        return await tavily.search(query, max_results, search_depth, include_answer)
    else:
        raise ValueError(f"Unknown provider in fallback: {provider}")


def _get_fallback_provider(current: str) -> str:
    """获取 fallback provider"""
    if current == "searxng":
        # searxng 失败时，优先 tavily，然后 you
        if os.getenv("TAVILY_API_KEY"):
            return "tavily"
        elif os.getenv("YDC_API_KEY") or os.getenv("YOU_API_KEY"):
            return "you"
    return None


def _resolve_provider(provider: str) -> str:
    """
    根据设置和环境解析提供者。

    参数:
        provider: 提供者字符串（auto/searxng/you/tavily）

    返回:
        解析后的提供者名称（searxng/you/tavily）

    异常:
        ValueError: 如果指定了无效的提供者或没有可用的 API Key
    """
    if provider == "searxng":
        # 如果没有 SEARXNG_BASE_URL，会在 SearXNGProvider 中失败
        return "searxng"
    elif provider == "you":
        # 如果没有 API Key，会在 YouProvider 中失败
        return "you"
    elif provider == "tavily":
        # 如果没有 API Key，会在 TavilyProvider 中失败
        return "tavily"
    elif provider == "auto":
        # 自动选择：优先 SearXNG，然后 Tavily，最后 You.com
        if os.getenv("SEARXNG_BASE_URL"):
            return "searxng"
        elif os.getenv("TAVILY_API_KEY"):
            return "tavily"
        elif os.getenv("YDC_API_KEY") or os.getenv("YOU_API_KEY"):
            return "you"
        else:
            raise ValueError(
                "No search provider configured. Set one of these environment variables: "
                "SEARXNG_BASE_URL, TAVILY_API_KEY, YDC_API_KEY, or YOU_API_KEY."
            )
    else:
        raise ValueError(
            f"Invalid provider: {provider}. Must be 'auto', 'searxng', 'you', or 'tavily'"
        )
