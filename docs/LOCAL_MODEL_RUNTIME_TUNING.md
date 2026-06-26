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


---

## 8. 日志位置

本地模型日志写入 macOS 临时目录 `/tmp`，这是绝对路径，不在项目目录中。

常用日志：

```bash
ls -lh /tmp/mtplx_8080.log /tmp/mtplx_8082.log /tmp/llama_8084.log /tmp/forge_smart_proxy.log /tmp/forge_litellm_4001.log 2>/dev/null

tail -120 /tmp/mtplx_8080.log

tail -120 /tmp/mtplx_8082.log

tail -120 /tmp/llama_8084.log
```

如果找不到 `/tmp/mtplx_8080.log`，通常是：

1. 模型尚未被启动；
2. `scripts/forge-start.sh` 只做冷启动自检后立即卸载，但正常情况下日志仍应保留；
3. macOS 的 `/tmp` 实际映射到 `/private/tmp`，也可以试：

```bash
ls -lh /private/tmp/mtplx_8080.log
```

查看当前哪些端口/进程在运行：

```bash
scripts/model_status.sh
```

---

## 9. 当前 MTPLX 显式加速参数

根据本机 `uv run mtplx quickstart --help`，当前已把显式参数写入 `config/model_runtime.yaml`：

8080 Qwen 主模型：

```bash
--profile sustained --mtp --depth 3 --stream-interval 1 --reasoning off --max-tokens 2048
```

8082 Gemma 评审模型：

```bash
--profile sustained --mtp --depth 6 --stream-interval 1 --reasoning off --max-tokens 2048
```

依据：

- Qwen3.6 MTPLX Quality 模型卡给出 depth-3 bakeoff 指标；
- Gemma4 MTPLX Quality 模型卡给出 block_size/depth 6、acceptance 99.76%、speedup_vs_ar 2.49x；
- `--stream-interval 1` 让服务端尽可能频繁提交 token chunk；
- `--reasoning off` 用于 Claude Code 日常交互，减少“thinking process”拖慢和污染输出。

如需做严谨 A/B，请复制一个端口配置，分别用 `--mtp` 与 `--no-mtp`、不同 `--depth` 对比。


---

## 10. A/B 对比注意事项

用户真机日志已经证明：

- 8080 Qwen：`Mode Sustained MTP`、`Installing native-MTP draft head`；
- 8082 Gemma：`Gemma 4 assistant MTP drafter is active`；
- 8084 Qwopus：`[spec] estimated memory usage of MTP context`。

这证明 MTP/spec runtime 已经进入工作路径。但如果要证明“加速多少”，不能用不同 prompt 或不同 completion token 数的日志直接比较。

严格 A/B 必须固定：

```text
prompt
max_tokens
temperature
top_p
top_k
seed
context/history
```

并且每次对照前：

```bash
scripts/stop_local_models.sh
: > /tmp/mtplx_8080.log
bash scripts/forge-start.sh
```

注意：`--no-mtp` 在 MTPLX sustained profile 下可能仍显示加载 MTP runtime；这不一定表示对照失败，因为 runtime 可加载 MTP 但 generation path 使用 target-only AR。最终应以 `mtplx_openai_generation` 指标和 MTPLX 更详细日志为准。

`test_mtp_effectiveness.py` 会解析最近 `mtplx_openai_generation` 指标：

```bash
python3 scripts/diagnostics/test_mtp_effectiveness.py
```

重点比较：

```text
prompt_tokens
completion_tokens
elapsed_s
tok_s
end_to_end_tok_s
```


---

## 11. 2026-06-26 真机诊断结果记录

用户真机执行后得到以下关键结论：

### 11.1 `forge-start.sh` 自检后 direct backend refused 是预期行为

`forge-start.sh` 会冷启动 8080/8082/8084 做可用性校验，然后立即卸载模型释放显存。因此紧接着运行：

```bash
python3 scripts/diagnostics/test_local_streaming.py
```

