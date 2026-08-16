<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-08-16 13:30:00
-->

# NVIDIA NIM Proxy Runbook

## 目标

在零付费、自用 2–3 个 NVIDIA NIM key 的前提下，让 Claude Code / Feishu Bot / Smart Proxy 不再裸打 NVIDIA NIM，降低 429、挂起、连续重试导致的锁定风险。

本仓库新增一个本地 OpenAI-compatible sidecar：

```text
_infra/nim_proxy.py
```

默认监听：

```text
http://127.0.0.1:4010/v1/chat/completions
```

Smart Proxy 仍然对客户端暴露：

```text
http://127.0.0.1:4000/v1/messages
```

当设置：

```bash
export FORGE_USE_NIM_PROXY=1
```

Smart Proxy 会把 NVIDIA remote routes 改写到本地 NIM Proxy。

---

## 环境变量

真实 key 只能放本机 `.env` 或 shell profile，禁止提交。

```bash
export NVIDIA_API_KEY_1="nvapi-..."
export NVIDIA_API_KEY_2="nvapi-..."
# 可选，建议最多 3 个自用 key
# export NVIDIA_API_KEY_3="nvapi-..."

export FORGE_USE_NIM_PROXY=1
export NIM_PROXY_HOST="127.0.0.1"
export NIM_PROXY_PORT=4010
export NIM_PROXY_BASE_URL="http://127.0.0.1:4010/v1"
export NIM_PROXY_API_KEY="nim-proxy-local"

export NIM_PROXY_PER_KEY_RPM=35
export NIM_PROXY_PER_KEY_CONCURRENCY=1
export NIM_PROXY_DEFAULT_COOLDOWN_SECONDS=300
export NIM_PROXY_RETRY_AFTER_CAP_SECONDS=900
export NIM_PROXY_QUEUE_TIMEOUT_SECONDS=900
export NIM_PROXY_READ_TIMEOUT_SECONDS=360
export NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS=600
export NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST=1
export NIM_PROXY_SESSION_AFFINITY=0
export FORGE_REMOTE_MAX_CONCURRENCY=1
export FORGE_CTX_SOFT_TOKENS=12000
export FORGE_CTX_KEEP_RECENT_TURNS=4
export FORGE_CTX_TRUNC_TOOL_RESULT_CHARS=800

export NIM_PRIMARY_MODEL="z-ai/glm-5.2"
export NIM_PROXY_ENABLE_FALLBACK=0
export NIM_FALLBACK_MODEL="deepseek-ai/DeepSeek-V4-Pro"

export FORGE_AUTO_CONTINUE_ON_API_ERROR=1
export FORGE_AUTO_CONTINUE_MAX_ATTEMPTS=1
export FORGE_AUTO_CONTINUE_DEFAULT_WAIT_SECONDS=60
export FORGE_AUTO_CONTINUE_MAX_WAIT_SECONDS=300
export FORGE_AUTO_CONTINUE_NO_OUTPUT_TIMEOUT_SECONDS=900
export FORGE_AUTO_CONTINUE_TIMEOUT_WAIT_SECONDS=5
export FORGE_AUTO_CONTINUE_CONTEXT_LIMIT_TOKENS=902752
export FORGE_AUTO_CONTINUE_STATUS_CODES="*"
export FORGE_AUTO_CONTINUE_PARTIAL_OUTPUT=1
export FORGE_REQUEST_EVENT_LOG_PATH="/tmp/forge_request_events.jsonl"
FORGE_SMART_PROXY_READ_TIMEOUT_SECONDS=900
FORGE_UPSTREAM_COMBINED_LIMIT_TOKENS=202749
FORGE_UPSTREAM_COMBINED_SAFETY_TOKENS=2048
FORGE_UPSTREAM_COMBINED_GUARD_ENABLED=1
```

如需同级 fallback：

```bash
export NIM_PROXY_ENABLE_FALLBACK=1
```

---

## 启动顺序

推荐：直接用全量启动脚本。

```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
export FORGE_USE_NIM_PROXY=1
# .env 中已配置 NVIDIA_API_KEY_1/2 时不需要重复 export key
bash scripts/forge-start.sh
```

`forge-start.sh` 会在启动 Smart Proxy 之前自动：

