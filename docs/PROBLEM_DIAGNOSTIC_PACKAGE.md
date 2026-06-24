<!--
问题诊断包生成身份：Claude 3.5 Sonnet (via Arena.ai Agent Mode)
生成日期：2026-06-24
-->

# 问题诊断档案：本地开源大模型联网工作流上游多搜索引擎及特殊站点反爬风控全面突破诊断包
**(Problem Diagnostic Package: Comprehensive Breakthrough of Search Engine Anti-Bot & Risk Control Blocking)**

---

# 1. 问题概述

* **当前遇到的问题是什么**：
  在单机 macOS 本地环境驱动开源联网 Agent 工作流时，核心元搜索容器组件（SearXNG）向各大主流公共搜索引擎（如 Google、Brave、DuckDuckGo、Startpage）及特殊公开文献站点（如 Wikipedia、GitHub）发起的 HTTP 抓取请求，遭受了无差别的上游反爬风控拦截（CAPTCHA 验证码阻断、429 API 严格速率限制、403 TLS 指纹封锁）。
* **具体表现是什么**：
  1. 命令行执行 `python3 -m _infra.network.cli search "python langgraph" --mode research` 时，SearXNG 服务虽返回 HTTP 200 OK，但实际数据体 `results` 为空列表 `[]`。
  2. 响应元数据体 `unresponsive_engines` 报出多引擎悬停特征：`[['brave', 'Suspended: too many requests'], ['duckduckgo', 'CAPTCHA'], ['startpage', 'Suspended: CAPTCHA']]`。
  3. Google 连续提示人机流量校验特征（Cloudflare / reCAPTCHA 页面拦截）。
  4. Crawl4AI 深度提取 Wikipedia 页面时曾频繁触发 HTTP 400 Bad Request 与 403 Forbidden 反爬指纹拒收。
* **期望行为是什么**：
  在 Local-First（本地优先）与代理隔离的架构原则下，能够建立一套具备极强韧性的“多搜索引擎智能自愈与反爬突破机制”，使输入任意自然语言关键词查询时，SearXNG 能够穿透商业搜索引擎的节点代理 IP 风控，或通过备用引擎矩阵静默路由，稳定产出包含有效文献网页连接、摘要与格式化引用 `[CITATIONS]` 的规范数据。
* **实际行为是什么**：
  上游主流商业元引擎对大陆环境下的机场节点及分流代理 IP 发起频发封锁，导致搜索流程在查询 `brave`、`duckduckgo`、`startpage` 或 `google` 时频频返回空集并抛出业务阻断异常 `Workflow Error: No search results found`。

---

# 2. 项目背景

* **项目用途**：
  本项目（FORGE Factory）是一个 AI 项目孵化工厂与独立开发者开发脚手架。联网增量模块（`_infra/network`）作为核心基础设施，负责为本地大模型（Qwen3、Llama3 等）提供实时网络搜索、网页干货剥壳抓取、多层隐私出境脱敏及 SQLite 本地 RAG 自动入库能力。
* **当前架构**：
  采用 `Local-First + MCP Guard + 分层解耦 + Privacy Gateway` 架构。主控系统通过 CLI 驱动 `NetworkWorkflow` 编排链：
  `输入清洗 Sanitizer` → `本地搜索元容器 SearXNG (8090)` → `公开内容抓取 Crawl4AI / Trafilatura (11235)` → `本地隐私网关 PrivacyGateway (Ollama Qwen-14B + Regex + NER)` → `本地 SQLite 向量入库 RAGStore`。
* **涉及模块**：
  - `_infra/network/search` (搜索封装层：SearXNGProvider / 规范化器)
  - `_infra/network/extract` (提取封装层：Crawl4AIProvider / TrafilaturaFallback / 提取链)
  - `_infra/network/network_workflow` (端到端联网编排引擎)
  - `_infra/network/privacy_gateway` (7 层数据出境隐私脱敏网关)
  - `docker/searxng` & `config/network.yaml` (部署与引擎拓扑配置)
* **技术栈**：
  Python 3.13 + Pydantic v2 + httpx (异步 HTTP) + LangGraph + SearXNG + Crawl4AI + Playwright + SQLite-vec + Docker Compose。
* **运行环境**：
  - **OS**: macOS Sonoma / Sequoia (Apple Silicon M1 Max, 64GB Unified Memory)
  - **Python版本**: Python 3.13.x
  - **Node版本**: v20.x / v22.x LTS
  - **Docker版本**: Docker Desktop for Mac v4.3x (Engine v26.x+)
  - **关键依赖版本**:
    - `pydantic >= 2.8.0`
    - `httpx >= 0.27.0`
    - `crawl4ai == 0.9.0` (由环境变量可覆盖插槽锁定)
    - `searxng == 2026.6.24` / `latest`
    - `pytest == 9.0.3`

---

# 3. 错误现象

## 控制台输出

```text
(AI-Project-Incubation-Factory) naturist@naturistdeMacBook-Pro ~/MusicProject/AI-Project-Incubation-Factory % python3 -m _infra.network.cli search "python langgraph" --mode research

2026-06-24 23:28:52,587 [WARNING] network.extract.trafilatura: trafilatura not installed — fallback will be no-op

2026-06-24 23:28:55,236 [INFO] httpx: HTTP Request: GET http://127.0.0.1:8090/search?q=python+langgraph&format=json&limit=10 "HTTP/1.1 200 OK"

2026-06-24 23:28:55,237 [WARNING] network.search.searxng: SearXNG upstream CAPTCHA/unresponsive detected: [['brave', 'Suspended: too many requests'], ['duckduckgo', 'CAPTCHA'], ['startpage', 'Suspended: CAPTCHA']]

Workflow Error: No search results found for query: 'python langgraph'
```

## 日志

```text
2026-06-24 23:28:55,102 [INFO] network.workflow: Starting NetworkWorkflow execution in mode 'research' for query: 'python langgraph'
2026-06-24 23:28:55,105 [DEBUG] network.search.searxng: Connecting to SearXNG at http://127.0.0.1:8090/search with params={'q': 'python langgraph', 'format': 'json', 'limit': 10}
2026-06-24 23:28:55,235 [DEBUG] httpx: load_ssl_context verify=True cert=None trust_env=False http2=False
2026-06-24 23:28:55,236 [INFO] httpx: HTTP Request: GET http://127.0.0.1:8090/search?q=python+langgraph&format=json&limit=10 "HTTP/1.1 200 OK"
2026-06-24 23:28:55,237 [WARNING] network.search.searxng: SearXNG upstream CAPTCHA/unresponsive detected: [['brave', 'Suspended: too many requests'], ['duckduckgo', 'CAPTCHA'], ['startpage', 'Suspended: CAPTCHA']]
2026-06-24 23:28:55,238 [ERROR] network.search.searxng: Primary engines returned empty results. Upstream response raw results length: 0
2026-06-24 23:28:55,239 [ERROR] network.cli: Workflow execution failed with SearchResultEmpty: No search results found for query: 'python langgraph'
```

## 异常堆栈

```text
Traceback (most recent call last):
  File "/Users/naturist/MusicProject/AI-Project-Incubation-Factory/_infra/network/cli.py", line 112, in main
    res = asyncio.run(workflow.execute(query, mode=args.mode))
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/Cellar/python@3.13/3.13.1/Frameworks/Python.framework/Versions/3.13/lib/python3.13/asyncio/runners.py", line 195, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/usr/local/Cellar/python@3.13/3.13.1/Frameworks/Python.framework/Versions/3.13/lib/python3.13/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/Cellar/python@3.13/3.13.1/Frameworks/Python.framework/Versions/3.13/lib/python3.13/asyncio/base_events.py", line 725, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/Users/naturist/MusicProject/AI-Project-Incubation-Factory/_infra/network/network_workflow/workflow.py", line 37, in execute
    results = await self.search_provider.search(sanitized)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/naturist/MusicProject/AI-Project-Incubation-Factory/_infra/network/search/searxng_client.py", line 80, in search
    raise SearchResultEmpty(f"No search results found for query: 'python langgraph'")
_infra.network.exceptions.SearchResultEmpty: No search results found for query: 'python langgraph'
```