可能出现：

```text
openai-backend: status=exception ... Connection refused
anthropic-proxy: status=ok ... content_block_delta
```

这表示 8080 direct backend 被卸载，但 4000 Smart Proxy 可按需拉起 8080 并返回 Claude Code 所需的 Anthropic SSE。不是故障。

### 11.2 MTP runtime 已确认进入工作路径

用户日志确认：

```text
8080 Qwen: Mode Sustained MTP / Installing native-MTP draft head
8082 Gemma: Gemma 4 assistant MTP drafter is active
8084 Qwopus: [spec] estimated memory usage of MTP context
```

因此当前结论是：

```text
MTP/speculative runtime 已启用。
```

### 11.3 短 prompt A/B 中 no-MTP 更快，不代表 MTP 无效

用户短 prompt A/B：

```text
MTP on:  prompt=22, completion=299, elapsed=34.30s, tok_s=8.86, e2e=8.72
no-MTP:  prompt=22, completion=260, elapsed=26.24s, tok_s=10.15, e2e=9.91
```

解释：

- 该样本中 no-MTP 更快。
- 但 completion tokens 不同，输出内容不同，且 prompt 很短。
- MTP/speculative decoding 在极短 prompt、短输出、小样本中可能因为 draft/verify 开销不占优。
- MTP 的收益更应在长输出、稳定 prompt、固定 seed、同等 completion length、重复多次时评估。

因此当前不能得出“MTP 比 no-MTP 慢”的全局结论，只能记录：

```text
短 prompt 单样本下 no-MTP 表现更快；需要标准化 benchmark 后再决定默认策略。
```

### 11.4 当前默认参数的合理性

当前默认仍保留：

```bash
--profile sustained --mtp --depth 3 --stream-interval 1 --reasoning off --max-tokens 2048
```

原因：

- 这是模型卡和 MTPLX runtime 推荐方向；
- 长上下文 Agent / Claude Code 用例更接近 MTP 目标场景；
- 单次短 prompt 结果不足以推翻默认；
- 若用户日常大量短问答，可后续增加 `fast-interactive` profile，使用 `--no-mtp` 或更小模型。


---

## 12. 一键综合 Benchmark（最终版）

如果不想手工切换 `--mtp` / `--no-mtp` / KV cache 参数，可以运行最终版一键 benchmark：

```bash
python3 scripts/diagnostics/benchmark_local_runtime.py
```

默认会一次性覆盖：

```text
profiles: mtp_depth3, no_mtp, mtp_depth3_kv_q8, mtp_depth3_kv_q4
prompts: controlled_medium, controlled_long_context
repeat: 2
startup-mode: proxy-only
stream benchmark: skipped by default, 每个 profile 仍会运行 test_local_streaming.py
```

设计原则：

- 每个 profile 只改变 8080 `extra_args`，控制单一变量；
- prompt 是固定格式，减少 completion 长度漂移；
- long context prompt 内置 48 条固定记录，用于测试长上下文 + 中长输出；
- 每个 profile/prompt 重复 2 次，生成 mean/std；
- 脚本自动恢复原始 `config/model_runtime.yaml`。

快速烟测：

```bash
python3 scripts/diagnostics/benchmark_local_runtime.py --profiles mtp_depth3,no_mtp --prompts controlled_medium --repeat 1
```

最终测试产物目录：

```text
diagnostics/local_runtime_benchmark/<timestamp>/
```

请发送：

```text
report.md
report.json
各 profile 的 mtplx_8080.log
test_local_streaming.txt
test_mtp_effectiveness.txt
```

或直接打包：

```bash
LATEST_DIR="$(ls -td diagnostics/local_runtime_benchmark/* | head -1)"
tar -czf /tmp/local_runtime_benchmark_latest.tar.gz "$LATEST_DIR"
```

注意：完整默认测试可能耗时 40～120 分钟。期间不要在 Claude Code 中发起其它本地模型请求。