1. 加载本地 `.env`；
2. 检查 `NVIDIA_API_KEY_1..10` 至少有一个；
3. 停止旧的 4010 进程；
4. 启动 `scripts/start-nim-proxy.sh`；
5. 等待 `http://127.0.0.1:4010/healthz` 就绪；
6. 再启动 4000 Smart Proxy。

手动启动 sidecar 也可用：

```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
make run-nim-proxy
# 或 bash scripts/start-nim-proxy.sh
```

如需单独调试 Smart Proxy，再开 Terminal 2：

```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
export FORGE_USE_NIM_PROXY=1
export NIM_PROXY_API_KEY="nim-proxy-local"
python3 _infra/smart_proxy.py
```

客户端仍然只连接 Smart Proxy：

```text
http://127.0.0.1:4000/v1/messages
```

---

## Smoke test

```bash
make nim-proxy-test
curl http://127.0.0.1:4010/healthz
curl http://127.0.0.1:4010/stats
```

### 自动诊断脚本

后续排查不要再手工复制多段命令。统一使用：

```bash
# 当前链路快照：采集 4000/4010 状态、关键配置、日志尾部并自动分类根因
make forge-nim-chain-snapshot

# 当前链路观察窗口：默认观察 10 分钟，每 15 秒采样一次；适合 Claude Code 卡住时运行
DURATION=600 INTERVAL=15 make forge-nim-chain-watch

# 当前配置下，仅跑 4010/4000 最小 non-stream 探针
make forge-nim-diagnostic

# 实验 A：不启用 fallback；临时把 NIM read timeout 拉到 300s、wall timeout 拉到 360s。
# 诊断脚本只快速重启 4010 NIM sidecar 和 4000 Smart Proxy，跳过 forge-start 全量本地模型自检，避免测试开始前卡住。
# 随后自动跑 4010/4000 探针，并把脱敏产物推送到 diagnostics/* 分支。
make forge-nim-timeout-a

# VS Code 固定窗口观测：脚本会打印 TRACE 句子；你在 VS Code 发出后立刻回终端按 Enter，脚本自动采样，不再等待 UI 返回
WATCH_SECONDS=1500 INTERVAL=15 make forge-nim-vscode-watch
```

脚本输出末尾会包含：

```text
DIAG_OUTPUT_DIR=...
DIAG_TARBALL=...
PUSHED_BRANCH=diagnostics/forge-nim-...
```

把 `PUSHED_BRANCH` 发给排查方即可；完整脱敏证据在该分支中。如果探针已经跑完但 artifact push 失败，不要重跑慢探针，可直接执行：

```bash
DIAG_DIR=/private/tmp/forge_nim_diag_YYYYMMDD_HHMMSS make forge-nim-push-existing
```

然后把新的 `PUSHED_BRANCH` 发给排查方。

若实验 A 返回的是快速 `HTTP 404`（不是 120/300 秒 ReadTimeout），说明当前要先判断 NVIDIA 上游是否仍接受 `z-ai/glm-5.2`。执行：

```bash
make forge-nim-upstream-probe
```

该命令会直接用本机 `NVIDIA_API_KEY_1..` 调 NVIDIA `/v1/models` 和 `/v1/chat/completions`，只上传脱敏结果。

若 90 秒直连也只是 read timeout，但 `/v1/models` 确认 `z-ai/glm-5.2` 存在，可再执行单 key 长等待探针，避免两个 key 串行等待过久：

```bash
make forge-nim-upstream-long
```

默认参数是 `DIRECT_TIMEOUT=360 DIRECT_KEY_LIMIT=1`。

若确认 GLM-5.2 最小 direct 请求会在 360s 内返回，但速度约数分钟，可在“不启用 fallback”的前提下验证慢速工作档：

```bash
# 应用 GLM 慢速无 fallback profile，快速重启 4010/4000，跑 4010 与 4000 最小 non-stream smoke。
# 预计耗时约 8-12 分钟。
make forge-nim-glm-slow-smoke

# VS Code 固定窗口观测；脚本打印 TRACE 后，你在 VS Code 发出并立刻回终端按 Enter。
# 不预跑 curl smoke，避免测试前额外等待。
WATCH_SECONDS=1800 INTERVAL=15 make forge-nim-vscode-glm-slow-watch
```