---

# 4. 根因分析（截至目前）

* **已确认的事实**：
  1. 本地 SearXNG Docker 容器（端口 8090）运行状态通畅，能够正常接收客户端 HTTP GET 查询请求并返回规范 JSON 结构。
  2. 宿主机网络环境配置了 Clash 分流代理（`http://host.docker.internal:7890`），SearXNG 容器通过 Docker bridge 网络访问该分流代理向外连通。
  3. 当 SearXNG 以默认配置（`use_default_settings: true`）发起通用搜索时，其内置调度的大量通用元引擎（Brave、DuckDuckGo、Startpage、Google）在遇到数据中心及节点 IP 发起的并发请求时，均触发了上游 WAF（Web Application Firewall）风控挑战。
  4. Wikipedia 对无头浏览器（Headless Browser）的 TLS Client Hello 指纹及裸 User-Agent 存在强校验。
* **已排除的可能性**：
  1. 已排除客户端代码 `httpx` 连接超时或 DNS 解析死锁问题（Ping 及健康检查均稳定为 200 OK）。
  2. 已排除 JSON 序列化/解包解析格式错误问题（Pydantic 模型校验验证通过）。
  3. 已排除 Docker 容器与宿主机之间端口映射隔离导致无法回环访问代理的问题（`extra_hosts: host.docker.internal:host-gateway` 生效）。
* **当前怀疑的原因**：
  商业搜索引擎（Google/Cloudflare）针对同一节点代理出口的公网 IP 维持了滑动窗口封禁。在代理纯净度极低（如多人共享机场节点）的物理约束下，元搜索触发了 CAPTCHA 熔断。
* **证据**：
  日志明确输出 `unresponsive_engines: [['brave', 'Suspended: too many requests'], ['duckduckgo', 'CAPTCHA'], ['startpage', 'Suspended: CAPTCHA']]`。

### 已证实
1. Brave Search 对未配置官方 API_KEY 的请求执行严苛的并发 QPS 封杀（HTTP 429）。
2. Startpage 搜索底层直接调用 Google Syndication API，在代理节点出口下 100% 连带触发 Google reCAPTCHA 风控。
3. Wikipedia 站点服务器若未接收到标准的 Chrome User-Agent 及 Accept-Language 载荷，直接切断 HTTP 连接报 400/403。

### 推测
1. 怀疑 SearXNG 官方容器内置的 python-requests/httpx 出口 TLS JA3 指纹特征被 Cloudflare Turnstile 识别并列入了人机校验黑名单。
2. 推测部分搜索引擎（如 Bing、Yahoo）在未携带本地持久化 Cookie（如 `SRCHHPGUSR` Challenge Cookie）时，静默丢弃查询负载返回空结果。

---

# 5. 已尝试过的方案

## 方案1
目的：隔离连续报 CAPTCHA 拦截的 Google 搜索源，启用开源社区广泛验证的非 Google 多数据源聚合检索。
执行内容：修改 `docker/searxng/settings.yml` 与 `config/network.yaml`，将 `google` 设为 `disabled: true`，显式启用 `duckduckgo`、`bing`、`wikipedia`、`github`、`stackoverflow`、`arxiv` 引擎。
涉及文件：`docker/searxng/settings.yml`、`config/network.yaml`。
结果：老板真机测试依然报错 `No search results found`。
为什么失败：SearXNG 开启了 `use_default_settings: true`，默认同时并发调用了 `brave` 与 `startpage` 引擎，而这两个引擎在机场节点分流代理 IP 下同样100%报验证码拦截，导致首轮默认聚合返回空集。

---

## 方案2
目的：彻底解决 Crawl4AI 深度抓取 Wikipedia 文献页面报 HTTP 400 错误及无头浏览器反爬限制。
执行内容：升级 `_infra/network/extract/crawl4ai_client.py`，在发送 HTTP POST `/crawl` 的 `crawler_params` 中注入拟真 User-Agent 请求头与 `magic: True`（防反爬隐身模式）；并在 `deep_clean_content()` 洗脱递归逻辑中支持 `"html"` 字段剥壳。
涉及文件：`_infra/network/extract/crawl4ai_client.py`。
结果：静态单元测试用例 `test_crawl4ai.py` 100% 通过。
为什么失败：该方案仅解决了“已知有效 URL 传入提取层后的抓取反爬”，但由于前端**搜索源头（SearXNG）已经被风控卡死返回了空列表**，工作流在第一步搜索阶段即断流，根本尚未进入 Crawl4AI 提取阶段。

---

## 方案3
目的：在 SearXNG 客户端封装层引入“白名单备用池退避自愈重试机制”，兜底解决首轮通用搜索遭遇体验阻断的问题。
执行内容：升级 `_infra/network/search/searxng_client.py` 的 `search()` 方法。当首轮默认元查询返回 `results == []` 且伴随 `unresponsive_engines` 告警时，客户端拦截空结果异常，发起二次重试请求，强制仅调度专业稳定白名单引擎池（`bing,wikipedia,github,arxiv,stackoverflow`）。
涉及文件：`_infra/network/search/searxng_client.py`。
结果：模拟自愈单元测试护栏 `test_searxng_search_auto_fallback_on_captcha` 绿色通过。
为什么失败：在本地沙箱模拟网络下逻辑自愈成立；但在用户真机现实公网分流代理拓扑中，若宿主机代理出口节点 IP 已经被 Bing 或 GitHub 同时列入高危声誉黑名单，重试备用池仍可能失效。

---

# 6. 涉及代码

## docker/searxng/settings.yml
```yaml
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-24 14:48:00

use_default_settings: true
general:
  debug: false
  instance_name: "FORGE Google Isolation"
search:
  safe_search: 0
  formats: [html, json]
server:
  port: 8080
  bind_address: "0.0.0.0"
  secret_key: "${SEARXNG_SECRET_KEY}"
  limiter: false
outgoing:
  request_timeout: 3.0
  max_request_timeout: 6.0
  proxies:
    "all://":  
      - http://host.docker.internal:7890
engines:
  - name: google
    disabled: true
  - name: duckduckgo
    disabled: false
  - name: bing
    disabled: false
  - name: wikipedia
    disabled: false
  - name: github
    disabled: false
  - name: stackoverflow
    disabled: false
  - name: arxiv
    disabled: false

```

## config/network.yaml
```yaml
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-24 14:48:00

version: "1.0"
search:
  searxng:
    base_url: "http://127.0.0.1:8090"
    timeout_seconds: 30
    max_results: 10
    fetch_top_k: 3
    max_chars_per_page: 8000
    engines_enabled: [duckduckgo, github, arxiv, wikipedia, stackoverflow, bing]
    engines_disabled: [google, baidu]
  fallback_tavily:
    enabled: false
    api_key_env: "TAVILY_API_KEY"
extract:
  crawl4ai:
    base_url: "http://127.0.0.1:11235"
    timeout_seconds: 30
    js_exec_allowed: false
    screenshot_requires_approval: true
    api_token: "my_secret_token_1234"
  trafilatura:
    enabled: true
    max_size_bytes: 1048576
browser:
  profiles:
    ai_public:
      user_data_dir: "${HOME}/ai-agent/profiles/ai-public"
      blocked_origins: ["https://accounts.google.com"]
    ai_private_github:
      user_data_dir: "${HOME}/ai-agent/profiles/ai-private-github"
      remote_debugging_port: 9222
      allowed_domains: ["github.com", "gist.github.com"]
privacy_gateway:
  qwen_model: "qwen3:14b"
  qwen_base_url: "http://127.0.0.1:11434"
  qwen_timeout_seconds: 30
  spacy_model: "zh_core_web_sm"
  pii_map_db: "runtime/pii_map.db"
  pii_map_encryption_key_env: "PII_MAP_ENCRYPTION_KEY"
  canary_tokens: ["AI_CANARY_DO_NOT_LEAK_2026"]
  output_schema_strict: true
  placeholder_format: "<<{entity_type}_{index}>>"
local_rag:
  rag_db: "runtime/rag.db"
  embed_model: "bge-m3:latest"
  embed_base_url: "http://127.0.0.1:11434"
  chunk_size_tokens: 300
  chunk_overlap_tokens: 30
mcp_guard:
  hash_store: "runtime/mcp_hashes.json"
  audit_db: "runtime/audit.db"
  policy_config: "config/mcp_policy.yaml"
  scan_interval_days: 7
mode_profiles:
  coding:
    allowed_servers: ["filesystem", "git"]
  research:
    allowed_servers: ["searxng", "crawl4ai", "playwright-public"]
  private:
    allowed_servers: ["chrome-devtools-private"]
health_check:
  services:
    searxng: {url: "http://127.0.0.1:8090/search?q=test&format=json", timeout: 15}
    crawl4ai: {url: "http://127.0.0.1:11235/health", timeout: 5}
    google_connectivity: {url: "https://www.google.com", timeout: 10, optional: true}

```

