"""You.com 搜索提供者"""

import os
from typing import List, Optional
import httpx
from ..schemas import SearchResult, ExtractResult


class YouProvider:
    """You.com 提供者实现（需要 YDC_API_KEY）"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 You.com 提供者。

        参数:
            api_key: You.com API Key。如果未提供，从 YDC_API_KEY 环境变量读取。

        异常:
            ValueError: 如果未提供 API Key 且环境中未找到
        """
        self.api_key = api_key or os.getenv("YDC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "YDC_API_KEY is required for You.com provider. "
                "Set YDC_API_KEY environment variable or pass api_key parameter. "
                "Get your API key at https://you.com/platform"
            )

        self.search_url = "https://ydc-index.io/v1/search"
        self.headers = {
            "X-API-Key": self.api_key,
            "User-Agent": "SearchEngineToolMCP/0.2.0",
        }

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        使用 You.com Search API 进行搜索。

        参数:
            query: 搜索查询字符串
            max_results: 返回结果的最大数量

        返回:
            SearchResult 对象列表
        """
        params = {"query": query, "count": max_results}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.search_url, params=params, headers=self.headers, timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                results = []
                # 解析 You.com API 响应
                web_results = data.get("results", {}).get("web", [])

                for item in web_results[:max_results]:
                    # 将描述和片段组合成摘要
                    description = item.get("description", "")
                    snippets = item.get("snippets", [])
                    abstract = description or (snippets[0] if snippets else "")

                    results.append(
                        SearchResult(
                            href=item.get("url", ""),
                            title=item.get("title", ""),
                            abstract=abstract,
                        )
                    )

                return results
            except Exception as e:
                raise RuntimeError(f"You.com search failed: {str(e)}")

    async def extract(self, url: str) -> ExtractResult:
        """
        使用 You.com Contents API 从 URL 提取内容。

        注意：You.com 没有像 Jina 的 r.jina.ai 这样的直接提取端点，
        但我们可以使用带有 livecrawl 参数的搜索 API 进行基本提取。
        对于完整提取，推荐使用 Jina Reader 或 Tavily。

        参数:
            url: 要提取内容的 URL

        返回:
            ExtractResult 对象
        """
        # You.com 不提供独立的提取端点
        # 我们推荐使用 Jina Reader 或 Tavily 进行提取
        raise NotImplementedError(
            "You.com provider does not support URL extraction. "
            "Please use Jina (r.jina.ai) or Tavily for content extraction, "
            "or switch provider to 'auto', 'jina', or 'tavily' for web_extract tool."
        )