`glm-slow` profile 固定保持 `NIM_PROXY_ENABLE_FALLBACK=0`，并设置：`NIM_PROXY_READ_TIMEOUT_SECONDS=360`、`NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS=600`、`FORGE_REMOTE_MAX_CONCURRENCY=1`、`NIM_PROXY_PER_KEY_CONCURRENCY=1`、`FORGE_CTX_SOFT_TOKENS=12000`、`FORGE_CTX_KEEP_RECENT_TURNS=4`、`FORGE_CTX_TRUNC_TOOL_RESULT_CHARS=800`。

最小 OpenAI-compatible 请求：

```bash
curl http://127.0.0.1:4010/v1/chat/completions \
  -H "Authorization: Bearer nim-proxy-local" \
  -H "Content-Type: application/json" \
  -d '{"model":"z-ai/glm-5.2","messages":[{"role":"user","content":"ping"}],"stream":false,"max_tokens":64}'
```

---

## Dashboard / 前端页面

当前仓库内置的是轻量 Python sidecar：`_infra/nim_proxy.py`。它没有 HTML dashboard；可视状态通过 JSON 端点查看：

```bash
curl http://127.0.0.1:4010/stats
make nim-proxy-tuning
```

你提到的 `miztertea/nim-proxy` 上游项目自带 Dashboard。若单独部署上游 Docker，它的页面在：

```text
http://localhost:8000/
```

首次打开会进入 setup wizard，后续用它生成的 `npk_...` client key 作为 OpenAI-compatible API key。

本仓库这版没有直接 vendor 上游 Rust dashboard，原因是：

- 先保持工厂内依赖最少，便于 `forge-start.sh` 一键启动；
- 先满足 key pool、cooldown、route rewrite、tuning 的核心限流目标；
- 如后续你明确要上游 dashboard，可把 `NIM_PROXY_BASE_URL` 切到上游 `http://127.0.0.1:8000/v1`，Smart Proxy 无需大改。


---


### Auto-continue for Claude Code / Feishu API Error

不要用 UI 自动输入来“发送继续”。最佳实践是在 Smart Proxy 层处理：当 NIM sidecar 在**尚未向客户端输出任何模型内容**之前返回瞬时 API Error（所有非上下文超限 API/network/timeout 错误（默认 `FORGE_AUTO_CONTINUE_STATUS_CODES="*"`））时，Smart Proxy 按 `Retry-After` 等待；没有 `Retry-After` 时默认等待 `FORGE_AUTO_CONTINUE_DEFAULT_WAIT_SECONDS=60`；等待上限 `FORGE_AUTO_CONTINUE_MAX_WAIT_SECONDS=300`；然后重放同一请求一次。这样对 Claude Code for VS Code、Claude Code 终端、cc-connect/飞书都生效，也不会依赖 GUI 自动化。

```bash
FORGE_AUTO_CONTINUE_ON_API_ERROR=1
FORGE_AUTO_CONTINUE_MAX_ATTEMPTS=1
FORGE_AUTO_CONTINUE_DEFAULT_WAIT_SECONDS=60
FORGE_AUTO_CONTINUE_MAX_WAIT_SECONDS=300
FORGE_AUTO_CONTINUE_NO_OUTPUT_TIMEOUT_SECONDS=900
FORGE_AUTO_CONTINUE_TIMEOUT_WAIT_SECONDS=5
FORGE_AUTO_CONTINUE_STATUS_CODES="*"
FORGE_AUTO_CONTINUE_CONTEXT_LIMIT_TOKENS=902752
FORGE_AUTO_CONTINUE_PARTIAL_OUTPUT=1
FORGE_REQUEST_EVENT_LOG_PATH="/tmp/forge_request_events.jsonl"
FORGE_SMART_PROXY_READ_TIMEOUT_SECONDS=900
FORGE_UPSTREAM_COMBINED_LIMIT_TOKENS=202749
FORGE_UPSTREAM_COMBINED_SAFETY_TOKENS=2048
FORGE_UPSTREAM_COMBINED_GUARD_ENABLED=1
FORGE_REQUEST_EVENT_LOG_INCLUDE_TEXT=0
FORGE_SMART_PROXY_READ_TIMEOUT_SECONDS=900
FORGE_UPSTREAM_COMBINED_LIMIT_TOKENS=202749
FORGE_UPSTREAM_COMBINED_SAFETY_TOKENS=2048
FORGE_UPSTREAM_COMBINED_GUARD_ENABLED=1
```


