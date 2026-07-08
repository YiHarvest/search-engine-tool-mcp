# Search Engine Tool MCP

A Python MCP (Model Context Protocol) Server for web search and extraction with multiple providers.

## Version

Current version: **0.2.0**

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

- **YDC_API_KEY** (recommended): Your You.com API key. Get it at [https://you.com/platform](https://you.com/platform).
- **TAVILY_API_KEY** (optional): Your Tavily API key for advanced features and fallback extraction.

**Auto Provider Selection Logic:**

For **web_search**:
- If both keys exist → prioritizes You.com
- If only YDC_API_KEY → uses You.com
- If only TAVILY_API_KEY → uses Tavily
- If neither key → throws error

For **web_extract**:
- Default provider is `local` (free, no API key required)
- If provider="auto" and local extraction fails:
  - Falls back to Tavily if `TAVILY_API_KEY` is available
  - Otherwise returns error
- If provider="tavily" → requires `TAVILY_API_KEY`

```bash
# Set You.com API key (recommended)
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
      "command": "search-engine-tool-mcp",
      "env": {
        "YDC_API_KEY": "ydc-sk-your-api-key",
        "TAVILY_API_KEY": "tvly-your-api-key"
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
| `provider` | string | ❌ | `"auto"` | Provider to use: `"auto"`, `"jina"`, or `"tavily"` |
| `max_results` | integer | ❌ | `5` | Maximum number of results (1-20) |
| `search_depth` | string | ❌ | `"basic"` | Search depth: `"basic"` or `"advanced"` (Tavily only) |
| `include_answer` | boolean | ❌ | `false` | Include AI-generated answer (Tavily only) |

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

- `provider="you"`: Always use You.com (requires `YDC_API_KEY`)
- `provider="tavily"`: Always use Tavily (requires `TAVILY_API_KEY`)
- `provider="auto"`** (default):
  - If `YDC_API_KEY` environment variable is set → use You.com
  - Otherwise → use Tavily

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