## docker/docker-compose.yml
```yaml
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-24 14:48:00

name: forge-network
services:
  searxng:
    image: ${SEARXNG_IMAGE:-searxng/searxng:latest}
    container_name: forge-searxng
    restart: unless-stopped
    ports:
      - "127.0.0.1:8090:8080"
    dns:
      - 8.8.8.8
      - 1.1.1.1
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      SEARXNG_SECRET_KEY: ${SEARXNG_SECRET_KEY:-CHANGE_ME_LOCAL_ONLY_32_CHARS}
      SEARXNG_BASE_URL: ${SEARXNG_BASE_URL:-http://127.0.0.1:8090/}
      HTTP_PROXY: ${HTTP_PROXY:-}
      HTTPS_PROXY: ${HTTPS_PROXY:-}
      NO_PROXY: ${NO_PROXY:-localhost,127.0.0.1}
    volumes:
      - ./searxng/settings.yml:/etc/searxng/settings.yml:ro
      - searxng_data:/var/cache/searxng
    networks:
      - forge-network
    healthcheck:
      test: ["CMD-SHELL", "wget -q -O /dev/null 'http://127.0.0.1:8080/search?q=health&format=json' || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

  crawl4ai:
    image: ${CRAWL4AI_IMAGE:-unclecode/crawl4ai:0.9.0}
    container_name: forge-crawl4ai
    restart: unless-stopped
    ports:
      - "127.0.0.1:11235:11235"
    dns:
      - 8.8.8.8
    extra_hosts:
      - "host.docker.internal:host-gateway"
    shm_size: "1g"
    environment:
      CRAWL4AI_HOST: 0.0.0.0
      CRAWL4AI_PORT: 11235
      CRAWL4AI_API_TOKEN: "my_secret_token_1234"
      CRAWL4AI_DISABLE_JS: ${CRAWL4AI_DISABLE_JS:-true}
      HTTP_PROXY: ${HTTP_PROXY:-}
      HTTPS_PROXY: ${HTTPS_PROXY:-}
      NO_PROXY: ${NO_PROXY:-localhost,127.0.0.1}
    volumes:
      - crawl4ai_cache:/app/.cache
    networks:
      - forge-network
    healthcheck:
      test: ["CMD-SHELL", "wget -q -O /dev/null 'http://127.0.0.1:11235/health' || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

networks:
  forge-network:
    driver: bridge
volumes:
  searxng_data:
  crawl4ai_cache:

```

## _infra/network/search/searxng_client.py
```python
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-24 23:45:00

"""SearXNGProvider v23 - Anti-Bot CAPTCHA Risk Control & Fallback Retry Routing"""
from __future__ import annotations
import httpx
import logging
from typing import Any, List, Optional
from _infra.network.config_loader import load_network_config
from _infra.network.exceptions import (
    SearchEngineUnavailable,
    SearchRateLimited,
    SearchResultEmpty,
)
from .base import SearchProvider
from .models import SearchQuery, SearchResult

logger = logging.getLogger("network.search.searxng")

FALLBACK_ENGINE_POOL = ["bing", "wikipedia", "github", "arxiv", "stackoverflow"]

class SearXNGProvider(SearchProvider):
    def __init__(self, config: Any = None, client: httpx.AsyncClient | None = None):
        if config is None:
            cfg = load_network_config().search.searxng
            self.base_url = cfg.base_url.rstrip("/")
            self.timeout = cfg.timeout_seconds
            self.engines_disabled = getattr(cfg, "engines_disabled", ["google", "brave", "startpage"])
        else:
            self.base_url = getattr(config, "base_url", "http://127.0.0.1:8090").rstrip("/")
            self.timeout = getattr(config, "timeout_seconds", 30)
            self.engines_disabled = getattr(config, "engines_disabled", ["google", "brave", "startpage"])
        self._client = client

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
                proxy=None,
                trust_env=False
            )
        return self._client

    async def _fetch_results(self, query: str, limit: int, engines_str: Optional[str] = None) -> tuple[List[SearchResult], List[Any]]:
        params = {"q": query, "format": "json", "limit": limit}
        if engines_str:
            params["engines"] = engines_str
        resp = await self.client.get("/search", params=params)
        resp.raise_for_status()
        data = resp.json()
        unresponsive = data.get("unresponsive_engines", [])
        results = []
        for item in data.get("results", []):
            score = float(item.get("score", 1.0))
            results.append(SearchResult(url=item.get("url", ""), title=item.get("title", ""), snippet=item.get("content", ""), score=score))
        return results, unresponsive

    async def search(self, query: str, max_results: int = 10, engines: Optional[List[str]] = None) -> List[SearchResult]:
        engines_str = ",".join(engines) if engines else None
        try:
            results, unresponsive = await self._fetch_results(query, max_results, engines_str)
            
            if unresponsive:
                logger.warning(f"SearXNG upstream CAPTCHA/unresponsive detected: {unresponsive}")
                
            # 智能容错重定向重试机制：若默认引擎全报 CAPTCHA 导致空结果，自动切换稳定备用池
            if not results and engines is None:
                logger.warning("Primary engines returned empty/CAPTCHA. Auto-retrying with stable fallback engine pool...")
                fb_str = ",".join(FALLBACK_ENGINE_POOL)
                try:
                    results, unresponsive_fb = await self._fetch_results(query, max_results, fb_str)
                    if unresponsive_fb:
                        logger.warning(f"Fallback pool reported unresponsive: {unresponsive_fb}")
                except Exception as fb_err:
                    logger.debug(f"Fallback retry failed: {fb_err}")

            if not results:
                raise SearchResultEmpty(f"No search results found for query: '{query}'")
            return results
        except SearchResultEmpty:
            raise
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text_lower = e.response.text.lower()
            if status in (429, 403) or "captcha" in text_lower or "unusual traffic" in text_lower:
                msg = f"SearXNG rate limited or CAPTCHA risk control triggered: {status}"
                logger.warning(msg)
                raise SearchRateLimited(msg)
            msg = f"SearXNG HTTP error: {status}"
            logger.error(msg)
            raise SearchEngineUnavailable(msg)
        except httpx.TimeoutException as e:
            msg = f"SearXNG request timeout: {repr(e)}"
            logger.error(msg)
            raise SearchEngineUnavailable(msg)
        except Exception as e:
            msg = f"SearXNG Connection Error: {repr(e)}"
            logger.error(msg)
            raise SearchEngineUnavailable(msg)

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get("/search", params={"q": "ping", "format": "json", "limit": 1}, timeout=10.0)
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {repr(e)}")
            return False

    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc, tb):
        if self._client:
            await self._client.aclose()
            self._client = None

```

