"""Local provider for web content extraction (free, no API key required)."""

import re
import ipaddress
from urllib.parse import urlparse
from typing import Optional
import httpx
import trafilatura
from bs4 import BeautifulSoup
from ..schemas import ExtractResult


class LocalExtractProvider:
    """Local provider for content extraction (no API key required)."""

    def __init__(self, timeout: float = 20.0, user_agent: Optional[str] = None):
        """
        Initialize local extract provider.

        Args:
            timeout: Request timeout in seconds (default: 20)
            user_agent: Custom user agent string (default: reasonable browser UA)
        """
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    def _validate_url(self, url: str) -> None:
        """
        Validate URL for security (prevent SSRF attacks).

        Args:
            url: URL to validate

        Raises:
            ValueError: If URL is invalid or potentially dangerous
        """
        parsed = urlparse(url)

        # Only allow http and https
        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                f"Invalid URL scheme: {parsed.scheme}. Only http:// and https:// are allowed."
            )

        # Check for localhost and loopback
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("URL must contain a valid hostname")

        # Block localhost variants
        if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            raise ValueError(
                "Access to localhost is not allowed for security reasons."
            )

        # Block private/internal IP addresses
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                raise ValueError(
                    "Access to private/internal IP addresses is not allowed for security reasons."
                )
        except ValueError:
            # Not an IP address, could be a domain name
            pass

        # Block common internal domain patterns
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
        Extract content from a URL using local extraction.

        Args:
            url: URL to extract content from

        Returns:
            ExtractResult with extracted content

        Raises:
            ValueError: If URL is invalid or not allowed
            RuntimeError: If extraction fails
        """
        # Validate URL first
        self._validate_url(url)

        # Download the page
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

        # Extract content using trafilatura
        content = self._extract_content(html)

        if not content or not content.strip():
            raise RuntimeError("Failed to extract any content from the page")

        return ExtractResult(
            url=url,
            content=content.strip(),
            provider="local"
        )

    def _extract_content(self, html: str) -> str:
        """
        Extract content from HTML using trafilatura with BeautifulSoup fallback.

        Args:
            html: Raw HTML content

        Returns:
            Extracted text content
        """
        # Try trafilatura first (better quality extraction)
        content = trafilatura.extract(
            html,
            output_format="txt",
            include_links=False,
            include_comments=False,
            include_tables=True,
            no_fallback=False
        )

        if content and content.strip():
            return content.strip()

        # Fallback to BeautifulSoup if trafilatura fails
        return self._extract_with_beautifulsoup(html)

    def _extract_with_beautifulsoup(self, html: str) -> str:
        """
        Fallback extraction using BeautifulSoup.

        Args:
            html: Raw HTML content

        Returns:
            Extracted text content
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()

            # Try to find main content
            main_content = (
                soup.find("main") or
                soup.find("article") or
                soup.find("div", class_=re.compile(r"content|main|article", re.I)) or
                soup.find("body")
            )

            if main_content:
                text = main_content.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            lines = [line for line in lines if line]
            return "\n".join(lines)

        except Exception as e:
            raise RuntimeError(f"BeautifulSoup extraction failed: {str(e)}")