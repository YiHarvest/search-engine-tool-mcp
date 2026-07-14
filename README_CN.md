# 搜索引擎工具 MCP

一个支持多提供者的 Python MCP（模型上下文协议）服务器，用于网络搜索和内容提取，可用于 Codex、Trae 及其他支持 STDIO MCP 的客户端。

## 版本

当前版本：**0.4.3**

## 功能特性

- 🔍 **网络搜索**：使用 You.com 或 Tavily API 搜索网络
- 📄 **内容提取**：从任意 URL 提取正文内容（免费本地提取或 Tavily API）
- 🔄 **自动提供者选择**：自动选择最佳可用提供者
- 🔑 **可选 API Keys**：无需 API Key 即可使用本地提取（Tavily 需要 API Key 以获得增强提取功能）
- 🚀 **MCP 兼容**：完全支持模型上下文协议
- 🔒 **安全防护**：内置 SSRF 防护，禁止访问 localhost、内网 IP 等

## 安装

### 从 PyPI 安装（推荐）

✅ **最新版本 0.4.3 已发布到 PyPI！**

**PyPI 包页面：** https://pypi.org/project/search-engine-tool-mcp/0.4.3/

```bash
# 使用 pip 安装
pip install search-engine-tool-mcp==0.4.3

# 或使用 uv 安装（推荐）
uv pip install search-engine-tool-mcp==0.4.3

# 或使用 uvx 直接运行（无需安装）
uvx --from search-engine-tool-mcp==0.4.3 search-engine-tool-mcp
```

### 从源码安装

```bash
git clone https://github.com/YiHarvest/search-engine-tool.git
cd search-engine-tool
pip install -e .
```

## 配置

### 环境变量