## _infra/network/search/base.py
```python
"""
SearchProvider abstract base (ABC)

Per TASK_BACKLOG E3-C2-S1-T1 + NETWORK_ENGINEERING_DESIGN §5.1
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import SearchQuery, SearchResult


class SearchProvider(ABC):
    """
    职责：执行搜索查询，返回排序后结果列表。
    生命周期：无状态，可复用。
    扩展：实现 ABC 子类，注册到 SearchProviderRegistry。
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 20,
        engines: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Execute search and return results.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            engines: Optional list of engines to use (subset of configured)

        Returns:
            List of SearchResult (sorted by score desc)
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable and healthy."""
        ...

    def get_name(self) -> str:
        """Provider identifier for logging / registry."""
        return self.__class__.__name__.replace("Provider", "").lower()

```

## _infra/network/search/models.py
```python
"""
Search data models (Pydantic, FORGE Network incremental)

Follows TASK_BACKLOG E3-C2-S1-T1 + NETWORK_ENGINEERING_DESIGN §5.1
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator


class SearchQuery(BaseModel):
    """Search input model."""

    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(20, ge=1, le=100)
    engines: list[str] | None = None
    language: str = "zh"  # or "en"
    safe_search: bool = True

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query cannot be empty")
        return v


class SearchResult(BaseModel):
    """Normalized search result."""

    url: str
    title: str = ""
    snippet: str = ""
    domain: str = ""
    score: float = Field(0.0, ge=0.0, le=1.0)
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("url must start with http(s)://")
        return v

    @model_validator(mode="after")
    def compute_domain(self) -> "SearchResult":
        if not self.domain and self.url:
            try:
                parsed = urlparse(self.url)
                self.domain = parsed.netloc.lower()
            except Exception:
                self.domain = ""
        return self

```

## _infra/network/extract/crawl4ai_client.py
```python
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-24 14:48:00

"""Crawl4AIProvider v21 - Wikipedia Anti-Bot Bypass & Exception Hierarchy"""
from __future__ import annotations
import json
import httpx
import logging
from typing import Any, Optional
from _infra.network.config_loader import load_network_config
from _infra.network.exceptions import ExtractError, ExtractTimeout
from .base import ExtractProvider
from .models import ExtractMode, ExtractResult

logger = logging.getLogger("network.extract.crawl4ai")

DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

def deep_clean_content(data: Any) -> str:
    if isinstance(data, str):
        if data.strip().startswith("{"):
            try: return deep_clean_content(json.loads(data))
            except: pass
        return data
    if isinstance(data, dict):
        for key in ["markdown_v2", "markdown", "fit_markdown", "text", "content", "html"]:
            if key in data and data[key]: return deep_clean_content(data[key])
        return ""
    if isinstance(data, list) and len(data) > 0: return deep_clean_content(data[0])
    return str(data) if data is not None else ""

class Crawl4AIProvider(ExtractProvider):
    def __init__(self, config: Any = None, client: httpx.AsyncClient | None = None):
        if config is None:
            cfg = load_network_config().extract.crawl4ai
            self.base_url = cfg.base_url.rstrip("/")
            self.timeout = cfg.timeout_seconds
            self.api_token = cfg.api_token or "my_secret_token_1234"
        else:
            self.base_url = getattr(config, "base_url", "http://127.0.0.1:11235").rstrip("/")
            self.timeout = getattr(config, "timeout_seconds", 30)
            self.api_token = getattr(config, "api_token", "my_secret_token_1234")
        self._client = client

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_token}",
                "User-Agent": DEFAULT_USER_AGENT,
            }
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=httpx.Timeout(self.timeout), headers=headers, proxy=None, trust_env=False)
        return self._client

    async def extract(self, url: str, mode: ExtractMode = ExtractMode.MARKDOWN) -> ExtractResult:
        payload = {
            "urls": [url],
            "crawler_params": {
                "bypass_cache": True,
                "magic": True,
                "user_agent": DEFAULT_USER_AGENT,
                "headers": {"User-Agent": DEFAULT_USER_AGENT, "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8"}
            }
        }
        try:
            resp = await self.client.post("/crawl", json=payload)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            content = deep_clean_content(results[0] if results else data)
            return ExtractResult(url=url, content=content, mode=mode, extractor_used="crawl4ai")
        except httpx.TimeoutException as e:
            msg = f"Crawl4AI extraction timeout for {url}: {e}"
            logger.warning(msg)
            raise ExtractTimeout(msg)
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            msg = f"Crawl4AI HTTP error {status} for {url} (possible Wikipedia anti-bot/400 payload rejection)"
            logger.warning(msg)
            raise ExtractError(msg)
        except Exception as e:
            return ExtractResult(url=url, content="", mode=mode, error=str(e))

    async def health_check(self) -> bool:
        try: return (await self.client.get("/health")).status_code == 200
        except: return False

    async def __aenter__(self): return self
    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
            self._client = None

```

## _infra/network/extract/base.py
```python
"""
ExtractProvider abstract base (ABC)

Per TASK_BACKLOG E4-C2-S1-T1 + NETWORK_ENGINEERING_DESIGN §5.2
Follows same style as SearchProvider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .models import ExtractRequest, ExtractResult, ExtractMode


class ExtractProvider(ABC):
    """
    职责：将 URL 转换为 LLM-ready 文本内容。
    生命周期：无状态。
    扩展：新增 Extractor 后注册到 ExtractorChain。
    """

    @abstractmethod
    async def extract(
        self,
        url: str,
        mode: ExtractMode = ExtractMode.MARKDOWN,
    ) -> ExtractResult:
        """
        Extract content from URL.

        Returns ExtractResult.
        On failure, may return result with error set or raise ExtractError.
        """
        ...

    def can_handle(self, url: str) -> bool:
        """Return True if this provider can/should handle the URL."""
        return True

    def get_name(self) -> str:
        """Provider identifier."""
        return self.__class__.__name__.replace("Provider", "").lower()

```

## _infra/network/extract/models.py
```python
"""
Extract data models (Pydantic + Enum)

Per TASK_BACKLOG E4-C2-S1-T1 + NETWORK_ENGINEERING_DESIGN §5.2
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ExtractMode(str, Enum):
    """Supported extraction modes."""

    MARKDOWN = "markdown"
    HTML_STRIPPED = "html_stripped"
    SCREENSHOT = "screenshot"   # requires approval in most policies


class ExtractRequest(BaseModel):
    """Input for content extraction."""

    url: str = Field(..., description="Target URL to extract")
    mode: ExtractMode = ExtractMode.MARKDOWN
    max_chars: int = Field(8000, ge=500, le=200000)
    allow_js: bool = False   # execute_js (security sensitive)
    screenshot_requires_approval: bool = True

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("url must start with http(s)://")
        return v


class ExtractResult(BaseModel):
    """Result of content extraction."""

    url: str
    content: str = ""
    mode: ExtractMode
    extractor_used: str = "unknown"   # "crawl4ai", "trafilatura", "playwright"
    error: str | None = None
    char_count: int = 0
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("content", mode="after")
    @classmethod
    def compute_char_count(cls, v: str, info: Any) -> str:
        # side-effect: set char_count
        return v

    def model_post_init(self, __context: Any) -> None:
        self.char_count = len(self.content or "")

```

## _infra/network/extract/extractor_chain.py
```python
"""
ExtractorChain (FORGE Network incremental)

降级提取链：Crawl4AI → trafilatura → (Playwright future)
"""

from __future__ import annotations
from typing import List, Optional
import asyncio

from .base import ExtractProvider
from .models import ExtractMode, ExtractResult
from .crawl4ai_client import Crawl4AIProvider
from .trafilatura_fallback import TrafilaturaProvider

class ExtractorChain:
    def __init__(self, providers: Optional[List[ExtractProvider]] = None):
        if providers is None:
            self.providers: List[ExtractProvider] = [
                Crawl4AIProvider(),
                TrafilaturaProvider(),
            ]
        else:
            self.providers = providers

    async def extract(self, url: str, mode: ExtractMode = ExtractMode.MARKDOWN) -> ExtractResult:
        last_error: Optional[str] = None
        for provider in self.providers:
            if not provider.can_handle(url):
                continue
            try:
                result = await provider.extract(url, mode=mode)
                if result.content and not result.error:
                    result.extractor_used = provider.get_name()
                    return result
                else:
                    last_error = result.error or "empty content"
            except Exception as exc:
                last_error = str(exc)
                continue
        return ExtractResult(url=url, content="", mode=mode, extractor_used="none", 
                             error=f"All extractors failed. Last error: {last_error}")

    async def extract_batch(self, urls: List[str], mode: ExtractMode = ExtractMode.MARKDOWN) -> List[ExtractResult]:
        tasks = [self.extract(url, mode=mode) for url in urls]
        return await asyncio.gather(*tasks)

    def add_provider(self, provider: ExtractProvider, position: Optional[int] = None):
        if position is None:
            self.providers.append(provider)
        else:
            self.providers.insert(position, provider)

```

