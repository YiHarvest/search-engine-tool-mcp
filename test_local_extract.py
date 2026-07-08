"""Manual test script for local extract provider."""

import asyncio
from src.search_engine_tool_mcp.extract import web_extract


async def test_local_extract():
    """Test local extract provider with real URLs."""

    test_urls = [
        "https://httpbin.org/html",  # Simple HTML test page
        "https://example.com",  # Basic example site
        "https://www.wikipedia.org",  # Wikipedia homepage
    ]

    print("=" * 60)
    print("Testing Local Extract Provider")
    print("=" * 60)

    for url in test_urls:
        print(f"\n\nTesting: {url}")
        print("-" * 60)

        try:
            result = await web_extract(url, provider="local")

            print(f"✅ Success!")
            print(f"Provider: {result.provider}")
            print(f"URL: {result.url}")
            print(f"Content length: {len(result.content)} characters")
            print(f"\nContent preview (first 200 chars):")
            print(result.content[:200] + "...")

        except Exception as e:
            print(f"❌ Failed: {str(e)}")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_local_extract())