"""搜索引擎工具 MCP 服务器实现"""

import logging
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .search import web_search as _web_search_impl
from .extract import web_extract as _web_extract_impl
from .schemas import WebSearchParams, WebExtractParams

# 从项目根目录加载 .env 文件
# 尝试多个位置查找 .env 文件
env_paths = [
    Path(__file__).parent.parent.parent / ".env",  # 项目根目录
    Path.cwd() / ".env",  # 当前工作目录
    Path.home() / ".env",  # 用户主目录
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        logging.info(f"从 {env_path} 加载环境变量")
        break

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("search-engine-tool-mcp")

# 创建 FastMCP 实例
mcp = FastMCP("search-engine-tool-mcp")


@mcp.tool()
async def web_search(
    query: str,
    provider: str = "auto",
    max_results: int = 5,
    search_depth: str = "basic",
    include_answer: bool = False,
) -> dict:
    """
    使用多个提供者（You.com/Tavily）搜索网络信息。

    参数:
        query: 搜索查询字符串
        provider: 使用的提供者：auto（默认）、you（需要 YDC_API_KEY）或 tavily（需要 TAVILY_API_KEY）
        max_results: 返回结果的最大数量（1-20）
        search_depth: 搜索深度（仅 Tavily）：basic 或 advanced
        include_answer: 包含 AI 生成的答案（仅 Tavily）

    返回:
        包含查询、提供者、计数和结果列表的搜索结果
    """
    params = WebSearchParams(
        query=query,
        provider=provider,
        max_results=max_results,
        search_depth=search_depth,
        include_answer=include_answer,
    )
    result = await _web_search_impl(
        query=params.query,
        provider=params.provider,
        max_results=params.max_results,
        search_depth=params.search_depth,
        include_answer=params.include_answer,
    )
    return result.model_dump()


@mcp.tool()
async def web_extract(url: str, provider: str = "auto") -> dict:
    """
    从指定 URL 提取内容。

    提供者选项：
    - local: 免费本地提取，无需 API Key
    - tavily: Tavily API 提取，需要 TAVILY_API_KEY
    - auto: 默认，优先使用 local，失败时自动回退到 Tavily（如果可用）

    参数:
        url: 要提取内容的 URL
        provider: 使用的提供者：auto（默认）、local 或 tavily（需要 TAVILY_API_KEY）

    返回:
        包含 url、content 和 provider 的提取结果
    """
    params = WebExtractParams(url=url, provider=provider)
    result = await _web_extract_impl(url=params.url, provider=params.provider)
    return result.model_dump()


def run():
    """命令行接口入口点"""
    logger.info("启动 MCP 服务器...")
    mcp.run()  # FastMCP 自动处理所有事情


if __name__ == "__main__":
    run()