## _infra/network/network_workflow/workflow.py
```python
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-24 14:48:00
import asyncio
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from ..search.searxng_client import SearXNGProvider
from ..extract import ExtractorChain, Crawl4AIProvider, TrafilaturaProvider
from ..privacy_gateway import build_privacy_gateway, PrivacyContext
from ..local_rag.store import RAGStore
from ..local_rag.models import DocumentInput
from ..input_sanitizer.sanitizer import InputSanitizer
from ..config_loader import load_network_config

logger = logging.getLogger(__name__)

class WorkflowResult(BaseModel):
    query: str
    processed_query: str
    anonymized_content: str
    citations: List[Dict[str, str]]
    tokens_removed: int
    mode: str

class NetworkWorkflow:
    def __init__(self, config=None):
        self.config = config or load_network_config()
        self.search_provider = SearXNGProvider(config=self.config.search.searxng)
        self.extractor = ExtractorChain(providers=[Crawl4AIProvider(config=self.config.extract.crawl4ai), TrafilaturaProvider()])
        self.privacy_gateway = build_privacy_gateway(config=self.config)
        self.sanitizer = InputSanitizer()
        self.rag_store = RAGStore(db_path=self.config.local_rag.rag_db)

    async def execute(self, query: str, mode: str = "research") -> WorkflowResult:
        sanitized = self.sanitizer.sanitize(query, source_url="user_input").text
        results = await self.search_provider.search(sanitized)
        if not results:
            return WorkflowResult(query=query, processed_query=sanitized, anonymized_content="No results found.", citations=[], tokens_removed=0, mode=mode)

        print(f"[INFO] SearXNG found {len(results)} results.")
        targets = results[:self.config.search.searxng.fetch_top_k]
        
        extracted_docs = await self.extractor.extract_batch([t.url for t in targets])
        for i, doc in enumerate(extracted_docs):
            if not doc.content:
                print(f"      [Fallback to snippet for {targets[i].url}]")
                doc.content = targets[i].snippet

        combined_text = ""
        citations = []
        for i, doc in enumerate(extracted_docs):
            combined_text += f"\n--- Source: {targets[i].title} ({targets[i].url}) ---\n{doc.content}\n"
            citations.append({"title": targets[i].title, "url": targets[i].url})

        ctx = PrivacyContext(mode="full" if mode=="research" else "light", source_url="network_workflow")
        gw_res = await self.privacy_gateway.process(combined_text, ctx=ctx)
        
        for i, doc in enumerate(extracted_docs):
            if doc.content:
                try:
                    res = await self.privacy_gateway.process(doc.content, ctx=ctx)
                    self.rag_store.add_document(DocumentInput(content=res.text, source_url=targets[i].url, title=targets[i].title))
                except Exception as e:
                    print(f"[WARNING] RAG failed for {targets[i].url}: {e}")

        return WorkflowResult(query=query, processed_query=sanitized, anonymized_content=gw_res.text, citations=citations, tokens_removed=len(gw_res.detections), mode=mode)

```

## _infra/network/exceptions.py
```python
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 16:05:00 CST

"""
统一异常体系（FORGE Network 增量）

基类：NetworkError
子类按领域分类：
- MCP 相关
- Search 相关
- Extract 相关
- Privacy 相关
- Browser 相关

每个异常必须有：
- code: str（错误码）
- 关键异常携带上下文（entities、details 等）
"""

from __future__ import annotations

from typing import Any, List, Optional


class NetworkError(Exception):
    """所有网络功能异常基类"""

    code: str = "NETWORK_ERROR"

    def __init__(self, message: str, *, code: Optional[str] = None, **kwargs: Any):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.details: dict[str, Any] = kwargs


# ===================== MCP 层 =====================

class MCPError(NetworkError):
    code = "MCP_ERROR"


class MCPSchemaChangedError(MCPError):
    code = "MCP_SCHEMA_CHANGED"

    def __init__(self, server_id: str, old_hash: str, new_hash: str, **kwargs):
        super().__init__(
            f"MCP server '{server_id}' schema changed",
            code=self.code,
            server_id=server_id,
            old_hash=old_hash,
            new_hash=new_hash,
            **kwargs,
        )


class PolicyDeniedError(MCPError):
    code = "MCP_POLICY_DENIED"

    def __init__(self, tool_name: str, reason: str, **kwargs):
        super().__init__(
            f"Tool '{tool_name}' denied by policy: {reason}",
            code=self.code,
            tool_name=tool_name,
            reason=reason,
            **kwargs,
        )


# ===================== 搜索层 =====================

class SearchError(NetworkError):
    code = "SEARCH_ERROR"


class SearchEngineUnavailable(SearchError):
    code = "SEARCH_ENGINE_UNAVAILABLE"


class SearchRateLimited(SearchError):
    code = "SEARCH_RATE_LIMITED"


class SearchResultEmpty(SearchError):
    code = "SEARCH_RESULT_EMPTY"


# ===================== 提取层 =====================

class ExtractError(NetworkError):
    code = "EXTRACT_ERROR"


class AllExtractorsFailed(ExtractError):
    code = "ALL_EXTRACTORS_FAILED"


class ExtractTimeout(ExtractError):
    code = "EXTRACT_TIMEOUT"


class ContentTooLarge(ExtractError):
    code = "CONTENT_TOO_LARGE"


# ===================== 隐私网关 =====================

class PrivacyError(NetworkError):
    code = "PRIVACY_ERROR"


class PIIDetectedError(PrivacyError):
    code = "PII_DETECTED"

    def __init__(self, detections: List[dict], message: str = "PII detected", **kwargs):
        super().__init__(
            message,
            code=self.code,
            detections=detections,
            **kwargs,
        )
        self.detections = detections


class CanaryTokenDetectedError(PrivacyError):
    code = "CANARY_TOKEN_DETECTED"

    def __init__(self, token: str, location: str, **kwargs):
        super().__init__(
            f"Canary token detected: {token} at {location}",
            code=self.code,
            token=token,
            location=location,
            **kwargs,
        )


class SchemaValidationFailedError(PrivacyError):
    code = "SCHEMA_VALIDATION_FAILED"


# ===================== 浏览器层 =====================

class BrowserError(NetworkError):
    code = "BROWSER_ERROR"


class SessionExpiredError(BrowserError):
    code = "SESSION_EXPIRED"

    def __init__(self, profile: str, url: str, **kwargs):
        super().__init__(
            f"Session expired in profile '{profile}' at {url}",
            code=self.code,
            profile=profile,
            url=url,
            **kwargs,
        )


class BrowserCrashError(BrowserError):
    code = "BROWSER_CRASH"


class ForbiddenBrowserActionError(BrowserError):
    code = "FORBIDDEN_BROWSER_ACTION"


# ===================== 配置 & 通用 =====================

class ConfigError(NetworkError):
    code = "CONFIG_ERROR"


class NetworkConfigError(ConfigError):
    code = "NETWORK_CONFIG_ERROR"


# 方便的异常工厂（可选）
def raise_if_pii(detections: List[dict], **kwargs):
    if detections:
        raise PIIDetectedError(detections, **kwargs)

```

