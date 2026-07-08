# Search Engine Tool MCP

A Python MCP (Model Context Protocol) Server for web search and extraction with multiple providers.

## Version

Current version: **0.4.1**

## Features

- 🔍 **Web Search**: Search the web using You.com or Tavily APIs
- 📄 **Content Extraction**: Extract clean content from any URL (free local extraction or Tavily API)
- 🔄 **Auto Provider Selection**: Automatically chooses the best available provider
- 🔑 **Optional API Keys**: Works without API keys using local extraction (Tavily requires API key for enhanced extraction)
- 🚀 **MCP Compatible**: Full support for Model Context Protocol

## Installation

### From PyPI (Recommended)

```bash
# Using pip
pip install search-engine-tool-mcp

# Or using uv (recommended)
uv pip install search-engine-tool-mcp
```

### From Source

```bash
git clone https://github.com/YiHarvest/search-engine-tool.git
cd search-engine-tool

# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

## Configuration

### Environment Variables

- **SEARXNG_BASE_URL** (recommended): Your SearXNG instance URL. Example: `http://127.0.0.1:8080`
- **TALORDATA_API_KEY** (recommended): Your TalorData SERP API key for web search. Get it at [https://dashboard.talordata.com](https://dashboard.talordata.com). **Note: TalorData only supports web_search, not web_extract.**
- **YDC_API_KEY** (recommended): Your You.com API key. Get it at [https://you.com/platform](https://you.com/platform).
- **TAVILY_API_KEY** (optional): Your Tavily API key for advanced features and fallback extraction.

**Auto Provider Selection Logic:**

For **web_search**:
- If SEARXNG_BASE_URL exists → uses SearXNG (free, self-hosted)
  - If SearXNG fails or returns empty results → falls back to TalorData, Tavily, or You.com
- If TALORDATA_API_KEY exists → uses TalorData (SERP API provider)
  - If TalorData fails or returns empty results → falls back to Tavily or You.com
- If TAVILY_API_KEY exists → uses Tavily
- If YDC_API_KEY or YOU_API_KEY exists → uses You.com
- If none configured → throws error

For **web_extract**:
- Default provider is `local` (free, no API key required)
- If provider="auto" and local extraction fails:
  - Falls back to Tavily if `TAVILY_API_KEY` is available
  - Otherwise returns error
- If provider="tavily" → requires `TAVILY_API_KEY`
- **Note: TalorData does NOT support web_extract**

### Quick Configuration

1. Copy the example configuration file:
```bash
cp .env.example .env
```

2. Edit the `.env` file and fill in your API keys:
```bash
YDC_API_KEY="your-ydc-api-key-here"
TAVILY_API_KEY="your-tavily-api-key-here"
SEARXNG_BASE_URL="http://127.0.0.1:8080"
TALORDATA_API_KEY="your-talordata-api-key-here"
```

### Or Set Environment Variables Manually

```bash
# Set SearXNG base URL (recommended for free self-hosted search)
export SEARXNG_BASE_URL="http://127.0.0.1:8080"

# Set TalorData API key (recommended for SERP API search)
export TALORDATA_API_KEY="your-talordata-api-key"

# Set You.com API key (alternative)
export YDC_API_KEY="ydc-sk-your-api-key"

# Or set Tavily API key (alternative)
export TAVILY_API_KEY="tvly-your-api-key"
```

### MCP Client Configuration

Add to your MCP client configuration (e.g., Claude Desktop, Cursor, or other MCP-compatible clients):

```json
{
  "mcpServers": {
    "search-engine-tool": {
      "command": "uvx",
      "args": [
        "--from",
        "search-engine-tool-mcp==0.4.1",
        "search-engine-tool-mcp"
      ],
      "env": {
        "TALORDATA_API_KEY": "your-talordata-api-key",
        "TALORDATA_BASE_URL": "https://serpapi.talordata.net/serp/v1/request",
        "TALORDATA_TRIAL_EXPIRES_AT": "2026-07-15T06:05:25+08:00",
        "SEARXNG_BASE_URL": "http://127.0.0.1:8080"
      }
    }
  }
}
```

## Usage

### Available Tools

The MCP server exposes two tools:

#### 1. web_search

Search the web for information.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ | - | Search query string |
| `provider` | string | ❌ | `"auto"` | Provider to use: `"auto"`, `"searxng"`, `"talordata"`, `"you"`, or `"tavily"` |
| `max_results` | integer | ❌ | `5` | Maximum number of results (1-20) |
| `search_depth` | string | ❌ | `"basic"` | Search depth: `"basic"` or `"advanced"` (Tavily only) |
| `include_answer` | boolean | ❌ | `false` | Include AI-generated answer (Tavily and TalorData only) |

**Response:**

```json
{
  "query": "search query",
  "provider": "jina",
  "count": 5,
  "results": [
    {
      "href": "https://example.com",
      "title": "Result Title",
      "abstract": "Result snippet..."
    }
  ]
}
```

#### 2. web_extract

Extract content from a specific URL.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | ✅ | - | URL to extract content from |
| `provider` | string | ❌ | `"auto"` | Provider to use: `"auto"`, `"local"`, or `"tavily"` |

**Provider Options:**

- **`local`** (default free provider): Free local extraction, no API key required. Uses trafilatura + BeautifulSoup for content extraction.
  - ⚠️ **Limitations:**
    - Does not execute JavaScript
    - Cannot bypass login walls, paywalls, or CAPTCHA
    - Dynamic/spa-style pages may have incomplete extraction
    - Timeout: 20 seconds (default)
- **`tavily`** (enhanced provider): Tavily API extraction, requires `TAVILY_API_KEY`.
  - ✅ Better for complex/dynamic pages
  - ✅ Can handle more challenging sites
- **`auto`** (default): Tries local first, falls back to Tavily if `TAVILY_API_KEY` is available and local fails.

**Response:**

```json
{
  "url": "https://example.com",
  "content": "Extracted content...",
  "provider": "local"
}
```

### Provider Selection Logic

- `provider="searxng"`: Always use SearXNG (requires `SEARXNG_BASE_URL`)
  - ⚠️ **Limitations:**
    - Requires self-hosted SearXNG instance
    - Timeout: 15 seconds
    - If returns empty results → throws error
- `provider="you"`: Always use You.com (requires `YDC_API_KEY`)
- `provider="tavily"`: Always use Tavily (requires `TAVILY_API_KEY`)
- `provider="auto"`** (default):
  - If `SEARXNG_BASE_URL` environment variable is set → use SearXNG
    - If SearXNG fails or returns empty results → fallback to TalorData, Tavily, or You.com
  - If `TALORDATA_API_KEY` exists → use TalorData
    - If TalorData fails or returns empty results → fallback to Tavily or You.com
  - If `TAVILY_API_KEY` exists → use Tavily
  - If `YDC_API_KEY` or `YOU_API_KEY` exists → use You.com
  - Otherwise → throws error

## TalorData SERP API

TalorData is a SERP (Search Engine Results Page) API provider that offers structured search results from Google, Bing, and other search engines. **Important: TalorData is ONLY for web_search, NOT for web_extract.**

### Features

- ✅ **High quality**: Top-ranked SERP API provider
- ✅ **Multi-engine support**: Google, Bing, DuckDuckGo, and more
- ✅ **Structured output**: Clean JSON format with detailed metadata
- ✅ **AI Overview**: Supports AI-generated answers (`include_answer` parameter)
- ✅ **Optional fields**: Returns position, source, display_link for advanced analysis
- ✅ **Fast response**: Average response time under 1 second
- ✅ **Pay for success**: Only charges for successful requests
- ⚠️ **API key required**: Requires `TALORDATA_API_KEY`
- ⚠️ **Web search only**: Does NOT support web_extract

### Get API Key

1. Visit [TalorData Dashboard](https://dashboard.talordata.com)
2. Sign up for a free account
3. Navigate to API Playground to get your API token
4. Set the environment variable:

```bash
export TALORDATA_API_KEY="your-api-key-here"
```

### Usage Example

```python
# Web search with TalorData
results = await web_search(
    query="OpenAI",
    provider="talordata",
    max_results=10,
    include_answer=True  # Get AI-generated overview
)

# Response includes:
# - href: URL of the result
# - title: Title of the result
# - abstract: Description or snippet
# - position: Position in search results (optional)
# - source: Source name (optional)
# - display_link: Displayed link (optional)
# - answer: AI-generated overview (if include_answer=True)
```

## SearXNG Setup

SearXNG is a free, self-hosted metasearch engine that aggregates results from multiple search engines.

### Installation

1. **Using Docker (recommended)**:
```bash
docker run -d --name searxng -p 8080:8080 searxng/searxng:latest
```

2. **Manual installation**: Follow the [SearXNG documentation](https://github.com/searxng/searxng)

### Configuration

After setting up SearXNG, set the environment variable:

```bash
export SEARXNG_BASE_URL="http://127.0.0.1:8080"
```

### Features

- ✅ **Free**: No API key required
- ✅ **Privacy-focused**: No tracking
- ✅ **Multiple engines**: Aggregates results from Google, Bing, DuckDuckGo, etc.
- ✅ **Customizable**: Choose specific engines with `engines` parameter
- ⚠️ **Self-hosted**: Requires running your own instance
- ⚠️ **Timeout**: 15-second limit to prevent MCP hanging

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/YiHarvest/search-engine-tool.git
cd search-engine-tool

# Using uv (recommended)
uv sync --all-extras

# Or using pip
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Run Tests

```bash
# Using uv
uv run pytest

# Or using pytest directly
pytest
```

### Build Package

```bash
# Using uv (recommended)
uv build

# Or using build directly
python -m build
```

### Check Package

```bash
# Using uv
uv run twine check dist/*

# Or using twine directly
twine check dist/*
```

## API Reference

### Jina Provider

- **Search API**: `https://api.jina.ai/search`
- **Reader API**: `https://r.jina.ai/{url}`
- **Requirements**: No API key needed
- **Rate Limits**: Subject to Jina's public API limits

### Tavily Provider

- **Search API**: `https://api.tavily.com/search`
- **Extract API**: `https://api.tavily.com/extract`
- **Requirements**: API key required (`TAVILY_API_KEY`)
- **Features**: Advanced search depth, AI-generated answers

## Project Structure

```
search-engine-tool/
├── src/search_engine_tool_mcp/
│   ├── __init__.py
│   ├── server.py          # MCP server implementation
│   ├── search.py          # Web search functionality
│   ├── extract.py         # Content extraction
│   ├── schemas.py         # Pydantic data models
│   └── providers/
│       ├── __init__.py
│       ├── you.py         # You.com provider (search)
│       ├── tavily.py      # Tavily provider (search + extract)
│       └── local_extract.py  # Local extraction provider (free)
├── tests/
│   ├── test_search.py
│   └── test_providers.py
│   └── test_extract.py
├── pyproject.toml
└── README.md
```
## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/YiHarvest/search-engine-tool/issues) page.