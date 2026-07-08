"""搜索引擎工具的数据模型"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """单个搜索结果项"""

    href: str = Field(..., description="搜索结果的 URL")
    title: str = Field(..., description="搜索结果的标题")
    abstract: str = Field(default="", description="搜索结果的摘要或简介")
    position: Optional[int] = Field(default=None, description="搜索结果的位置")
    source: Optional[str] = Field(default=None, description="搜索结果的来源")
    display_link: Optional[str] = Field(default=None, description="显示的链接")


class SearchResponse(BaseModel):
    """搜索 API 响应"""

    query: str = Field(..., description="原始搜索查询")
    provider: str = Field(
        ..., description="使用的提供者（talordata/searxng/you/tavily）"
    )
    count: int = Field(..., description="返回结果的数量")
    results: List[SearchResult] = Field(default_factory=list, description="搜索结果")
    answer: Optional[str] = Field(
        default=None, description="AI 生成的答案（仅当 include_answer=True 时）"
    )


class ExtractResult(BaseModel):
    """单个提取结果"""

    url: str = Field(..., description="提取内容的 URL")
    content: str = Field(..., description="提取的内容")
    provider: str = Field(..., description="使用的提供者（local/tavily）")


class WebSearchParams(BaseModel):
    """web_search 工具的参数"""

    query: str = Field(..., description="搜索查询字符串")
    provider: str = Field(
        default="auto", description="提供者: auto/talordata/searxng/you/tavily"
    )
    max_results: int = Field(default=5, ge=1, le=20, description="最大结果数量")
    search_depth: str = Field(default="basic", description="搜索深度: basic/advanced")
    include_answer: bool = Field(default=False, description="包含 AI 生成的答案")


class WebExtractParams(BaseModel):
    """web_extract 工具的参数"""

    url: str = Field(..., description="要提取内容的 URL")
    provider: str = Field(default="auto", description="提供者: auto/local/tavily")
