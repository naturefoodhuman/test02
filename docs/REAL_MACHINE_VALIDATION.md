<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# REAL MACHINE VALIDATION —— 真机验证清单

> 沙箱（Linux，无 Ollama/GLM/Claude Code）跑不了的链路，由老板在 Mac 上逐项验证。
> 每项给了**命令**和**期望结果**。打勾即代表通过。验证时如失败，把现象贴回来我来修。

前置：先把补丁解压到 `/Users/naturist/MusicProject/AI-Project-Incubation-Factory`，并 `cd` 进去。

---

## [V-0] 环境自检
```bash
bash _infra/setup.sh --check
```
- [ ] 期望：Python/uv/Ollama/LiteLLM/Git/forge 骨架逐项有 ✅ 或明确提示。

## [V-1] forge CLI 能装能跑（沙箱已通过，真机复核）
```bash
cd _infra/forge_tools
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple
python -m pytest -q          # 期望：19 passed
forge --help                 # 期望：打印命令帮助
```
- [ ] 19 passed
- [ ] `forge` 命令可用

## [V-2] Pattern 自带测试通过（沙箱已通过 core 部分）
```bash
cd _factory/patterns/fastapi-backend
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple
python -m pytest -q          # 期望：core + http 集成全过
uvicorn app.main:app --port 8000 &
curl -s http://localhost:8000/health     # 期望：{"status":"ok",...}
curl -s "http://localhost:8000/greet?name=老板"   # 期望：含"老板"的中文问候
```
- [ ] 单测 + 集成测试通过
- [ ] /health 与 /greet 正常

## [V-Ollama] 本地模型工具调用（C3/C4）
```bash
# ⚠️ 若 `ollama serve` 报 "address already in use"，是好事——说明服务已在后台运行，
#    直接用即可，无需再启动。（macOS 装 Ollama 后常已随登录自启。）
ollama list             # 确认 qwen3.6:35b-a3b-q8_0 与 qwen3:14b 在列
ollama run qwen3:14b "用一句话中文自我介绍"   # 期望：中文回复，然后 /bye 退出
```
- [ ] 两个模型都在列且能对话

## [V-LiteLLM] 网关 → Ollama 链路
> ⚠️ litellm 装在 venv（如 `~/.venv`）里时，启动前要先激活该 venv：
> `source ~/.venv/bin/activate`，否则 `litellm` 命令找不到（这正是终端 B 自检"未找到 litellm"的原因，无害）。

```bash
# 终端 A（已在跑就不用重启）：
source ~/.venv/bin/activate
litellm --config _infra/litellm-config.yaml --port 4000

# 终端 B 另开，发测试请求（本地主力模型）：
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"local/primary","messages":[{"role":"user","content":"你好"}]}'
```
- [ ] 返回本地模型的中文回复（说明 LiteLLM→Ollama 通）
- [ ] 若超时：35b 首次加载较慢，多等几十秒；或先用 `"model":"local/fallback"`（14b 更快）试。

## [V-GLM] 网关 → GLM 链路（经 ModelScope，⚠️ 待填 ModelScope SDK Token）
先在 `_infra/.env` 填 `GLM_API_KEY`（= ModelScope SDK Token），
确认 `litellm-config.yaml` 里 model 为 `openai/ZhipuAI/GLM-5`、api_base 为 `https://api-inference.modelscope.cn/v1`。

先单独验证 ModelScope 端点本身能通（绕过 LiteLLM，直连）：
```bash
source _infra/.env
curl -s https://api-inference.modelscope.cn/v1/chat/completions \
  -H "Authorization: Bearer $GLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"ZhipuAI/GLM-5","messages":[{"role":"user","content":"你好"}]}'
```
- [ ] 直连 ModelScope 返回 GLM 回复（确认 Token 与型号有效）

再通过 LiteLLM 网关验证：
> ⚠️⚠️ 第5轮关键修复：启动 litellm **必须用启动脚本**，否则 GLM_API_KEY 进不了进程环境
> （光 `source _infra/.env` 默认不 export，litellm 会报 Missing credentials）。
```bash
source ~/.venv/bin/activate            # 激活装了 litellm 的 venv
bash _infra/start-litellm.sh           # ← 用这个启动（自动 export .env），不要再裸跑 litellm
# 它会打印 "✅ GLM_API_KEY 已加载到环境"，看到这行才说明 Key 进去了

# 另开终端测试（GLM 默认走流式最稳）：
curl -N -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"cloud/glm-primary","stream":true,"messages":[{"role":"user","content":"你好，报一下你是哪个模型"}]}'
```
- [ ] 经网关返回 **GLM** 回复（返回 JSON 里 `"model"` 应是 ModelScope/GLM，而不是 ollama/qwen）