- **SEARXNG_BASE_URL**（推荐）：你的自托管 SearXNG 实例地址，例如 `http://127.0.0.1:8080`。
- **TALORDATA_API_KEY**（可选）：你的 TalorData SERP API Key，仅用于 `web_search`。
- **YDC_API_KEY**（可选）：你的 You.com API Key。获取地址：[https://you.com/platform](https://you.com/platform)
- **TAVILY_API_KEY**（可选）：你的 Tavily API Key，用于高级功能和回退提取。

**自动提供者选择逻辑：**

对于 **web_search**：
- 如果存在 `TALORDATA_API_KEY` → 优先使用 TalorData
- 否则如果存在 `SEARXNG_BASE_URL` → 使用 SearXNG
- 否则如果存在 `YDC_API_KEY` 或 `YOU_API_KEY` → 使用 You.com
- 否则如果存在 `TAVILY_API_KEY` → 使用 Tavily
- 当前提供者失败或返回空结果时，按照可用配置自动回退；如果均未配置 → 抛出错误

对于 **web_extract**：
- 默认提供者是 `local`（免费，无需 API Key）
- 如果 provider="auto" 且本地提取失败：
  - 如果有 TAVILY_API_KEY，自动回退到 Tavily
  - 否则返回错误
- 如果 provider="tavily" → 需要 TAVILY_API_KEY

### 快速配置

1. 复制示例配置文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的 API Keys：
```bash
YDC_API_KEY="your-ydc-api-key-here"
TAVILY_API_KEY="your-tavily-api-key-here"
SEARXNG_BASE_URL="http://127.0.0.1:8080"
TALORDATA_API_KEY="your-talordata-api-key-here"
```

### 或手动设置环境变量

```bash
# 设置 You.com API Key（可选）
export YDC_API_KEY="ydc-sk-your-api-key"

# 或设置 Tavily API Key（可选）
export TAVILY_API_KEY="tvly-your-api-key"

# 设置 SearXNG 实例 URL（可选）
export SEARXNG_BASE_URL="http://127.0.0.1:8080"

# 设置 TalorData API Key（可选，仅用于搜索）
export TALORDATA_API_KEY="your-talordata-api-key"
```

### 本地部署 SearXNG（推荐，免费）

SearXNG 是一个免费的开源搜索引擎，支持多引擎聚合搜索。以下是快速部署步骤：

#### 1. 创建配置文件

```bash
mkdir -p /tmp/searxng
```

创建 `/tmp/searxng/settings.yml`：

```yaml
use_default_settings: true

search:
  safe_search: 0
  formats:
    - html
    - json

server:
  port: 8080
  bind_address: "0.0.0.0"
  secret_key: "change_this_to_unique_value"
  limiter: false
  image_proxy: false
  http_protocol_headers:
    X-Forwarded-For: "127.0.0.1"
    X-Real-IP: "127.0.0.1"

outgoing:
  request_timeout: 10.0
  max_request_timeout: 15.0

engines:
  - name: google
    engine: google
  - name: bing
    engine: bing
  - name: duckduckgo
    engine: duckduckgo
  - name: brave
    engine: brave
```

#### 2. 启动容器

```bash
docker run -d \
  --name searxng \
  --restart unless-stopped \
  --network host \
  -v /tmp/searxng/settings.yml:/etc/searxng/settings.yml \
  searxng/searxng:latest
```

#### 3. 验证服务

```bash
# 等待服务启动（约5秒）
sleep 5

# 测试 JSON API
curl -s "http://127.0.0.1:8080/search?q=test&format=json" | jq '.results | length'
```

如果返回数字（如 10-50），说明配置成功。

#### 4. 设置环境变量

```bash
SEARXNG_BASE_URL="http://127.0.0.1:8080"
```

#### 常见问题

**问题：返回空结果或所有引擎不可用**

- **原因**：容器内配置了错误的代理（如 `http://127.0.0.1:7890`）
- **解决**：确保配置文件中**没有** `HTTP_PROXY` 或 `HTTPS_PROXY` 环境变量

**问题：403 Forbidden**

- **原因**：缺少必要的 HTTP 头配置
- **解决**：确保 `settings.yml` 中包含 `http_protocol_headers` 配置

#### 生产环境部署

生产或公网部署请使用反向代理、HTTPS、访问控制和随机 `secret_key`。详细部署方式参见 [SearXNG 官方文档](https://docs.searxng.org/admin/installation-docker.html)。

### MCP 客户端配置

密钥必须通过 MCP 服务进程的环境变量传入。下面所有值均为占位符，请只填写你实际使用的提供者；不要把真实密钥提交到 Git。

#### Trae（JSON）

在 Trae 的 MCP 设置中添加或导入以下配置：

```json
{
  "mcpServers": {
    "search-engine-tool": {
      "command": "uvx",
      "args": [
        "--from",
        "search-engine-tool-mcp==0.4.3",
        "search-engine-tool-mcp"
      ],
      "env": {
        "TALORDATA_API_KEY": "your-talordata-api-key",
        "TALORDATA_BASE_URL": "https://serpapi.talordata.net/serp/v1/request",
        "SEARXNG_BASE_URL": "http://127.0.0.1:8080",
        "YDC_API_KEY": "your-you-api-key",
        "TAVILY_API_KEY": "tvly-your-tavily-api-key"
      }
    }
  }
}
```

保存后重启或刷新 MCP 服务。如果 Trae 与 SearXNG 不在同一台主机或容器网络中，`127.0.0.1` 指向的是 Trae/MCP 进程所在环境，需要改成该环境可访问的 SearXNG 地址。

#### Codex（TOML）

Codex CLI 和 Codex IDE 扩展共用 `config.toml`。将下面内容添加到用户配置 `~/.codex/config.toml`，或者可信项目的 `.codex/config.toml`：

```toml
[mcp_servers.search-engine-tool]
command = "uvx"
args = [
  "--from",
  "search-engine-tool-mcp==0.4.3",
  "search-engine-tool-mcp",
]
startup_timeout_sec = 30
tool_timeout_sec = 60

[mcp_servers.search-engine-tool.env]
TALORDATA_API_KEY = "your-talordata-api-key"
TALORDATA_BASE_URL = "https://serpapi.talordata.net/serp/v1/request"
SEARXNG_BASE_URL = "http://127.0.0.1:8080"
YDC_API_KEY = "your-you-api-key"
TAVILY_API_KEY = "tvly-your-tavily-api-key"
```

重启 Codex 后，可运行 `codex mcp list`，或在 Codex 会话中使用 `/mcp` 检查连接。Codex 的配置格式和可选项参见 [Codex MCP 官方文档](https://developers.openai.com/codex/mcp/)。

## 使用方法

### 可用工具

MCP 服务器提供两个工具：

#### 1. web_search

搜索网络信息。

**参数：**

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `query` | string | ✅ | - | 搜索查询字符串 |
| `provider` | string | ❌ | `"auto"` | 使用的提供者：`"auto"`、`"searxng"`、`"talordata"`、`"you"` 或 `"tavily"` |
| `max_results` | integer | ❌ | `5` | 最大结果数量（1-20） |
| `search_depth` | string | ❌ | `"basic"` | 搜索深度：`"basic"` 或 `"advanced"`（仅 Tavily） |
| `include_answer` | boolean | ❌ | `false` | 包含 AI 生成的答案（仅 TalorData 和 Tavily） |

**响应示例：**

```json
{
  "query": "搜索查询",
  "provider": "you",
  "count": 5,
  "results": [
    {
      "href": "https://example.com",
      "title": "结果标题",
      "abstract": "结果摘要..."
    }
  ]
}
```

#### 2. web_extract

从指定 URL 提取内容。

**参数：**

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `url` | string | ✅ | - | 要提取内容的 URL |
| `provider` | string | ❌ | `"auto"` | 使用的提供者：`"auto"`、`"local"` 或 `"tavily"` |

**提供者选项：**

- **`local`**（默认免费提供者）：免费本地提取，无需 API Key。使用 trafilatura + BeautifulSoup 提取内容。
  - ⚠️ **限制：**
    - 不执行 JavaScript
    - 无法绕过登录墙、付费墙或验证码
    - 动态/SPA 类页面可能提取不完整
    - 超时时间：20 秒（默认）
    - SSRF 防护：禁止访问 localhost、内网 IP、私有域名
- **`tavily`**（增强提供者）：Tavily API 提取，需要 `TAVILY_API_KEY`。
  - ✅ 更适合复杂/动态页面
  - ✅ 可以处理更多挑战性网站
- **`auto`**（默认）：优先使用 local，如果失败且有 `TAVILY_API_KEY` 则自动回退到 Tavily。

**响应示例：**

```json
{
  "url": "https://example.com",
  "content": "提取的内容...",
  "provider": "local"
}
```

### 提供者选择逻辑

- `provider="searxng"`：始终使用 SearXNG（需要 `SEARXNG_BASE_URL`）
- `provider="talordata"`：始终使用 TalorData（需要 `TALORDATA_API_KEY`，仅支持搜索）
- `provider="you"`：始终使用 You.com（需要 `YDC_API_KEY`）
- `provider="tavily"`：始终使用 Tavily（需要 `TAVILY_API_KEY`）
- `provider="local"`：始终使用本地提取（免费，无需 API Key）
- `provider="auto"` **（默认）**：
  - **web_search**：初始选择顺序为 TalorData → SearXNG → You.com → Tavily；失败或空结果时按当前提供者的可用回退链切换
  - **web_extract**：优先使用 local，失败时自动回退到 Tavily（如果 `TAVILY_API_KEY` 可用）

## 开发

### 设置开发环境

```bash
# 克隆仓库
git clone https://github.com/YiHarvest/search-engine-tool.git
cd search-engine-tool

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装开发模式
pip install -e ".[dev]"
```

### 运行测试

```bash
python -m pytest
```

### 构建包

```bash
python -m build
```

### 检查包

```bash
python -m twine check dist/*
```

## API 参考

### You.com 提供者

- **搜索 API**：`https://ydc-index.io/v1/search`
- **要求**：需要 API Key (`YDC_API_KEY`)
- **获取地址**：[https://you.com/platform](https://you.com/platform)

### Tavily 提供者

- **搜索 API**：`https://api.tavily.com/search`
- **提取 API**：`https://api.tavily.com/extract`
- **要求**：需要 API Key (`TAVILY_API_KEY`)
- **特性**：高级搜索深度、AI 生成的答案

### Local 提取提供者

- **技术栈**：trafilatura + BeautifulSoup
- **要求**：无需 API Key
- **特性**：免费、本地提取、SSRF 防护
- **限制**：不执行 JavaScript、无法绕过付费墙/验证码

## 项目结构

```
search-engine-tool/
├── src/search_engine_tool_mcp/
│   ├── __init__.py
│   ├── server.py          # MCP 服务器实现
│   ├── search.py          # 网络搜索功能
│   ├── extract.py         # 内容提取
│   ├── schemas.py         # Pydantic 数据模型
│   └── providers/
│       ├── __init__.py
│       ├── you.py         # You.com 提供者（搜索）
│       ├── tavily.py      # Tavily 提供者（搜索 + 提取）
│       └── local_extract.py  # 本地提取提供者（免费）
├── tests/
│   ├── test_search.py
│   ├── test_providers.py
│   └── test_extract.py
├── pyproject.toml
└── README.md
```

## 许可证

MIT 许可证

## 贡献

欢迎贡献！请随时提交 Pull Request。

## 支持

如有问题和功能请求，请使用 [GitHub Issues](https://github.com/YiHarvest/search-engine-tool-mcp/issues) 页面。

## 更新日志

### v0.2.0
- ✨ 新增本地提取提供者（免费，无需 API Key）
- 🔒 新增 SSRF 防护（禁止访问 localhost、内网 IP）
- 🌐 支持代理配置（通过 httpx[socks]）
- 🔄 自动提供者回退机制
- 🇨🇳 中文注释和文档支持
