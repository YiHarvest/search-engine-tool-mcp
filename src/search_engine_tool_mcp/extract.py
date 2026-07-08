"""Web content extraction functionality with provider routing."""

import os
import logging
from .schemas import ExtractResult
from .providers import TavilyProvider, LocalExtractProvider

logger = logging.getLogger("search-engine-tool-mcp")


async def web_extract(
    url: str,
    provider: str = "auto"
) -> ExtractResult:
    """
    Extract content from a URL with automatic provider selection.

    Supports multiple providers:
    - local: Free local extraction, no API key required (uses trafilatura + BeautifulSoup)
    - tavily: Tavily API extraction, requires TAVILY_API_KEY
    - auto: Default, tries local first, falls back to Tavily if available

    Args:
        url: URL to extract content from
        provider: Provider to use (auto/local/tavily)

    Returns:
        ExtractResult object with content

    Raises:
        ValueError: If invalid provider specified or missing required API key
        RuntimeError: If extraction fails
    """
    # Determine which provider to use
    actual_provider = _resolve_provider(provider)

    # Execute extraction based on provider
    if actual_provider == "local":
        # Try local extraction (no API key required)
        local_provider = LocalExtractProvider()
        try:
            result = await local_provider.extract(url)
            return result
        except ValueError as e:
            # URL validation errors should be raised directly
            logger.warning(f"URL validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.warning(f"Local extraction failed: {str(e)}")
            # If provider was explicitly "local", don't fallback
            if provider == "local":
                raise RuntimeError(f"Local extraction failed: {str(e)}")
            # If provider was "auto" and Tavily is available, try fallback
            if provider == "auto" and os.getenv("TAVILY_API_KEY"):
                logger.info("Falling back to Tavily extraction")
                tavily = TavilyProvider()
                return await tavily.extract(url)
            else:
                raise RuntimeError(f"Local extraction failed and no Tavily fallback available: {str(e)}")

    elif actual_provider == "tavily":
        # Tavily extraction (requires API key)
        tavily = TavilyProvider()  # Will raise ValueError if no API key
        return await tavily.extract(url)

    else:
        raise ValueError(
            f"Provider '{actual_provider}' does not support URL extraction. "
            "Available providers: 'local', 'tavily', 'auto'."
        )


def _resolve_provider(provider: str) -> str:
    """
    Resolve provider based on setting and environment.

    Provider options:
    - local: Free local extraction (no API key)
    - tavily: Tavily API (requires TAVILY_API_KEY)
    - auto: Default, prioritizes local, falls back to Tavily if available

    Args:
        provider: Provider string (auto/local/tavily)

    Returns:
        Resolved provider name (local/tavily)

    Raises:
        ValueError: If invalid provider specified or missing required API key
    """
    if provider == "local":
        # Local extraction is always available (no API key required)
        return "local"
    elif provider == "tavily":
        # Tavily requires API key - will be checked later in TavilyProvider
        return "tavily"
    elif provider == "auto":
        # Auto mode: prioritize local, can fallback to Tavily later
        return "local"
    else:
        raise ValueError(
            f"Invalid provider: {provider}. For web_extract, use 'auto', 'local', or 'tavily'."
        )