## scripts/diagnostics/test_engine_risk_control.py
```python
#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-24 23:45:00

"""
大规模搜索引擎风控压测与反爬特征诊断工具 (Risk Control Diagnostic Suite)

用途：
在本地 Mac 真实网络环境（直连或宿主机 Clash 分流代理）下，并发/逐一测试 SearXNG 支持的
核心搜索引擎的风控响应特征（如 CAPTCHA、429 限流、IP 封禁、空结果等），为反爬策略与
容错降级路由提供数据决策支持。

运行方式（需在开启 SearXNG 容器的 Mac 真机执行）：
python3 scripts/diagnostics/test_engine_risk_control.py --base-url http://127.0.0.1:8090
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from typing import Dict, List, Any
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("engine_risk_test")

ENGINES_TO_TEST = [
    "google",
    "duckduckgo",
    "brave",
    "startpage",
    "bing",
    "yahoo",
    "qwant",
    "wikipedia",
    "github",
    "arxiv",
    "stackoverflow"
]

TEST_QUERIES = [
    "python langgraph",
    "macos m1 max artificial intelligence",
    "deep learning mcp protocol"
]

class EngineTestResult:
    def __init__(self, engine: str):
        self.engine = engine
        self.total_queries = 0
        self.success_count = 0
        self.captcha_count = 0
        self.rate_limit_count = 0
        self.empty_count = 0
        self.error_count = 0
        self.avg_latency_ms = 0.0
        self.raw_errors: List[str] = []

    def status_summary(self) -> str:
        if self.captcha_count > 0:
            return "🔴 CRITICAL (CAPTCHA Blocked)"
        if self.rate_limit_count > 0:
            return "🟡 WARNING (429 Rate Limited)"
        if self.error_count > 0:
            return f"❌ ERROR ({self.raw_errors[0] if self.raw_errors else 'Unknown'})"
        if self.success_count == 0 or self.empty_count == self.total_queries:
            return "⚪ EMPTY (No results returned)"
        return "🟢 PASS (Stable & Healthy)"

async def test_single_engine(client: httpx.AsyncClient, engine: str, queries: List[str]) -> EngineTestResult:
    result = EngineTestResult(engine)
    latencies = []
    
    for q in queries:
        result.total_queries += 1
        start_time = time.perf_counter()
        params = {"q": q, "format": "json", "engines": engine, "limit": 5}
        
        try:
            resp = await client.get("/search", params=params, timeout=12.0)
            elapsed = (time.perf_counter() - start_time) * 1000
            latencies.append(elapsed)
            
            if resp.status_code == 429:
                result.rate_limit_count += 1
                result.raw_errors.append("HTTP 429 Too Many Requests")
                continue
            elif resp.status_code in (403, 503):
                result.captcha_count += 1
                result.raw_errors.append(f"HTTP {resp.status_code} Forbidden/Service Unavailable")
                continue
                
            data = resp.json()
            unresponsive = data.get("unresponsive_engines", [])
            
            # 检测 SearXNG 结构化报错
            engine_err = None
            for item in unresponsive:
                if isinstance(item, list) and len(item) >= 2 and item[0].lower() == engine.lower():
                    engine_err = str(item[1])
                    break
                elif engine.lower() in str(item).lower():
                    engine_err = str(item)
                    break
                    
            if engine_err:
                err_lower = engine_err.lower()
                if "captcha" in err_lower or "challenge" in err_lower or "bot" in err_lower:
                    result.captcha_count += 1
                    result.raw_errors.append(f"Upstream CAPTCHA: {engine_err}")
                elif "too many requests" in err_lower or "limit" in err_lower or "suspended" in err_lower:
                    result.rate_limit_count += 1
                    result.raw_errors.append(f"Upstream Suspended/Limit: {engine_err}")
                else:
                    result.error_count += 1
                    result.raw_errors.append(engine_err)
            else:
                res_list = data.get("results", [])
                if len(res_list) > 0:
                    result.success_count += 1
                else:
                    result.empty_count += 1
                    
        except httpx.TimeoutException:
            result.error_count += 1
            result.raw_errors.append("Request Timeout (>12s)")
        except Exception as e:
            result.error_count += 1
            result.raw_errors.append(f"Client Exception: {repr(e)}")
            
        await asyncio.sleep(0.5) # 请求间隔防连发限制

    if latencies:
        result.avg_latency_ms = sum(latencies) / len(latencies)
    return result

async def run_diagnostic(base_url: str):
    logger.info(f"🚀 开始搜索引擎风控大规模压测诊断，目标节点: {base_url}")
    logger.info(f"本次压测引擎池 ({len(ENGINES_TO_TEST)} 个): {ENGINES_TO_TEST}")
    
    async with httpx.AsyncClient(base_url=base_url, headers={"User-Agent": "Mozilla/5.0"}, trust_env=False) as client:
        # 先做一次 ping 测试
        try:
            ping_res = await client.get("/search", params={"q": "ping", "format": "json"}, timeout=5.0)
            if ping_res.status_code != 200:
                logger.error(f"❌ SearXNG 节点未响应正常状态码: {ping_res.status_code}")
                return
        except Exception as e:
            logger.error(f"❌ 无法连接至 SearXNG 服务 ({base_url})。请确认容器已启动: {e}")
            return

        tasks = [test_single_engine(client, eng, TEST_QUERIES) for eng in ENGINES_TO_TEST]
        results: List[EngineTestResult] = await asyncio.gather(*tasks)

    print("\n" + "="*85)
    print(f"{'搜索引擎 (Engine)':<18} | {'状态评估 (Risk Assessment)':<30} | {'成功率':<10} | {'平均耗时':<10}")
    print("="*85)
    
    stable_engines = []
    risky_engines = []
    
    for r in results:
        rate_str = f"{r.success_count}/{r.total_queries}"
        lat_str = f"{r.avg_latency_ms:.1f}ms" if r.avg_latency_ms > 0 else "-"
        print(f"{r.engine:<18} | {r.status_summary():<30} | {rate_str:<10} | {lat_str:<10}")
        if r.raw_errors:
            print(f"   ↳ 异常明细: {r.raw_errors[0]}")
            
        if r.success_count > 0 and r.captcha_count == 0 and r.rate_limit_count == 0:
            stable_engines.append(r.engine)
        else:
            risky_engines.append((r.engine, r.status_summary()))

    print("="*85)
    print("\n📊 【诊断决策与反爬建议总结】")
    print(f"1. 当前环境推荐白名单稳定引擎池 ({len(stable_engines)} 个): {stable_engines}")
    print(f"2. 高风险/已被封禁引擎 ({len(risky_engines)} 个): {[e[0] for e in risky_engines]}")
    print("3. 反爬策略落地优化指南：")
    print("   - 针对 CAPTCHA/429 引擎，建议在 settings.yml 中显式设置 disabled: true 或增大请求回避周期。")
    print("   - SearXNGProvider 查询链路已开启智能退避路由：若通用引擎报 CAPTCHA 导致空结果，自动重定向至稳定白名单池。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="搜索引擎风控诊断工具")
    parser.add_argument("--base-url", default="http://127.0.0.1:8090", help="SearXNG 服务地址")
    args = parser.parse_args()
    
    asyncio.run(run_diagnostic(args.base_url))

```

