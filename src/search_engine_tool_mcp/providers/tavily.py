"""Tavily 搜索和提取提供者"""

from typing import List, Optional
import os
import httpx
from ..schemas import SearchResult, ExtractResult


class TavilyProvider:
    """Tavily 提供者实现（需要 TAVILY_API_KEY）"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Tavily 提供者。

        参数:
            api_key: Tavily API Key。如果未提供，从 TAVILY_API_KEY 环境变量读取。

        异常:
            ValueError: 如果未提供 API Key 且环境中未找到
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Tavily API key is required. Set TAVILY_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.base_url = "https://api.tavily.com"

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_answer: bool = False,
    ) -> List[SearchResult]:
        """
        使用 Tavily API 进行搜索。

        参数:
            query: 搜索查询字符串
            max_results: 返回结果的最大数量
            search_depth: 搜索深度（basic/advanced）
            include_answer: 是否包含 AI 生成的答案

        返回:
            SearchResult 对象列表
        """
        url = f"{self.base_url}/search"

        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": include_answer,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("results", []):
                    results.append(
                        SearchResult(
                            href=item.get("url", ""),
                            title=item.get("title", ""),
                            abstract=item.get("content", ""),
                        )
                    )
                return results
            except Exception as e:
                raise RuntimeError(f"Tavily search failed: {str(e)}")

    async def extract(self, url: str) -> ExtractResult:
        """
        使用 Tavily Extract API 从 URL 提取内容。

        参数:
            url: 要提取内容的 URL

        返回:
            ExtractResult 对象
        """
        extract_url = f"{self.base_url}/extract"

        payload = {"api_key": self.api_key, "urls": [url]}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(extract_url, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                if results and len(results) > 0:
                    content = results[0].get("raw_content", "")
                else:
                    content = ""

                return ExtractResult(url=url, content=content, provider="tavily")
            except Exception as e:
                raise RuntimeError(f"Tavily extraction failed: {str(e)}")
