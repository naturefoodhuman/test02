<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-26 00:00:00
-->

# 本地模型运行参数与推理加速指南

## 1. 目标

本文件是本地开源模型运行参数的操作说明。目标是让 MTPLX、Ollama、llama.cpp 等后端的启动参数可追溯、可配置、可验证，而不是散落在多个脚本中硬编码。

当前运行参数 SSOT（决策记录：`docs/adr/ADR-009-local-model-runtime-configuration.md`）：

```text
config/model_runtime.yaml
```

相关工具：

```bash
python3 _infra/model_runtime.py command 8080
python3 _infra/model_runtime.py command 8082
python3 _infra/model_runtime.py command 8084
python3 _infra/model_runtime.py env-shell ollama
python3 scripts/diagnostics/test_local_streaming.py
python3 scripts/diagnostics/test_mtp_effectiveness.py
scripts/model_status.sh
scripts/stop_local_models.sh
```

---

## 2. 当前模型清单

| 角色 | 后端 | 模型 | 配置位置 |
|---|---|---|---|
| 本地主大脑 | MTPLX | `Youssofal/Qwen3.6-27B-MTPLX-Optimized-Quality` | `config/model_runtime.yaml` → `servers.8080` |
| 测试 / 编码模型 | Ollama | `qwen3-coder-next:q4_K_M` | `config/model_runtime.yaml` → `ollama.models.qwen3-coder-next` |
| 独立评审 | Ollama | `deepseek-r1:32b` | `config/model_runtime.yaml` → `ollama.models.deepseek-r1-32b` |
| 独立评审 | MTPLX | `Youssofal/Gemma4-MTPLX-Optimized-Quality` | `config/model_runtime.yaml` → `servers.8082` |
| 深度评审 | llama.cpp | `Qwopus3.6-35B-A3B-v1-MTP-Q8_0.gguf` | `config/model_runtime.yaml` → `servers.8084` |

---

## 3. 如何自定义启动参数

### 3.1 MTPLX 参数

编辑：

```text
config/model_runtime.yaml
```

例如为 8080 主模型增加 MTPLX 参数：

```yaml
servers:
  8080:
    extra_args:
      - "--some-mtplx-flag"
      - "value"
```

然后检查生成命令：

```bash
python3 _infra/model_runtime.py command 8080
```

重启：

```bash
scripts/stop_local_models.sh
bash scripts/forge-start.sh
```

说明：当前模型卡片给出的 MTPLX 启动示例是 `mtplx start --model ...` 或本项目历史使用的 `mtplx quickstart --model ... --port ...`。是否存在显式 `--stream` 或 `--mtp` 参数，需要以你本地安装的 MTPLX CLI 为准：

```bash
cd ~/LocalAI/servers
uv run mtplx --help
uv run mtplx quickstart --help
uv run mtplx start --help
```

如果 help 中出现 stream / serve / mtp / profile / depth 等参数，再写入 `extra_args`。

### 3.2 Ollama 参数

当前已在 `config/model_runtime.yaml` 中设置：

```yaml
ollama:
  env:
    OLLAMA_FLASH_ATTENTION: "1"
    OLLAMA_KV_CACHE_TYPE: "q4_0"
```

`bash scripts/forge-start.sh` 启动 Ollama 前会加载这些环境变量。

检查：

```bash
python3 _infra/model_runtime.py env-shell ollama
```

如果你希望“永久”对手工启动的 Ollama 也生效，可以在 shell 配置或 launchctl 中设置，但项目内推荐先以 `scripts/forge-start.sh` 为准，避免污染全局环境。

### 3.3 llama.cpp / Qwopus MTP 参数

当前 8084 配置已启用：

```yaml
spec_type: "draft-mtp"
spec_draft_n_max: 2
flash_attention: true
```

生成命令包含：

```bash
--spec-type draft-mtp --spec-draft-n-max 2 -fa on
```

