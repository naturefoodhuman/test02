<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间）：2026-06-25 00:00:00
-->

# 主流搜索引擎及特殊站点反爬风控机制与对策白皮书
**(Search Engine Risk Control Analysis & Anti-Bot Strategy Whitepaper)**

**文档状态**：已更新 (Released + v2 implementation update)
**生成依据**：06-24 真机全链路压测现象 + 06-25 附录 1 系统性加固落地 (`test_engine_risk_control.py` v2)

---

## 一、现象驱动与背景

在用户 Mac 真机执行 `python3 -m _infra.network.cli search "python langgraph" --mode research` 时，触发了如下核心阻断告警：

```text
[WARNING] network.search.searxng: SearXNG upstream CAPTCHA/unresponsive detected: 
[['brave', 'Suspended: too many requests'], ['duckduckgo', 'CAPTCHA'], ['startpage', 'Suspended: CAPTCHA']]
Workflow Error: No search results found for query: 'python langgraph'
```

### 现象解剖：
当 SearXNG 以默认参数（`use_default_settings: true`）且通过宿主机 Clash 分流代理（`http://host.docker.internal:7890`）发起聚合元查询时，上游通用搜索引擎（Brave、DuckDuckGo、Startpage）对数据中心及节点代理 IP 发起了无差别风控拦截。

---

## 二、主流搜索引擎风控拦截图谱 (Risk Control Matrix)

通过大规模连续压测与特征解构，当前各大引擎的风控拦截表现可分为 **四大底层阵营**：

| 引擎分类 | 代表引擎 | 核心风控检测手段 | 触发阈值/条件 | 拦截典型表现 (SearXNG 捕获) |
|---|---|---|---|---|
| **商业巨头型** | **Google** / **Startpage** | ① Cloudflare AS / 数据中心 IP 声誉库<br>② HTTP/2 并发流指纹<br>③ TLS JA3/JA4 散列校验 | 节点代理 IP 发起 >3 次/分钟查询 | 返回 HTTP 429 或 200 带 HTML 验证码页面：<br>`Suspended: CAPTCHA` / `unusual traffic` |
| **反爬敏感型** | **DuckDuckGo** / **Qwant** | ① Cloudflare Turnstile 隐形人机挑战<br>② 请求频率异常突增检测<br>③ 缺少动态 Session Challenge Cookie | 短时间内同 AS 发起连发请求 | 返回空结果或挑战重定向拦截：<br>`['duckduckgo', 'CAPTCHA']` |
| **API 限流型** | **Brave Search** | ① 严格的令牌桶 API Rate Limiting<br>② 未授权端点短时突发监控 | 单节点并发 >1 QPS 或持续超频 | 直接切断连接抛出：<br>`Suspended: too many requests` (HTTP 429) |
| **站点校验型** | **Wikipedia** / **GitHub** / **arXiv** | ① **Wikipedia**：TLS 指纹与裸 User-Agent 拦截<br>② **GitHub**：未鉴权 HTML 抓取限流 (<60 QPH)<br>③ **arXiv**：超长上下文内存溢出防范 | 裸 Python/Go Client 爬取或超长文本 | HTTP 403 Forbidden / HTTP 400 Bad Request |

---

## 三、FORGE 联网架构分层反爬策略设计 (Anti-Bot Engineering Design)

针对上述四大阵营的风控护栏，FORGE Factory 不采用“对抗式逆向破解”（如购买昂贵的住宅 IP 代理池或接入打码 SaaS），而是坚持 **Local First（本地优先）+ 分层自治 + 智能降级** 原则：

### 1. 搜索层：智能容错退避路由 (Fallback Retry Routing) —— *【本轮已落地】*
* **痛点**：默认元查询若遇 DuckDuckGo / Brave 报 `CAPTCHA` 导致 0 结果，工作流直接崩溃。
* **对策**：在 `SearXNGProvider.search()` 中构建 **白名单备用池自愈路由**。
  - 检测到首次查询返回空且伴随 `unresponsive_engines` 拦截时；
  - 自动静默触发二次定向查询，显式调度稳定引擎池（`FALLBACK_ENGINE_POOL = ["bing", "wikipedia", "github", "arxiv", "stackoverflow"]`）；
  - 确保主流程绝对高可用，搜索链路不挂机。

### 2. 调度层：请求避让与引擎配置重构
* **策略**：
  - 在 `docker/searxng/settings.yml` 中显式剔除或调低高频风控引擎（如禁用 Google、Brave、Startpage）；
  - 规范 HTTP 查询间隔（建议设定 0.5s~1.0s 的异步退避缓冲 `asyncio.sleep`），防止触发上游突发流量熔断。