`FORGE_AUTO_CONTINUE_NO_OUTPUT_TIMEOUT_SECONDS=900` 是无真实输出 watchdog：如果 15 分钟没有任何 text/tool_call 输出，Smart Proxy 会取消当前 upstream HTTP 请求（关闭本地到 4010/NVIDIA 的连接；不会向 NVIDIA 发送“取消上一条请求”的自然语言指令），等待 `FORGE_AUTO_CONTINUE_TIMEOUT_WAIT_SECONDS=5` 秒后重放一次。

如果当前请求估算上下文达到 `FORGE_AUTO_CONTINUE_CONTEXT_LIMIT_TOKENS`，Smart Proxy 不再自动继续，而是返回：

```text
上下文接近超限，请新开会话
```

限制：如果模型已经向客户端输出了文本或 tool call，Smart Proxy 不会透明重放，避免重复执行工具或打乱 transcript。


### NVIDIA combined token guard

NVIDIA hosted GLM-5.2 can reject a request with a combined input+output limit, e.g. `accepts at most 202749 combined input and output tokens`. Smart Proxy therefore preflights:

```text
estimated_input + requested_max_tokens + safety <= FORGE_UPSTREAM_COMBINED_LIMIT_TOKENS
```

The guard **does not cut output tokens first**. It preserves `max_tokens`, compacts input history deterministically, and only asks for a new session if input still cannot fit:

```bash
FORGE_UPSTREAM_COMBINED_LIMIT_TOKENS=202749
FORGE_UPSTREAM_COMBINED_SAFETY_TOKENS=2048
FORGE_UPSTREAM_COMBINED_GUARD_ENABLED=1
```

If the guard cannot fit input under the target budget, the response is:

```text
上下文接近超限，请新开会话
```

## 参数调优

先观察：

```bash
curl http://127.0.0.1:4010/stats | tee /tmp/nim-stats.json
python3 scripts/diagnostics/nim_proxy_tuning.py --stats-json /tmp/nim-stats.json
# 或直接：
make nim-proxy-tuning
```

调参原则：

| 现象 | 建议 |
|---|---|
| 任一 key `in_cooldown=true` | 降低 `NIM_PROXY_PER_KEY_RPM`，例如 35 → 30；冷却改 600s |
| `semaphore_locked=true` 或 error_count 上升 | 把 `NIM_PROXY_PER_KEY_CONCURRENCY=1`，并把 `FORGE_REMOTE_MAX_CONCURRENCY=1` |
| 只有 key-1 有 success/error，key-2 一直 0 | 确认 `NIM_PROXY_SESSION_AFFINITY=0`，拉取新版并重启 4010/4000 |
| 只有 1 个 key | 先加第 2 个自用 key，而不是提 RPM |
| fallback_count > 0 | 检查 DeepSeek-V4-Pro 输出质量；不满意则关闭 fallback |
| stats 健康但仍慢 | 优先裁剪 prompt / 开 tool selection / 降 max_tokens，而不是加 key |

推荐起步值：

```bash
NIM_PROXY_PER_KEY_RPM=35
NIM_PROXY_PER_KEY_CONCURRENCY=1
NIM_PROXY_DEFAULT_COOLDOWN_SECONDS=300
NIM_PROXY_READ_TIMEOUT_SECONDS=360
NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS=600
NIM_PROXY_SESSION_AFFINITY=0
FORGE_REMOTE_MAX_CONCURRENCY=1
FORGE_CTX_SOFT_TOKENS=12000
FORGE_CTX_KEEP_RECENT_TURNS=4
FORGE_CTX_TRUNC_TOOL_RESULT_CHARS=800
```

如果 429 仍频繁：

```bash
NIM_PROXY_PER_KEY_RPM=30
NIM_PROXY_PER_KEY_CONCURRENCY=1
NIM_PROXY_DEFAULT_COOLDOWN_SECONDS=600
```