检查：

```bash
python3 _infra/model_runtime.py command 8084
```

---

## 4. 如何判断 MTP 是否真正生效

### 4.1 静态证据

- Qwen3.6 MTPLX Quality 模型卡说明 artifact 包含 `mtplx_runtime.json` 和 `mtp/weights.safetensors`，MTPLX 可通过 native Qwen MTP backend 路由。
- Gemma4 MTPLX Quality 模型卡说明它是 target + assistant 的 MTPLX pair bundle，并给出 speculative decoding 的 acceptance / speedup 数据。
- Qwopus MTP GGUF 模型卡说明该 GGUF 保留 MTP heads，并兼容支持 MTP speculative decoding 的 llama.cpp / derivatives。

静态证据只能说明“模型具备 MTP 条件”，不能证明你的本地运行已启用。

### 4.2 运行时证据

运行：

```bash
python3 scripts/diagnostics/test_mtp_effectiveness.py
```

它会检查：

- 启动命令是否包含 speculative / MTP flags；
- `/tmp/mtplx_8080.log`、`/tmp/mtplx_8082.log`、`/tmp/llama_8084.log` 是否出现：
  - `mtp`
  - `draft`
  - `acceptance`
  - `speedup`
  - `tok/s`
  - `tps`

### 4.3 真正证明加速的方法

必须做 A/B：

1. 同一个 prompt；
2. 同一个 max_tokens；
3. 开启 MTP / spec flags 跑一次；
4. 关闭 MTP / spec flags 跑一次；
5. 比较：
   - time to first token；
   - decode tok/s；
   - total tokens/sec；
   - acceptance rate；
   - total latency。

如果日志能看到 acceptance / draft accepted / speedup_vs_ar，且 tok/s 明显优于关闭 MTP，则可认为 MTP 加速生效。

---

## 5. 如何判断是否真流式

运行：

```bash
python3 scripts/diagnostics/test_local_streaming.py
```

结果含义：

| 状态 | 含义 |
|---|---|
| `true_streaming` | 后端返回多个 OpenAI SSE delta，是真 token streaming。 |
| `single_delta` | 后端只返回一个文本 delta，可能是伪流式。 |
| `full_json_not_sse` | 后端无视 `stream=true`，返回完整 JSON。 |
| `anthropic-proxy: ok` | Smart Proxy 已输出 Claude Code 需要的 `content_block_delta`。 |

如果后端不是 `true_streaming`，但 `anthropic-proxy: ok`，说明：

```text
Claude Code 协议层可用，但 token-by-token 真流式受后端 runtime 限制。
```

---

## 6. 推荐调优顺序

1. 先保证稳定：

```bash
scripts/stop_local_models.sh
bash scripts/forge-start.sh
python3 scripts/diagnostics/test_local_streaming.py
```

2. 再确认 Ollama 环境变量：

```bash
python3 _infra/model_runtime.py env-shell ollama
```

3. 再确认 MTP / spec flags：

```bash
python3 scripts/diagnostics/test_mtp_effectiveness.py
```

4. 最后做 A/B benchmark。不要在还不稳定时盲目增加 flags。

---

## 7. 当前已知结论

- `FORGE_CLAUDE_CODE_MAX_TOKENS` 限制输出长度，不提升输入处理速度。
- Ollama 的 `OLLAMA_FLASH_ATTENTION=1` 与 `OLLAMA_KV_CACHE_TYPE=q4_0` 已纳入项目启动配置。
- Qwopus llama.cpp 路径已显式使用 MTP speculative flags。
- MTPLX Qwen / Gemma 的 MTP 能力更多由 artifact metadata + MTPLX runtime 决定，是否需要额外 flag 需看本地 `mtplx quickstart --help`。
- Hugging Face 模型卡提供了 MTP / acceptance / speedup 线索，但本地是否生效必须看启动命令和 runtime 日志。
