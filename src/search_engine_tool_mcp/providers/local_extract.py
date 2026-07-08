"""本地网页内容提取提供者（免费，无需 API Key）"""

import re
import ipaddress
from urllib.parse import urlparse
from typing import Optional
import httpx
import trafilatura
from bs4 import BeautifulSoup
from ..schemas import ExtractResult


class LocalExtractProvider:
    """本地内容提取提供者（无需 API Key）"""

    def __init__(self, timeout: float = 20.0, user_agent: Optional[str] = None):
        """
        初始化本地提取提供者。

        参数:
            timeout: 请求超时时间（秒），默认：20
            user_agent: 自定义 User Agent 字符串（默认：合理的浏览器 UA）
        """
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    def _validate_url(self, url: str) -> None:
        """
        验证 URL 安全性（防止 SSRF 攻击）。

        参数:
            url: 要验证的 URL

        异常:
            ValueError: 如果 URL 无效或存在安全风险
        """
        parsed = urlparse(url)

        # 只允许 http 和 https
        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                f"Invalid URL scheme: {parsed.scheme}. Only http:// and https:// are allowed."
            )

        # 检查 localhost 和回环地址
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("URL must contain a valid hostname")

        # 阻止 localhost 变体
        if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            raise ValueError("Access to localhost is not allowed for security reasons.")

        # 阻止私有/内网 IP 地址
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                raise ValueError(
                    "Access to private/internal IP addresses is not allowed for security reasons."
                )
        except ValueError:
            # 不是 IP 地址，可能是域名
            pass

        # 阻止常见的内网域名模式
        blocked_patterns = [
            r"\.local$",
            r"\.internal$",
            r"\.localhost$",
            r"\.localdomain$",
            r"^localhost\.",
            r"^192\.168\.",
            r"^10\.",
            r"^172\.(1[6-9]|2[0-9]|3[0-1])\.",
            r"^127\.",
            r"^0\.0\.0\.0",
        ]

        for pattern in blocked_patterns:
            if re.search(pattern, hostname, re.IGNORECASE):
                raise ValueError(
                    f"Access to internal networks is not allowed: {hostname}"
                )

    async def extract(self, url: str) -> ExtractResult:
        """
        使用本地提取从 URL 提取内容。

        参数:
            url: 要提取内容的 URL

        返回:
            包含提取内容的 ExtractResult

        异常:
            ValueError: 如果 URL 无效或不允许访问
            RuntimeError: 如果提取失败
        """
        # 先验证 URL
        self._validate_url(url)

        # 下载页面
        headers = {"User-Agent": self.user_agent}

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                html = response.text
        except httpx.TimeoutException:
            raise RuntimeError(f"Request timed out after {self.timeout} seconds")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP error: {e.response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch URL: {str(e)}")

        # 使用 trafilatura 提取内容
        content = self._extract_content(html)

        if not content or not content.strip():
            raise RuntimeError("Failed to extract any content from the page")

        return ExtractResult(url=url, content=content.strip(), provider="local")

    def _extract_content(self, html: str) -> str:
        """
        使用 trafilatura 和 BeautifulSoup 回退从 HTML 提取内容。

        参数:
            html: 原始 HTML 内容

        返回:
            提取的文本内容
        """
        # 先尝试 trafilatura（质量更好的提取）
        content = trafilatura.extract(
            html,
            output_format="txt",
            include_links=False,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )

        if content and content.strip():
            return content.strip()

        # 如果 trafilatura 失败，回退到 BeautifulSoup
        return self._extract_with_beautifulsoup(html)

    def _extract_with_beautifulsoup(self, html: str) -> str:
        """
        使用 BeautifulSoup 进行回退提取。

        参数:
            html: 原始 HTML 内容

        返回:
            提取的文本内容
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # 移除不需要的元素
            for element in soup(
                ["script", "style", "nav", "footer", "header", "aside"]
            ):
                element.decompose()

            # 尝试找到主要内容
            main_content = (
                soup.find("main")
                or soup.find("article")
                or soup.find("div", class_=re.compile(r"content|main|article", re.I))
                or soup.find("body")
            )

            if main_content:
                text = main_content.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)

            # 清理空白字符
            lines = (line.strip() for line in text.splitlines())
            lines = [line for line in lines if line]
            return "\n".join(lines)

        except Exception as e:
            raise RuntimeError(f"BeautifulSoup extraction failed: {str(e)}")