如果选择“方向 A：继续使用 GLM-5.2、禁用 fallback、接受慢响应”，推荐：

```bash
NIM_PROXY_READ_TIMEOUT_SECONDS=900
NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS=1200
NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST=1
NIM_PROXY_ENABLE_FALLBACK=0
NIM_PROXY_PER_KEY_CONCURRENCY=1
FORGE_REMOTE_MAX_CONCURRENCY=1
FORGE_CTX_MAX_TOKENS=902752
FORGE_CTX_SOFT_TOKENS=162201
FORGE_CTX_KEEP_RECENT_TURNS=4
FORGE_CTX_TRUNC_TOOL_RESULT_CHARS=1200
```

注意：`NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST=1` 很重要。若 `read_timeout=900` 且 attempts=2，坏请求最坏会占用 key 约 30 分钟，容易导致 “No NVIDIA NIM key available”。

当所有 key 都被长请求占用时，新请求现在会返回 `503 busy` + `Retry-After`，而不是误导性的 `429 retry-after: 0.0`；Smart Proxy 也不会因 NIM sidecar 的本地 busy/429 触发全局 circuit breaker。

链路分类说明：

- `NVIDIA_UPSTREAM_429_COOLDOWN`：NVIDIA/免费档上游返回 429，key 被 cooldown，偏上游问题。
- `NIM_KEYS_BUSY`：本地两个 key 正在等待长请求，后续请求会排队或 busy，偏本地容量/长请求问题。
- `LONG_TIMEOUT_WITH_MULTIPLE_ATTEMPTS`：长 timeout 叠加多次 attempts，容易把 key 占用 20-30 分钟，建议 attempts=1。
- `PROMPT_LARGE_OR_COMPACTED`：上下文过大，容易放大 GLM-5.2 延迟和 429。


---

## Smart Proxy 冲突审查

已检查当前 `_infra/smart_proxy.py` 的 NIM 相关路径：

- `FORGE_USE_NIM_PROXY=0`：保持原直连 NVIDIA 行为。
- `FORGE_USE_NIM_PROXY=1`：NVIDIA route 被重写到 `NIM_PROXY_BASE_URL`。
- 对 `api_key_optional` 的 NIM sidecar route，Smart Proxy 跳过自身 `rpm_guard`；否则会把多 key sidecar 的吞吐重新压成一个全局窗口。
- Smart Proxy 的全局 `FORGE_REMOTE_MAX_CONCURRENCY` 仍保留；它是总并发保险阀，不替代 sidecar 的 per-key concurrency。
- Anthropic→OpenAI 工具转换、SSE 回传、context guard、remote tool selection 均不被 sidecar 改写。

建议：使用 sidecar 时，把每 key 限速交给 NIM Proxy；Smart Proxy 只做协议转换、工具选择、上下文预算和总并发保护。


---

## 已实现控制

- `NVIDIA_API_KEY_1..NVIDIA_API_KEY_10` indexed key pool。
- 每 key 滑窗 RPM，默认 35。
- 每 key 并发限制，默认 1（免费档安全起步值）。
- key pool 默认关闭 session affinity（`NIM_PROXY_SESSION_AFFINITY=0`），避免同一 VS Code/cc-connect 会话永远打 key-1；如确需粘滞会话，可显式设为 1。
- `Retry-After` 解析，支持秒数和 HTTP-date。
- 429 key cooldown，默认 300 秒，cap 900 秒。
- 可配置 fallback：默认关闭，启用后可切 `deepseek-ai/DeepSeek-V4-Pro`。
- `/stats` 暴露 key 状态，但不输出真实 key。
- Smart Proxy 可通过 `FORGE_USE_NIM_PROXY=1` 改写 NIM remote route 到 sidecar。

---

## VS Code / Claude Code 长会话压测后的典型诊断

如果看到：

```json
"active_requests": 13,
"retry_counters": {"504": 15},
"key-1": {"success_count": 30, "error_count": 15},
"key-2": {"success_count": 0, "error_count": 0}
```

