"""网络搜索功能，支持多提供者路由"""

import os
from typing import List, Optional
from .schemas import SearchResult, SearchResponse
from .providers import YouProvider, TavilyProvider, SearXNGProvider, TalorDataProvider


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
        provider: 使用的提供者（auto/talordata/searxng/you/tavily）
        max_results: 返回结果的最大数量
        search_depth: 搜索深度（basic/advanced）- 仅 Tavily
        include_answer: 包含 AI 生成的答案 - 仅 Tavily 和 TalorData

    返回:
        包含结果的 SearchResponse 对象

    异常:
        ValueError: 如果指定了无效的提供者
    """
    # 确定使用哪个提供者
    actual_provider = _resolve_provider(provider)

    # 根据提供者执行搜索
    results: List[SearchResult] = []
    answer: Optional[str] = None

    if actual_provider == "talordata":
        try:
            talordata = TalorDataProvider()
            results, answer = await talordata.search(query, max_results, include_answer)

            # 如果 talordata 返回空结果且 provider=auto，fallback 到其他 provider
            if provider == "auto" and len(results) == 0:
                fallback_provider = _get_fallback_provider("talordata")
                if fallback_provider:
                    results, answer = await _search_with_provider(
                        fallback_provider,
                        query,
                        max_results,
                        search_depth,
                        include_answer,
                    )
                    actual_provider = fallback_provider
        except Exception:
            # talordata 失败时，如果 provider=auto，fallback 到其他 provider
            if provider == "auto":
                fallback_provider = _get_fallback_provider("talordata")
                if fallback_provider:
                    results, answer = await _search_with_provider(
                        fallback_provider,
                        query,
                        max_results,
                        search_depth,
                        include_answer,
                    )
                    actual_provider = fallback_provider
                else:
                    raise ValueError(
                        "No search provider configured after TalorData failure"
                    )
            else:
                # provider=talordata 时直接抛出异常
                raise
    elif actual_provider == "searxng":
        try:
            searxng = SearXNGProvider()
            results = await searxng.search(query, max_results)

            # 如果 searxng 返回空结果且 provider=auto，fallback 到其他 provider
            if provider == "auto" and len(results) == 0:
                fallback_provider = _get_fallback_provider("searxng")
                if fallback_provider:
                    results, answer = await _search_with_provider(
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
                    results, answer = await _search_with_provider(
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
        results, answer = await _search_with_provider(
            actual_provider, query, max_results, search_depth, include_answer
        )
    else:
        raise ValueError(f"Unknown provider: {actual_provider}")

    return SearchResponse(
        query=query,
        provider=actual_provider,
        count=len(results),
        results=results,
        answer=answer,
    )


async def _search_with_provider(
    provider: str,
    query: str,
    max_results: int,
    search_depth: str = "basic",
    include_answer: bool = False,
) -> tuple[List[SearchResult], Optional[str]]:
    """使用指定 provider 执行搜索"""
    if provider == "you":
        you = YouProvider()
        results = await you.search(query, max_results)
        return results, None
    elif provider == "tavily":
        tavily = TavilyProvider()
        results = await tavily.search(query, max_results, search_depth, include_answer)
        answer = None
        # Tavily 可能包含 answer 字段，需要提取
        if include_answer:
            # Tavily 的 answer 在不同的字段中，需要根据实际返回结构调整
            # 这里假设 answer 在 results 的某个特殊字段中
            pass
        return results, answer
    elif provider == "talordata":
        talordata = TalorDataProvider()
        return await talordata.search(query, max_results, include_answer)
    else:
        raise ValueError(f"Unknown provider in fallback: {provider}")


def _get_fallback_provider(current: str) -> str:
    """获取 fallback provider"""
    fallback_order = {
        "searxng": ["talordata", "tavily", "you"],
        "talordata": ["tavily", "you"],
        "tavily": ["you"],
        "you": [],
    }

    if current in fallback_order:
        for fallback in fallback_order[current]:
            if fallback == "talordata" and os.getenv("TALORDATA_API_KEY"):
                return "talordata"
            elif fallback == "tavily" and os.getenv("TAVILY_API_KEY"):
                return "tavily"
            elif fallback == "you" and (os.getenv("YDC_API_KEY") or os.getenv("YOU_API_KEY")):
                return "you"
    return None


def _resolve_provider(provider: str) -> str:
    """
    根据设置和环境解析提供者。

    参数:
        provider: 提供者字符串（auto/talordata/searxng/you/tavily）

    返回:
        解析后的提供者名称（talordata/searxng/you/tavily）

    异常:
        ValueError: 如果指定了无效的提供者或没有可用的 API Key
    """
    if provider == "talordata":
        # 如果没有 TALORDATA_API_KEY，会在 TalorDataProvider 中失败
        return "talordata"
    elif provider == "searxng":
        # 如果没有 SEARXNG_BASE_URL，会在 SearXNGProvider 中失败
        return "searxng"
    elif provider == "you":
        # 如果没有 API Key，会在 YouProvider 中失败
        return "you"
    elif provider == "tavily":
        # 如果没有 API Key，会在 TavilyProvider 中失败
        return "tavily"
    elif provider == "auto":
        # 自动选择优先级：TalorData -> SearXNG -> You.com -> Tavily
        if os.getenv("TALORDATA_API_KEY"):
            return "talordata"
        elif os.getenv("SEARXNG_BASE_URL"):
            return "searxng"
        elif os.getenv("YDC_API_KEY") or os.getenv("YOU_API_KEY"):
            return "you"
        elif os.getenv("TAVILY_API_KEY"):
            return "tavily"
        else:
            raise ValueError(
                "No search provider configured. Set one of these environment variables: "
                "TALORDATA_API_KEY, SEARXNG_BASE_URL, YDC_API_KEY, YOU_API_KEY, or TAVILY_API_KEY."
            )
    else:
        raise ValueError(
            f"Invalid provider: {provider}. Must be 'auto', 'talordata', 'searxng', 'you', or 'tavily'"
        )