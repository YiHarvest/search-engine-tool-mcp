"""网络搜索功能，支持多提供者路由"""

import os
from typing import List
from .schemas import SearchResult, SearchResponse
from .providers import YouProvider, TavilyProvider


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
        provider: 使用的提供者（auto/you/tavily）
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

    if actual_provider == "you":
        you = YouProvider()
        results = await you.search(query, max_results)
    elif actual_provider == "tavily":
        tavily = TavilyProvider()  # 如果没有 API Key 会抛出 ValueError
        results = await tavily.search(query, max_results, search_depth, include_answer)
    else:
        raise ValueError(f"Unknown provider: {actual_provider}")

    return SearchResponse(
        query=query, provider=actual_provider, count=len(results), results=results
    )


def _resolve_provider(provider: str) -> str:
    """
    根据设置和环境解析提供者。

    参数:
        provider: 提供者字符串（auto/you/tavily）

    返回:
        解析后的提供者名称（you/tavily）

    异常:
        ValueError: 如果指定了无效的提供者或没有可用的 API Key
    """
    if provider == "you":
        # 如果没有 API Key，会在 YouProvider 中失败
        return "you"
    elif provider == "tavily":
        # 如果没有 API Key，会在 TavilyProvider 中失败
        return "tavily"
    elif provider == "auto":
        # 自动选择：优先使用 You.com，然后是 Tavily
        if os.getenv("YDC_API_KEY"):
            return "you"
        elif os.getenv("TAVILY_API_KEY"):
            return "tavily"
        else:
            raise ValueError(
                "Either YDC_API_KEY or TAVILY_API_KEY is required. "
                "Set one of these environment variables to use the search functionality."
            )
    else:
        raise ValueError(
            f"Invalid provider: {provider}. Must be 'auto', 'you', or 'tavily'"
        )
