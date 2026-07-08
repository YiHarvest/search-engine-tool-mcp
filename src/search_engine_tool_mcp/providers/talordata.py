"""TalorData SERP API 搜索提供者"""

from typing import List, Optional, Tuple
import os
import httpx
from ..schemas import SearchResult


class TalorDataProvider:
    """TalorData SERP API 提供者实现（需要 TALORDATA_API_KEY）

    注意：TalorData 只用于 web_search，不用于 web_extract。
    网页正文提取请使用 web_extract(provider="local" 或 "tavily")。
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        初始化 TalorData 提供者。

        参数:
            api_key: TalorData API Token。如果未提供，从 TALORDATA_API_KEY 环境变量读取。
            base_url: TalorData API 基础 URL。如果未提供，从 TALORDATA_BASE_URL 环境变量读取，
                     默认为 https://serpapi.talordata.net/request

        异常:
            ValueError: 如果未提供 api_key 且环境中未找到
        """
        self.api_key = api_key or os.getenv("TALORDATA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "TalorData API key is required. Set TALORDATA_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.base_url = base_url or os.getenv(
            "TALORDATA_BASE_URL", "https://serpapi.talordata.net/request"
        )

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_answer: bool = False,
    ) -> Tuple[List[SearchResult], Optional[str]]:
        """
        使用 TalorData SERP API 进行搜索。

        参数:
            query: 搜索查询字符串
            max_results: 返回结果的最大数量
            search_depth: 搜索深度（basic/advanced）- TalorData 目前不支持此参数，保留以兼容接口
            include_answer: 是否包含 AI 生成的答案（从 ai_overview 提取）

        返回:
            Tuple[List[SearchResult], Optional[str]]: 搜索结果列表和可选的 AI 答案

        异常:
            ValueError: API 请求失败或状态不成功时抛出
            httpx.HTTPError: 网络请求失败时抛出
        """
        # TalorData 目前不支持 search_depth 参数，但保留接口兼容性
        # 根据文档，TalorData 使用 engine 参数而不是 url 参数
        params = {
            "engine": "google",  # 指定搜索引擎
            "q": query,
            "json": "1",
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # 设置超时时间不超过 15 秒
        timeout = 15.0

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self.base_url, data=params, headers=headers
                )
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException:
            raise ValueError(f"TalorData API request timeout after {timeout} seconds")
        except httpx.HTTPStatusError as e:
            raise ValueError(
                f"TalorData API request failed with status {e.response.status_code}"
            )
        except Exception as e:
            raise ValueError(f"TalorData API request failed: {str(e)}")

        # 检查状态
        if "search_metadata" in data:
            status = data["search_metadata"].get("status", "")
            if status != "Success":
                raise ValueError(f"TalorData API returned status: {status}")

        # 解析响应数据
        results: List[SearchResult] = []

        # 处理 organic 字段（可能为空）
        if "organic" in data and isinstance(data["organic"], list):
            for item in data["organic"][:max_results]:
                # 必需字段映射
                href = item.get("link", "")
                title = item.get("title", "")
                abstract = item.get("description") or item.get("snippet") or ""

                # 可选字段
                position = item.get("position")
                source = item.get("source")
                display_link = item.get("display_link")

                result = SearchResult(
                    href=href,
                    title=title,
                    abstract=abstract,
                    position=position,
                    source=source,
                    display_link=display_link,
                )
                results.append(result)

        # 处理 ai_overview（仅在 include_answer=True 时）
        answer: Optional[str] = None
        if include_answer and "ai_overview" in data:
            ai_overview = data["ai_overview"]
            if isinstance(ai_overview, dict) and "content" in ai_overview:
                answer = ai_overview.get("content")

        return results, answer