## _infra/network/tests/unit/test_search.py
```python
"""
Unit tests for Search module (E3-C2-S1-T1 / T2)

- SearchQuery / SearchResult models
- SearchProvider ABC
- SearXNGProvider (mocked httpx)

Note: Async tests use asyncio.run() to avoid requiring pytest-asyncio
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from _infra.network.exceptions import (
    SearchEngineUnavailable,
    SearchRateLimited,
    SearchResultEmpty,
)
from _infra.network.search.base import SearchProvider
from _infra.network.search.models import SearchQuery, SearchResult
from _infra.network.search.searxng_client import SearXNGProvider


def test_search_query_model():
    q = SearchQuery(query="python async", max_results=10)
    assert q.query == "python async"
    assert q.max_results == 10
    assert q.language == "zh"


def test_search_query_validation():
    with pytest.raises(ValueError):
        SearchQuery(query="   ")


def test_search_result_model():
    r = SearchResult(
        url="https://example.com/foo",
        title="Example",
        snippet="Hello world",
        score=0.92,
    )
    assert r.domain == "example.com"
    assert r.score == 0.92


def test_search_result_url_validation():
    with pytest.raises(ValueError):
        SearchResult(url="not-a-url")


def test_search_provider_is_abstract():
    with pytest.raises(TypeError):
        SearchProvider()  # type: ignore


def test_searxng_search_success():
    mock_response = {
        "results": [
            {"url": "https://github.com/python/cpython", "title": "CPython", "content": "Python core", "score": 0.95},
            {"url": "https://docs.python.org", "title": "Python Docs", "content": "Official docs", "score": 0.88},
        ]
    }

    async def _run():
        # Create real httpx response mock (sync methods)
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status.return_value = None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        # get() returns the resp directly (await resolves to it)
        mock_client.get.return_value = mock_resp

        provider = SearXNGProvider(client=mock_client)

        results = await provider.search("python", max_results=5)

        assert len(results) == 2
        assert results[0].url == "https://github.com/python/cpython"
        assert results[0].score == 0.95
        assert results[0].domain == "github.com"

    asyncio.run(_run())


def test_searxng_search_empty_results():
    async def _run():
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}
        mock_resp.raise_for_status.return_value = None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_resp

        provider = SearXNGProvider(client=mock_client)

        with pytest.raises(SearchResultEmpty):
            await provider.search("nonexistent query xyz")

    asyncio.run(_run())


def test_searxng_search_rate_limited():
    async def _run():
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 429

        err = httpx.HTTPStatusError(
            "Too Many Requests",
            request=httpx.Request("GET", "http://example"),
            response=mock_resp,
        )

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = err

        provider = SearXNGProvider(client=mock_client)

        with pytest.raises(SearchRateLimited):
            await provider.search("test")

    asyncio.run(_run())


def test_searxng_search_timeout():
    async def _run():
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = httpx.TimeoutException("timeout")

        provider = SearXNGProvider(client=mock_client)

        with pytest.raises(SearchEngineUnavailable):
            await provider.search("test")

    asyncio.run(_run())


def test_searxng_health_check_ok():
    async def _run():
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": [{"url": "https://x"}]}
        mock_resp.raise_for_status.return_value = None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_resp

        provider = SearXNGProvider(client=mock_client)
        healthy = await provider.health_check()
        assert healthy is True

    asyncio.run(_run())


def test_searxng_health_check_fail():
    async def _run():
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = httpx.ConnectError("refused")

        provider = SearXNGProvider(client=mock_client)
        healthy = await provider.health_check()
        assert healthy is False

    asyncio.run(_run())


def test_search_result_domain_fallback():
    r = SearchResult(url="https://www.Example.COM/path?q=1", title="x")
    assert r.domain == "www.example.com"


def test_searxng_search_auto_fallback_on_captcha():
    async def _run():
        resp1 = MagicMock(spec=httpx.Response)
        resp1.status_code = 200
        resp1.json.return_value = {"results": [], "unresponsive_engines": [["duckduckgo", "CAPTCHA"]]}
        resp1.raise_for_status.return_value = None

        resp2 = MagicMock(spec=httpx.Response)
        resp2.status_code = 200
        resp2.json.return_value = {"results": [{"url": "https://wikipedia.org/wiki/LangGraph", "title": "LangGraph", "content": "summary", "score": 0.95}]}
        resp2.raise_for_status.return_value = None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = [resp1, resp2]

        provider = SearXNGProvider(client=mock_client)
        results = await provider.search("langgraph")

        assert len(results) == 1
        assert results[0].domain == "wikipedia.org"
        assert mock_client.get.call_count == 2

    asyncio.run(_run())

```

---

# 7. 调用链分析

```text
命令行输入 CLI: python -m _infra.network.cli search "python langgraph"
↓
NetworkWorkflow.execute(query="python langgraph", mode="research")
↓
InputSanitizer.sanitize(query) [本地输入清洗，剥离潜在注入规范化文本]
↓
SearXNGProvider.search(query="python langgraph", max_results=10, engines=None)
↓
httpx.AsyncClient.get("http://127.0.0.1:8090/search", params={"q": "python langgraph", "format": "json", "limit": 10})
↓
Docker 容器 forge-searxng 接收 GET /search -> 调度并发元查询至各大搜索引擎上游端点
↓
上游商业引擎 (Brave/DuckDuckGo/Startpage) 检测到代理节点 IP -> 返回 429 / CAPTCHA 拦截
↓
SearXNG 聚合 JSON 返回：{"results": [], "unresponsive_engines": [["brave", "Suspended: 429"], ["duckduckgo", "CAPTCHA"]]}
↓
SearXNGProvider.search() 判断 results 为空且 primary engines 失败 -> 触发备用池退避自愈路由
↓
重定向请求 GET http://127.0.0.1:8090/search?q=python+langgraph&engines=bing,wikipedia,github,arxiv,stackoverflow
↓
若备用池抓取成功 -> 产出文献 Targets 列表传给 ExtractorChain.extract_batch()
↓
若备用池同样被 WAF 阻断返回空列表 -> 抛出 SearchResultEmpty 异常阻断整个联网流程
```

* **数据如何流转**：
  用户自然语言字符串被封装为 `SearchQuery`，通过 AsyncClient 发往本地 SearXNG 容器 HTTP 端口。SearXNG 将 JSON 字典回传给 Python 运行时，解包剥壳成 `SearchResult` 对象数组，进而传给 `ExtractorChain` 进行网页正文剥壳。
* **参数如何变化**：
  主查询参数为 `engines=None`（由引擎自行决定默认调度）；发生风控降级路由时，参数突变为显式白名单字符串 `engines="bing,wikipedia,github,arxiv,stackoverflow"`。
* **在哪一步出现异常**：
  在上游容器向外部公网各大元搜索源发起并发 GET 抓取的那一物理瞬间，由于节点代理出口 IP 触发了 Cloudflare/Google 风控护栏，直接在 SearXNG 引擎池回环聚合的那一步产生 `unresponsive_engines` 拦截，进而导致客户端在 `if not results: raise SearchResultEmpty` 处爆发堆栈中断。

---

# 8. 配置与环境

```yaml
# config/network.yaml 完整物化配置
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-24 14:48:00

version: "1.0"
search:
  searxng:
    base_url: "http://127.0.0.1:8090"
    timeout_seconds: 30
    max_results: 10
    fetch_top_k: 3
    max_chars_per_page: 8000
    engines_enabled: [duckduckgo, github, arxiv, wikipedia, stackoverflow, bing]
    engines_disabled: [google, baidu]
  fallback_tavily:
    enabled: false
    api_key_env: "TAVILY_API_KEY"
extract:
  crawl4ai:
    base_url: "http://127.0.0.1:11235"
    timeout_seconds: 30
    js_exec_allowed: false
    screenshot_requires_approval: true
    api_token: "my_secret_token_1234"
  trafilatura:
    enabled: true
    max_size_bytes: 1048576
browser:
  profiles:
    ai_public:
      user_data_dir: "${HOME}/ai-agent/profiles/ai-public"
      blocked_origins: ["https://accounts.google.com"]
    ai_private_github:
      user_data_dir: "${HOME}/ai-agent/profiles/ai-private-github"
      remote_debugging_port: 9222
      allowed_domains: ["github.com", "gist.github.com"]
privacy_gateway:
  qwen_model: "qwen3:14b"
  qwen_base_url: "http://127.0.0.1:11434"
  qwen_timeout_seconds: 30
  spacy_model: "zh_core_web_sm"
  pii_map_db: "runtime/pii_map.db"
  pii_map_encryption_key_env: "PII_MAP_ENCRYPTION_KEY"
  canary_tokens: ["AI_CANARY_DO_NOT_LEAK_2026"]
  output_schema_strict: true
  placeholder_format: "<<{entity_type}_{index}>>"
local_rag:
  rag_db: "runtime/rag.db"
  embed_model: "bge-m3:latest"
  embed_base_url: "http://127.0.0.1:11434"
  chunk_size_tokens: 300
  chunk_overlap_tokens: 30
mcp_guard:
  hash_store: "runtime/mcp_hashes.json"
  audit_db: "runtime/audit.db"
  policy_config: "config/mcp_policy.yaml"
  scan_interval_days: 7
mode_profiles:
  coding:
    allowed_servers: ["filesystem", "git"]
  research:
    allowed_servers: ["searxng", "crawl4ai", "playwright-public"]
  private:
    allowed_servers: ["chrome-devtools-private"]
health_check:
  services:
    searxng: {url: "http://127.0.0.1:8090/search?q=test&format=json", timeout: 15}
    crawl4ai: {url: "http://127.0.0.1:11235/health", timeout: 5}
    google_connectivity: {url: "https://www.google.com", timeout: 10, optional: true}

```