含义不是 Feishu 或 cc-connect 单点故障，而是 Claude Code for VS Code 在长会话里持续发起大 body / streaming 请求，NVIDIA GLM free-tier 出现 ReadTimeout/504/RemoteProtocolError，并且旧 key picker 由于粘滞/排序导致 key-1 被长期偏置。

处理顺序：

1. 拉取新版；
2. 设置 `NIM_PROXY_SESSION_AFFINITY=0`、`NIM_PROXY_PER_KEY_CONCURRENCY=1`、`FORGE_REMOTE_MAX_CONCURRENCY=1`；
3. 可接受降级时设置 `NIM_PROXY_ENABLE_FALLBACK=1`；
4. 杀掉旧 4000/4010 后重启 `bash scripts/forge-start.sh`；
5. 用 `/stats` 确认 key-1/key-2 都开始有 `success_count` 或 `error_count`。

新版还会把 streaming 入口处的 `httpx.ReadTimeout` 序列化为 SSE error，不再让 FastAPI 打出 `Exception in ASGI application` 并留下空挂请求。

---

## Troubleshooting


### Upstream GLM request waits for many minutes then fails

Symptom:

```text
NVIDIA direct curl returns HTTP 504 after ~5 minutes, or Feishu waits 10-20 minutes.
```

Meaning: NIM free-tier queue/worker is overloaded. For the chosen direction A
(GLM-5.2 remains primary and fallback stays disabled), use a long enough read timeout
to avoid cutting off successful-but-slow responses, while keeping one-attempt/no-fallback behavior:

```bash
NIM_PROXY_READ_TIMEOUT_SECONDS=360
NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS=600
NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST=1
NIM_PROXY_ENABLE_FALLBACK=0
NIM_PROXY_PER_KEY_CONCURRENCY=1
FORGE_REMOTE_MAX_CONCURRENCY=1
FORGE_CTX_SOFT_TOKENS=12000
FORGE_CTX_KEEP_RECENT_TURNS=4
FORGE_CTX_TRUNC_TOOL_RESULT_CHARS=800
```

Why: direct upstream testing showed GLM-5.2 can succeed after ~236s, but smoke tests can still fail at 360s. Therefore 360s read timeout avoids the previously guaranteed 120s cutoff, while still bounding bad turns to about six minutes. Smart Proxy skips extra remote retries for NIM sidecar routes, so retry multiplication is avoided. Fallback remains disabled by policy.

### Smart Proxy pid file points to `bash scripts/forge-start.sh`

Older `forge-start.sh` captured the PID of a subshell instead of the Python
`smart_proxy.py` process. The launcher now starts Smart Proxy via the venv Python
binary directly and writes the actual process PID to `/tmp/forge_smart_proxy.pid`.
Verify:

```bash
cat /tmp/forge_smart_proxy.pid
ps -p $(cat /tmp/forge_smart_proxy.pid) -o pid,command
```

### NIM sidecar `/v1/chat/completions` returns HTTP 422 missing query `request`

Symptom in Claude/Feishu:

```text
API Error: 504 {"detail":"Backend failed: HTTP 422: ... loc=["query","request"] ..."}
```

Meaning: FastAPI treated the handler argument named `request` as a query parameter
instead of a `Request` object. This was fixed by exposing FastAPI `Request` in module
globals before route registration. Verify your repo includes the fix:

```bash
grep -n 'globals()["Request"]' _infra/nim_proxy.py
python3 -m pytest _infra/network/tests/unit/test_nim_proxy.py -q
```

After restarting, `curl http://127.0.0.1:4010/stats` should show `request_count`
increasing after a model request.

### NIM sidecar shows `upstream_base_url` with brackets in copied chat text

If terminal output is copied into a Markdown chat, URLs may be auto-rendered as
`[https://...](https://...)`. Check the raw value with:

```bash
curl -s http://127.0.0.1:4010/stats | python3 -m json.tool | grep upstream_base_url
make env-config-audit
```

If `make env-config-audit` reports pass, the raw `.env` is likely fine; the brackets
may be only chat rendering.


---

## 红线

- 不做 key farm。
- 不在 429 cooldown 内狂刷同一 key。
- 不把小模型作为默认主链路。
- 不把免费层当生产 SLA。
- 发现提交过真实 key 后必须轮换 key；`.env.bak*` 已加入 `.gitignore`。
