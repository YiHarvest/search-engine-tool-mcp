"""网页内容提取功能，支持多提供者路由"""

import os
import logging
from .schemas import ExtractResult
from .providers import TavilyProvider, LocalExtractProvider

logger = logging.getLogger("search-engine-tool-mcp")


async def web_extract(url: str, provider: str = "auto") -> ExtractResult:
    """
    从 URL 提取内容，自动选择提供者。

    支持多个提供者：
    - local: 免费本地提取，无需 API Key（使用 trafilatura + BeautifulSoup）
    - tavily: Tavily API 提取，需要 TAVILY_API_KEY
    - auto: 默认，优先使用 local，失败时自动回退到 Tavily（如果可用）

    参数:
        url: 要提取内容的 URL
        provider: 使用的提供者（auto/local/tavily）

    返回:
        包含内容的 ExtractResult 对象

    异常:
        ValueError: 如果指定了无效的提供者或缺少必需的 API Key
        RuntimeError: 如果提取失败
    """
    # 确定使用哪个提供者
    actual_provider = _resolve_provider(provider)

    # 根据提供者执行提取
    if actual_provider == "local":
        # 尝试本地提取（无需 API Key）
        local_provider = LocalExtractProvider()
        try:
            result = await local_provider.extract(url)
            return result
        except ValueError as e:
            # URL 验证错误应该直接抛出
            logger.warning(f"URL validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.warning(f"Local extraction failed: {str(e)}")
            # 如果提供者明确指定为 "local"，不进行回退
            if provider == "local":
                raise RuntimeError(f"Local extraction failed: {str(e)}")
            # 如果提供者是 "auto" 且 Tavily 可用，尝试回退
            if provider == "auto" and os.getenv("TAVILY_API_KEY"):
                logger.info("Falling back to Tavily extraction")
                tavily = TavilyProvider()
                return await tavily.extract(url)
            else:
                raise RuntimeError(
                    f"Local extraction failed and no Tavily fallback available: {str(e)}"
                )

    elif actual_provider == "tavily":
        # Tavily 提取（需要 API Key）
        tavily = TavilyProvider()  # 如果没有 API Key 会抛出 ValueError
        return await tavily.extract(url)

    else:
        raise ValueError(
            f"Provider '{actual_provider}' does not support URL extraction. "
            "Available providers: 'local', 'tavily', 'auto'."
        )


def _resolve_provider(provider: str) -> str:
    """
    根据设置和环境解析提供者。

    提供者选项：
    - local: 免费本地提取（无需 API Key）
    - tavily: Tavily API（需要 TAVILY_API_KEY）
    - auto: 默认，优先使用 local，如果可用可以回退到 Tavily

    参数:
        provider: 提供者字符串（auto/local/tavily）

    返回:
        解析后的提供者名称（local/tavily）

    异常:
        ValueError: 如果指定了无效的提供者或缺少必需的 API Key
    """
    if provider == "local":
        # 本地提取始终可用（无需 API Key）
        return "local"
    elif provider == "tavily":
        # Tavily 需要 API Key - 将在 TavilyProvider 中检查
        return "tavily"
    elif provider == "auto":
        # 自动模式：优先使用 local，稍后可以回退到 Tavily
        return "local"
    else:
        raise ValueError(
            f"Invalid provider: {provider}. For web_extract, use 'auto', 'local', or 'tavily'."
        )
