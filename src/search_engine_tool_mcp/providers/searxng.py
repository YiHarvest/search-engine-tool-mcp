"""SearXNG 搜索提供者（自托管，无需 API Key）"""

from typing import List, Optional
import os
import httpx
from ..schemas import SearchResult


class SearXNGProvider:
    """SearXNG 提供者实现（需要 SEARXNG_BASE_URL）"""

    def __init__(self, base_url: Optional[str] = None):
        """
        初始化 SearXNG 提供者。

        参数:
            base_url: SearXNG 实例的 URL。如果未提供，从 SEARXNG_BASE_URL 环境变量读取。

        异常:
            ValueError: 如果未提供 base_url 且环境中未找到
        """
        self.base_url = base_url or os.getenv("SEARXNG_BASE_URL")
        if not self.base_url:
            raise ValueError(
                "SearXNG base URL is required. Set SEARXNG_BASE_URL environment variable "
                "or pass base_url parameter. Example: http://127.0.0.1:8080"
            )
        # 移除末尾斜杠
        self.base_url = self.base_url.rstrip("/")

    async def search(
        self, query: str, max_results: int = 5, engines: Optional[str] = None
    ) -> List[SearchResult]:
        """
        使用 SearXNG API 进行搜索。

        参数:
            query: 搜索查询字符串
            max_results: 返回结果的最大数量
            engines: 可选的搜索引擎列表（例如："google,bing"）

        返回:
            SearchResult 对象列表
        """
        url = f"{self.base_url}/search"

        params = {"q": query, "format": "json"}

        if engines:
            params["engines"] = engines

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=15.0)
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("results", [])[:max_results]:
                    results.append(
                        SearchResult(
                            href=item.get("url", ""),
                            title=item.get("title", ""),
                            abstract=item.get("content", ""),
                        )
                    )
                return results
            except httpx.TimeoutException:
                raise RuntimeError(
                    f"SearXNG search timeout after 15 seconds: {self.base_url}"
                )
            except Exception as e:
                raise RuntimeError(f"SearXNG search failed: {str(e)}")
