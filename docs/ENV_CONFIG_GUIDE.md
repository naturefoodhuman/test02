<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-08-05 13:20:00
-->

# FORGE Environment Config Guide

## 为什么有两个 `.env`

当前工厂历史上存在两个本地环境文件：

```text
.env
_infra/.env
```

推荐新规则：

- 根目录 `.env`：运行时主配置，供 `scripts/forge-start.sh`、`_infra/smart_proxy.py`、`_infra/nim_proxy.py`、Network secrets loader 使用。
- `_infra/.env`：历史 LiteLLM 启动脚本使用的 legacy 凭据文件，只保留 `GLM_API_KEY`、`DEEPSEEK_API_KEY`、`QWEN_API_KEY`、`ANTHROPIC_AUTH_TOKEN` 等必要密钥；不要放 `FORGE_*` / `NIM_PROXY_*` 调参项。

`_infra/start-litellm.sh` 仍读取 `_infra/.env`，这是历史原因；`smart_proxy.py` 和 `forge-start.sh` 以根目录 `.env` 为主。

## 你当前配置中需要修正的高风险点

### 1. Markdown 污染 URL

聊天工具可能把 URL 变成：

```text
[http://127.0.0.1:4010/v1](http://127.0.0.1:4010/v1)
```

实际 `.env` 必须是纯 URL：

```bash
NIM_PROXY_BASE_URL="http://127.0.0.1:4010/v1"
NETWORK_SEARCH_API_PROXY="http://127.0.0.1:7890"
```

同理，`~/.cc-connect/config.toml` 里的：

```toml
ANTHROPIC_BASE_URL = "http://127.0.0.1:4000"
OPENAI_BASE_URL = "http://127.0.0.1:4000/v1"
```

也必须是纯 URL。

### 2. 重复参数冲突

你贴的根 `.env` 中 `FORGE_REMOTE_MAX_CONCURRENCY` 出现两次：

```bash
FORGE_REMOTE_MAX_CONCURRENCY=2
...
FORGE_REMOTE_MAX_CONCURRENCY=5
```

如果用 shell `source .env`，后者覆盖前者；如果用 Python dotenv loader 且“不覆盖已存在变量”，第一次可能生效。这会导致启动方式不同、参数不同。

建议只保留一个：

```bash
FORGE_REMOTE_MAX_CONCURRENCY=5
```

开启 NIM sidecar 后，per-key 并发由 sidecar 管，Smart Proxy 的 `FORGE_REMOTE_MAX_CONCURRENCY` 是总并发保险阀。2 个 key × 每 key并发 2 时，总并发 4；设 5 可以接受，sidecar 会排队。

### 3. 重复但相同的参数

`FORGE_CTX_SOFT_TOKENS`、`FORGE_REMOTE_TOOL_SELECTION`、`FORGE_REMOTE_SELECTOR_PORT` 重复但值相同，短期不坏，但建议只保留一次，降低排错成本。

## 推荐根 `.env` NIM 段

```bash
FORGE_USE_NIM_PROXY=1
NIM_PROXY_HOST="127.0.0.1"
NIM_PROXY_PORT=4010
NIM_PROXY_BASE_URL="http://127.0.0.1:4010/v1"
NIM_PROXY_API_KEY="nim-proxy-local"

NVIDIA_API_KEY_1="..."
NVIDIA_API_KEY_2="..."

NIM_PROXY_PER_KEY_RPM=35
NIM_PROXY_PER_KEY_CONCURRENCY=2
NIM_PROXY_DEFAULT_COOLDOWN_SECONDS=300
NIM_PROXY_RETRY_AFTER_CAP_SECONDS=900
NIM_PROXY_QUEUE_TIMEOUT_SECONDS=900

NIM_PRIMARY_MODEL="z-ai/glm-5.2"
NIM_PROXY_ENABLE_FALLBACK=0
NIM_FALLBACK_MODEL="deepseek-ai/DeepSeek-V4-Pro"

FORGE_CTX_SOFT_TOKENS=32000
FORGE_REMOTE_TOOL_SELECTION=1
FORGE_REMOTE_SELECTOR_PORT=8080
FORGE_TOOL_SELECTION_MAX=8
FORGE_TOOL_SCHEMA_BYTE_BUDGET=32768
FORGE_REMOTE_MAX_CONCURRENCY=5
```

## 一键审计

```bash
make env-config-audit
```

检查项：

- `.env` / `_infra/.env` 重复冲突；
- URL 是否被 Markdown 污染；
- `FORGE_USE_NIM_PROXY=1` 时是否存在 `NVIDIA_API_KEY_1..`；
- `NIM_PROXY_BASE_URL` 是否看起来像 `/v1` base URL；
- 高风险 RPM 配置提醒。

如果 audit 失败，先修 `.env`，再运行：

```bash
bash scripts/forge-start.sh
```