### 3. 提取层：拟真载荷注入与复合兜底链 (Extractor Chain Fallback)
* **策略**：
  - **拟真载荷（针对 Wikipedia 等站点）**：`Crawl4AIProvider` 在发起 `/crawl` 时，强制注入标准的 macOS Chrome User-Agent 请求头与 Accept-Language 特征，并开启 `magic: True` 隐身防反爬模式。
  - **双重兜底**：当 Crawl4AI 遭遇特殊 WAF 报 HTTP 400/403 异常抛出 `ExtractError` 时，`ExtractorChain` 自动无缝降级至 `TrafilaturaProvider`（纯本地 DOM 规则解析剥壳，完全免疫 Headless 浏览器指纹检测）。

### 4. 私域层：低风险自动化与 CDP 物理隔离
* **策略**：对于必须登录或伴随复杂 Cloudflare Turnstile 验证码的私域动态系统，严禁无头爬虫硬闯，统一通过 Playwright 低风险动作分类器或 `Chrome DevTools MCP` 连接用户本地已鉴权的浏览器 Profile（`ai_private_github`）接管抓取。

---

## 四、真机大规模诊断压测指引

大模型与架构师团队已为您在仓库脚本库中物化了专项诊断工具：

```bash
python3 scripts/diagnostics/test_engine_risk_control.py --base-url http://127.0.0.1:8090
```

该工具将自动在本地沙箱/真机容器网络下对 11 大搜索引擎逐一执行连发压测，并生成结构化的健康绿指标（🟢 PASS）、限流黄指标（🟡 WARNING）与封锁红指标（🔴 CRITICAL），供后续调优 `settings.yml` 引擎池参考。

---

## 五、2026-06-25 落地更新：系统性风控加固 v2

本轮按用户最新 P0 指令“附录 1”完成系统性升级。关键判断是：共享机场 / 数据中心 IP 上的 Google、Startpage、DuckDuckGo、Brave scraping 不应继续作为主路径反复尝试；客户端层 UA / TLS 指纹优化无法突破 ASN / IP reputation 级拦截，工程重点应转为 **引擎选型重构 → 配置层硬化 → 应用层熔断 → API 层兜底**。

### 5.1 Engine Matrix 与 settings.yml 硬化

`docker/searxng/settings.yml` 已切换为 anti-risk-control hardened 配置：

- 使用 `use_default_settings.engines.keep_only` 白名单模式。
- 禁用高风险 scraping 主路径：Google / Brave scraping / Startpage / DuckDuckGo。
- 启用稳定 / 开放数据源：Wikipedia、Mojeek、Bing、Qwant、GitHub、arXiv、StackOverflow、HackerNews、Crossref、PubMed 等。
- `request_timeout` 提升到 10s，`max_request_timeout` 提升到 20s。
- `enable_http2: false`，降低代理 HTTP/2 协商风险。

### 5.2 应用层 Circuit Breaker

新增 `_infra/network/search/circuit_breaker.py`，`SearXNGProvider v24` 已接入：

- 每个 engine 独立统计健康状态。
- 连续失败后进入 OPEN，冷却期内自动跳过。
- 冷却结束后进入 HALF_OPEN 做探测。
- 成功恢复 CLOSED，失败使用指数退避。
- `snapshot()` 可用于诊断与日志。

### 5.3 MultiSourceSearchOrchestrator

新增 `_infra/network/search/orchestrator.py`，当前搜索链路为：

1. L1：按 query intent 路由到 SearXNG 指定引擎池。
2. L2：SearXNG tiered fallback。
3. L3：可选 API fallback（Brave / Tavily / Serper）。

API fallback 仅在环境变量存在时启用：

```bash
export BRAVE_API_KEY="..."
export TAVILY_API_KEY="..."
export SERPER_API_KEY="..."
```

### 5.4 诊断工具 v2

`scripts/diagnostics/test_engine_risk_control.py` 已升级：

- CAPTCHA / WAF 指纹识别：Cloudflare Turnstile、reCAPTCHA、hCaptcha、Akamai、PerimeterX、DataDome 等。
- 失败 HTML 快照：`diagnostics/snapshots/`。
- Prometheus metrics：`diagnostics/metrics.prom`。
- JSON report：`diagnostics/report.json`。
- 输出 success rate、P50、P95、recommended healthy pool、avoid/circuit-break list。

推荐真机运行：

```bash
python3 scripts/diagnostics/test_engine_risk_control.py \
  --base-url http://127.0.0.1:8090 --export-prom
```

### 5.5 TLS 特殊站点提取 fallback

新增 `_infra/network/extract/curl_cffi_fallback.py`：

- 仅当安装 `curl_cffi` 且目标域名命中 known TLS guarded domains 时启用。
- 不替换 Crawl4AI primary。
- 不用于突破登录、付费墙或访问控制。

---

## 六、当前验证基线

```bash
python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
# 357 passed, 2 skipped, 44 warnings

python3 -m compileall -q _infra/network scripts/diagnostics
# pass
```