> 🔑 **怎么 100% 确认调的是 GLM 而不是被 fallback？**（第6轮）
> 不要看模型嘴上说自己是谁——**GLM-5 常自报为"通义千问/GPT"，这是训练数据导致的认知偏差，不代表调错**。
> 权威依据是 LiteLLM 的**响应头 `x-litellm-model-id`**（官方文档指定的 fallback 验证方法）。
> 一条命令搞定：
> ```bash
> bash _infra/verify-glm.sh
> # 输出 "✅ 实际调用的是 ModelScope 的 GLM-5" = 链路正确
> ```
> 或手动看响应头：`curl -i ...` 然后找 `x-litellm-model-id`，含 `GLM-5` 即对。
> 另两个 GLM 特征：响应里有 `reasoning_content`（思考链）、`"model":"cloud/glm-primary"`（被 fallback 会变成 `ollama/qwen3.6`）。
- [ ] **若 `"model"` 是 `ollama/qwen3.6...`**：说明 GLM 调用失败被 fallback 切到本地了 → 用下面 V-GLM-DEBUG 看真实错误。
- [ ] **若报 "LLM Provider NOT provided"**：检查 model 是否带了 `openai/` 前缀（应为 `openai/ZhipuAI/GLM-5`）。
- [ ] **若 404**：检查 api_base 是否为 `.../v1`（ModelScope 必须带 /v1）。

## [V-GLM-DEBUG] 诊断 GLM 经网关卡住/被回退（第4轮新增）
> 背景：第3轮真机发现——直连 ModelScope 秒回，但经 LiteLLM 调 `cloud/glm-primary` 时
> 卡很久后返回的是本地 qwen（说明 GLM 调用失败触发了 fallback）。
> 第4轮已加 `stream_timeout: 20` + `drop_params: true`，并新增**无 fallback 的诊断模型** `cloud/glm-debug`。

**步骤①：用流式（stream）方式调 glm-primary（最可能直接成功）**
```bash
curl -N -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"cloud/glm-primary","stream":true,"messages":[{"role":"user","content":"你好"}]}'
```
- [ ] 期望：以 SSE 流式逐字返回 GLM 回复（`data: {...}` 多行）。若流式通了，说明问题就是非流式聚合卡顿。

**步骤②：用诊断模型（无 fallback，失败会直接报真实错误）**
```bash
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"cloud/glm-debug","messages":[{"role":"user","content":"你好"}]}'
```
- [ ] 期望情况A：返回 GLM 回复（说明 stream_timeout/drop_params 修好了）。
- [ ] 期望情况B：返回一段**错误 JSON**（不再静默切本地）→ **把这段错误原样贴回来/或 push 给我**，我据此定位。

> 排障完成后，日常仍用 `cloud/glm-primary`（带 fallback，更稳）。`cloud/glm-debug` 留着备用无害。

## [V-LocalModels] 新增本地模型验证（第7轮）
> 用 start-litellm.sh 启动网关后，逐一验证新加的 3 个本地模型。
```bash
# 编程专用模型（chat）
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"local/coder","messages":[{"role":"user","content":"用Python写一个判断质数的函数"}]}'

# 向量嵌入（首选 bge-m3）—— 注意走 /embeddings 端点
curl -s http://localhost:4000/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"local/embedding","input":"你好世界"}'

# 向量嵌入（备选 qwen3-embedding:8b）
curl -s http://localhost:4000/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"local/embedding-large","input":"你好世界"}'
```
- [ ] local/coder 返回代码
- [ ] local/embedding 返回向量数组（data[0].embedding）
- [ ] local/embedding-large 返回向量数组
- [ ] 若 embedding 报错：确认 Ollama 已拉取 bge-m3 / qwen3-embedding:8b（ollama list）

