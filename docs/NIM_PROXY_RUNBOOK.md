<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-08-05 12:10:00
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
export NIM_PROXY_PER_KEY_CONCURRENCY=2
export NIM_PROXY_DEFAULT_COOLDOWN_SECONDS=300
export NIM_PROXY_RETRY_AFTER_CAP_SECONDS=900
export NIM_PROXY_QUEUE_TIMEOUT_SECONDS=900

export NIM_PRIMARY_MODEL="z-ai/glm-5.2"
export NIM_PROXY_ENABLE_FALLBACK=0
export NIM_FALLBACK_MODEL="deepseek-ai/DeepSeek-V4-Pro"
```

如需同级 fallback：

```bash
export NIM_PROXY_ENABLE_FALLBACK=1
```

---

## 启动顺序

Terminal 1：启动 NIM Proxy sidecar。

```bash
cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
make run-nim-proxy
# 或 bash scripts/start-nim-proxy.sh
```

Terminal 2：启动 Smart Proxy。

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

最小 OpenAI-compatible 请求：

```bash
curl http://127.0.0.1:4010/v1/chat/completions \
  -H "Authorization: Bearer nim-proxy-local" \
  -H "Content-Type: application/json" \
  -d '{"model":"z-ai/glm-5.2","messages":[{"role":"user","content":"ping"}],"stream":false,"max_tokens":64}'
```

---

## 已实现控制

- `NVIDIA_API_KEY_1..NVIDIA_API_KEY_10` indexed key pool。
- 每 key 滑窗 RPM，默认 35。
- 每 key 并发限制，默认 2。
- session affinity：`x-forge-session-id` / `metadata.session_id` / `user` / prompt hash。
- `Retry-After` 解析，支持秒数和 HTTP-date。
- 429 key cooldown，默认 300 秒，cap 900 秒。
- 可配置 fallback：默认关闭，启用后可切 `deepseek-ai/DeepSeek-V4-Pro`。
- `/stats` 暴露 key 状态，但不输出真实 key。
- Smart Proxy 可通过 `FORGE_USE_NIM_PROXY=1` 改写 NIM remote route 到 sidecar。

---

## 红线

- 不做 key farm。
- 不在 429 cooldown 内狂刷同一 key。
- 不把小模型作为默认主链路。
- 不把免费层当生产 SLA。
- 发现提交过真实 key 后必须轮换 key；`.env.bak*` 已加入 `.gitignore`。