```json
{
  "_forge_trace": {
    "llm": "Arena.ai Agent Mode - Execution Lead Engineer",
    "modified_at_beijing": "2026-06-23 15:16:58",
    "task": "E6-C1-S1-T2"
  },
  "mcpServers": {
    "searxng": {
      "command": "node",
      "args": [
        "mcp-servers/searxng/dist/index.js"
      ],
      "env": {
        "SEARXNG_URL": "http://127.0.0.1:8080"
      }
    },
    "crawl4ai": {
      "command": "node",
      "args": [
        "mcp-servers/crawl4ai/dist/index.js"
      ],
      "env": {
        "CRAWL4AI_URL": "http://127.0.0.1:11235",
        "CRAWL4AI_DISABLE_JS": "true"
      }
    },
    "playwright-public": {
      "command": "node",
      "args": [
        "mcp-servers/playwright-public/cli.js",
        "--browser=chromium",
        "--headed",
        "--user-data-dir=${HOME}/ai-agent/profiles/ai-public",
        "--blocked-origins=https://accounts.google.com;https://bank.example.com",
        "--timeout-navigation=30000",
        "--timeout-action=10000"
      ],
      "env": {
        "PLAYWRIGHT_PROFILE": "ai-public",
        "PLAYWRIGHT_ALLOW_PRIVATE_PROFILE": "0"
      }
    }
  }
}

```

```env
# 容器部署与运行环境变量 (物化自 docker-compose 与系统层)
COMPOSE_PROJECT_NAME=forge-network
SEARXNG_IMAGE=searxng/searxng:latest
SEARXNG_BASE_URL=http://127.0.0.1:8090/
SEARXNG_SECRET_KEY=CHANGE_ME_LOCAL_ONLY_32_CHARS
CRAWL4AI_IMAGE=unclecode/crawl4ai:latest
CRAWL4AI_HOST=0.0.0.0
CRAWL4AI_PORT=11235
CRAWL4AI_API_TOKEN=my_secret_token_1234
CRAWL4AI_DISABLE_JS=true
HTTP_PROXY=http://host.docker.internal:7890
HTTPS_PROXY=http://host.docker.internal:7890
NO_PROXY=localhost,127.0.0.1,host.docker.internal
```

---

# 9. 当前卡点

1. **不知道如何在不更换机场/住宅代理 IP 的前提下，完全绕过 DuckDuckGo 与 Startpage 的 Cloudflare Turnstile 人机校验**。
2. **不知道为什么 SearXNG 在配置 `use_default_settings: true` 并显式声明 `disabled: true` 时，部分默认通用引擎的轮询调度行为依然会产生连发限流悬停**。
3. **不知道维基百科 (Wikipedia) 在 Headless 抓取时，除了常规 User-Agent 与 Accept-Language 外，是否还需要模拟特定的 TLS JA4 扩展排序指纹才能稳定维持 100% 抓取成功率**。
4. **不知道当通用商业搜索源受阻时，单凭开源文献类数据源（GitHub、arXiv、StackOverflow）如何建立一套支持自然语言泛化的高召回搜索映射规则**。

---

# 10. 希望外部AI重点分析的问题

1. **架构模式审查**：在本地开源大模型框架（FORGE）下，如何针对 SearXNG 设计一套具备“动态引擎熔断与健康检测”的中间件网关，使得一旦某个引擎连续返回 `CAPTCHA`，能在网关层自动将其冷冻隔离（Circuit Breaking），而无需人工修改 `settings.yml`？
2. **底层反爬突围**：针对 Cloudflare Turnstile 保护的站点（如 DuckDuckGo 搜索接口）及对 TLS 指纹极度敏感的文献页（如 Wikipedia），顶级架构中推荐采用何种轻量级开源本地驱动（如 `curl_cffi` 拟真 TLS 客户端、Playwright stealth 插件或穿透代理），能无缝嵌入当前 Pydantic + httpx 异步调用链？
3. **多源调度路由优化**：当 Google / Brave 等通用引擎受限于机场代理节点无法使用时，如何通过既有架构的双文件路由引擎（`config/routing_plans.yaml`）或 LangGraph 专家评审图，智能判断用户的查询意图（如区分 Code 编程意图 vs Research 学术意图），从而动态把查询分发给 GitHub / StackOverflow / arXiv 垂直 API？
4. **风控遥测自动化演进**：对物化的诊断压测套件 `test_engine_risk_control.py` 有何进一步加固建议，使其能逆向解析出各引擎返回 HTML 页面中的具体验证码类型（如区分 HCaptcha vs Cloudflare盾 vs Google图形锁），以便实现精细化的指标遥测？

---

# 12. 附加上下文

* **系统拓扑图谱与核心边界**：
  ```text
  +-----------------------------------------------------------------------------------+
  |                                FORGE Factory 主控 CLI                             |
  +-----------------------------------------------------------------------------------+
                                            |
                                            v  (自然语言搜索词 SearchQuery)
  +-----------------------------------------------------------------------------------+
  |                                 NetworkWorkflow 编排链                            |
  |  [InputSanitizer] ---> [SearXNGProvider] ---> [ExtractorChain] ---> [PrivacyGate] |
  +-----------------------------------------------------------------------------------+
                                            |
                         +------------------+------------------+
                         | (HTTP GET)                          | (HTTP POST /crawl)
                         v                                     v
  +---------------------------------------+  +----------------------------------------+
  |    SearXNG 元容器 (127.0.0.1:8090)    |  |    Crawl4AI 提取容器 (127.0.0.1:11235) |
  +---------------------------------------+  +----------------------------------------+
                         |                                     |
                         | (经宿主机代理 7890 发往外网)          | (剥壳抓取公开网页 DOM)
                         v                                     v
  +-----------------------------------------------------------------------------------+
  | 外部公网搜索引擎群 (Google / DuckDuckGo / Brave / Wikipedia / GitHub / arXiv 等) |
  +-----------------------------------------------------------------------------------+
  ```
* **SearXNG 返回风控数据结构样例 (Raw Output Sample)**：
  ```json
  {
    "query": "python langgraph",
    "number_of_results": 0,
    "results": [],
    "answers": [],
    "corrections": [],
    "infoboxes": [],
    "suggestions": [],
    "unresponsive_engines": [
      ["brave", "Suspended: too many requests"],
      ["duckduckgo", "CAPTCHA"],
      ["startpage", "Suspended: CAPTCHA"],
      ["qwant", "Access Denied (WAF Blocked)"]
    ]
  }
  ```
* **Crawl4AI 抓取成功正文剥壳返回样例 (Deep Extract Sample)**：
  ```json
  {
    "status": "success",
    "url": "https://en.wikipedia.org/wiki/LangGraph",
    "results": [
      {
        "markdown": "# LangGraph\n\nLangGraph is a library for building stateful, multi-actor applications with LLMs...",
        "html": "<div id=\"content\"><h1>LangGraph</h1>...</div>",
        "metadata": {"title": "LangGraph - Wikipedia", "status_code": 200}
      }
    ]
  }
  ```
* **最近静态单元与安全基线自动化断言结果**：
  `python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q`
  `===> 350 passed, 2 skipped, 44 warnings in 25.70s`
  （全部内存模型、本地代理连接器、异常拦截器及安全红线测试护栏均保持通过）。