## [V-Fallback] GLM 不可用自动切本地（C2）
```bash
# 临时把 GLM_API_KEY 改成错误值，重启 litellm，再调 cloud/glm-primary
# 期望：不报死，自动回退 local/primary 给出本地回复
```
- [ ] 工作流不中断，回退本地成功

## [V-ClaudeCode] Claude Code 走本地网关（C6）

> ⚠️ 重要澄清：**不要去改 VS Code 的 settings.json**。Claude Code 是通过**环境变量**接管的。
> settings.json 保持原样即可。你要做的是：在启动 VS Code 的那个终端里先 export 两个环境变量，
> 再从该终端启动 VS Code，这样 Claude Code 才会继承到这些变量、把请求打到本地网关。

具体步骤（每次想用 forge 网关时）：
```bash
# 1) 确保 ollama 和 litellm 已在跑（见 V-LiteLLM）
# 2) 在终端 export（也可以放进 _infra/.env 后 source）
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_AUTH_TOKEN=sk-forge-local-anytoken
# 3) 从这个终端启动 VS Code（关键：让它继承环境变量）
code /Users/naturist/MusicProject/AI-Project-Incubation-Factory
# 4) 在 Claude Code 里随便发一句话，去看 LiteLLM 终端是否打印出这次请求
```
- [ ] Claude Code 的请求出现在 LiteLLM 日志里（说明已走本地网关）

> 想长期固定：把上面 2 个 export 写进 `~/.zshrc`（用完想恢复直连官方时再注释掉）。
> 想临时只用某次：就用上面"开终端→export→code"这套，不影响全局。
> 如果你大多数时候仍想用 Claude 官方账号直连，那就**不要**全局设这两个变量，
> 只在要跑 forge 流水线时临时开终端设置——两种模式互不干扰。

## [V-Hooks] 熔断机制（沙箱已逻辑验证，真机复核）
```bash
# 复制 _TEMPLATE 到一个项目，故意让 test-runner.sh 失败，连续触发 5 次
# 期望：第 5 次打印 CIRCUIT BREAKER 并 exit 2
```
- [ ] 第 5 次触发熔断

---

## 验证状态汇总
| 项 | 状态 | 备注 |
|---|---|---|
| V-0 | ✅ | 真机自检通过（模型名乱码已修） |
| V-1 | ✅ | 真机 19 passed，forge 命令可用 |
| V-2 | ✅ | 真机 5 passed，uvicorn 起服务成功 |
| V-Ollama | ✅ | 真机 qwen3:14b 对话正常 |
| V-LiteLLM | ✅ | 真机 local/primary 经网关返回正常 |
| V-GLM | ✅ | 第7轮闭环：根因=Key 填错；填对后 diag-glm-v2 全绿（A1/A2/B1/B2/B3），流式+非流式均命中真 GLM。"非流式不稳"是 Key 错误的假象 |
| V-LocalModels | ⬜ | 第7轮新增 local/coder + local/embedding(+large)，待真机各测一次 |
| V-GLM-DEBUG | ✅ | 第4轮诊断已跑（T3 暴露 Missing credentials，定位成功） |
| V-Fallback | ✅ | 已观察到 fallback 生效（GLM 非流式失败→自动回退本地，工作流不中断） |
| V-ClaudeCode | ⬜ | |
| V-Hooks | ⬜ | 沙箱已逻辑验证 |

## 变更记录
| 时间(CST) | 变更 | 模型 |
|---|---|---|
| 2026-06-10 23:03:36 | 初版 | Claude Sonnet 4.5 |
| 2026-06-11 12:30:00 | 第4轮：更新真机进度；GLM 诊断（stream_timeout+glm-debug），新增 V-GLM-DEBUG | Claude Sonnet 4.5 |
| 2026-06-11 15:10:00 | 第5轮：诊断定位根因(缺export Key+非流式不稳)；新增 start-litellm.sh；V-GLM 改用启动脚本+流式 | Claude Sonnet 4.5 |
| 2026-06-11 15:45:00 | 第6轮：澄清 GLM 自报身份偏差；新增 verify-glm.sh（x-litellm-model-id 终极判定）；V-GLM 标记通过 | Claude Sonnet 4.5 |
| 2026-06-11 16:30:00 | 第7轮：非流式不稳遗留问题；diag-glm.sh/verify-glm.sh v2 重写（流式/非流式分别测+ModelScope 非流式对照） | Claude Sonnet 4.5 |
