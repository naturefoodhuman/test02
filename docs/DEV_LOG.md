<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# DEV LOG —— 逐轮开发日志

> 记录每一轮"做了什么、为什么这么做、踩了什么坑"。接续 Agent 靠这个理解历史。

---

## 第 1 轮 · 2026-06-10

### 老板的指令
- 当技术合伙人，做出真正能用的产品。从 `naturefoodhuman/test02.git` 拉初始文档。
- 特殊要求 #1：建立接力维护文档，应对意外中止，每轮更新。
- 特殊要求 #2：每轮的需求增删改，同步到相关文档并写变动说明。
- 每轮改动后打 zip 补丁包供下载。

### 老板的关键决策（通过 ask_user）
1. **入口** = 先搭基础设施骨架（Phase 1）。
2. **对齐方式** = 两者都要（沙箱跑通逻辑 + 真机验证清单）。
3. **GLM** = 先留占位，Key/型号老板回头填。

### 我做了什么
1. 拉取仓库，读完两份核心 docx（需求书 V2 + 架构书 V4）。
2. Web 搜索确认 GLM 真实端点（`open.bigmodel.cn/api/paas/v4`，model `glm-5.1`），并发现一个真实坑：OpenAI 兼容模式可能被强制拼 `/v1` 导致 404，已记入配置注释。
3. 建立接力文档体系：`HANDOFF.md` + `docs/PROJECT_STATE.md` + `docs/DEV_LOG.md` + `docs/DECISIONS.md` + `docs/CHANGELOG.md` + `docs/REAL_MACHINE_VALIDATION.md`。
4. 建立 forge 目录骨架：`_infra/ _factory/ _agents/ projects/`。

### 为什么这么做
- 架构书明确 Phase 1 = 基础设施，且老板选了 infra_first，方向无歧义。
- 接力文档先行：老板的硬性要求是"意外中止可接续"，这必须是第一优先级，否则后面做得越多越难接手。

### 踩坑/注意
- 仓库 `.gitignore` 残留了 `soundproof-agent/` 痕迹（疑似上个项目），我们按 forge 体系重建，会更新 .gitignore。
- 沙箱是 Linux + Python 3.13 + 无 uv/Ollama/GLM/Claude Code，纯逻辑可测，链路待真机。

### 本轮最终产出（已完成）
- `_infra/`：litellm-config.yaml（含 GLM 404 坑注释）、model-routing-rules.md、forge-cli.sh、setup.sh、.env.example、CLAUDE.global.md。
- `_infra/forge_tools/`：零依赖 Python CLI（task_graph.py 解析+校验、phases.py 状态机、cli.py），**19 个测试沙箱实跑通过**。
- `_factory/skills/`：_TEMPLATE + discovery-interview + arch-design + tdd-cycle + security-review。
- `_factory/patterns/fastapi-backend/`：可运行脚手架，core 单测 **3 passed**；集成测试需真机装 fastapi。
- `_factory/lessons/_TEMPLATE.lesson.md`。
- `_agents/`：arch-advisor / security-reviewer / code-explorer / retro-analyst。
- `projects/_TEMPLATE/`：AGENTS.md + .claude（CLAUDE.md/hooks/agents/runner）+ docs 全套模板。
- Hooks 熔断：沙箱模拟连续失败，**第 5 次触发 exit 2** 验证通过。
- `docs/REAL_MACHINE_VALIDATION.md`、`README.md`、重写 `.gitignore`。

### 验证证据（沙箱实跑）
- forge_tools：`19 passed`
- pattern core：`3 passed`
- forge CLI 在 _TEMPLATE 上：status/check/tasks/advance 均正确输出，Gate 提示正确。
- 全部 bash 脚本 `bash -n` 语法通过。
- 熔断：1/5..4/5 retry，5/5 CIRCUIT BREAKER exit 2，第6次计数重置。

### 下一步建议（接续 Agent 看这里）
- 等老板真机验证链路（V-Ollama/V-LiteLLM/V-GLM/V-Fallback/V-ClaudeCode）。
- 老板填 GLM_API_KEY + 确认真实型号后，修订 litellm-config.yaml 的 model 字段。
- 验证通过即 Phase 1 完成 → 进入 Phase 2：选试点项目，复制 `projects/_TEMPLATE` 走 DISCOVERY。
- 若本轮中止重来：对照 PROJECT_STATE.md 勾选表，已完成项无需重做。

---

## 第 2 轮 · 2026-06-10

### 老板的反馈/需求
1. GLM 改走 ModelScope 接入（给了配置片段：model ZhipuAI/GLM-5，base_url api-inference.modelscope.cn/v1）。
2. setup.sh 真机报错 `m?: unbound variable`（在第 53 行参数展开处）。
3. 问：Claude Code v2.1.172 已装，settings.json 没动过，是否要手动设参数？

### 我做了什么
1. **改 GLM 配置**：litellm-config.yaml 的 cloud/glm-primary 改为 ModelScope：
   - model = `openai/ZhipuAI/GLM-5`（**关键**：LiteLLM 必须加 openai/ 前缀，老板原片段漏了会报 Provider 错）
   - api_base = `https://api-inference.modelscope.cn/v1`；cost 暂记 0。
   - 同步改 .env.example（GLM_API_KEY = ModelScope SDK Token）和 REAL_MACHINE_VALIDATION 的 V-GLM。
2. **修 setup.sh bug**：
   - 把 `${m%%:*}` 参数展开改为 `cut -d: -f1`（规避 macOS 老 bash + set -u 的 unbound 报错）。
   - 去掉 `set -u`（自检脚本不该自己崩），保留 pipefail。
   - 修正 Ollama 版本提取：服务未启动时不再把 Warning 误显示为 ✅。
   - 沙箱用假 ollama 模拟老板输出，验证：无 unbound、版本正确、两模型正确识别、RC=0。
3. **回答 Claude Code 问题**：写进 V-ClaudeCode —— **不改 settings.json**，靠环境变量
   ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN 接管；给了"开终端→export→code 启动"的临时法和写 ~/.zshrc 的长期法，并说明如何与官方直连模式互不干扰。

### 验证证据（沙箱实跑）
- forge_tools：19 passed（无回归）。
- setup.sh：假 ollama 场景 RC=0，无 unbound，模型识别正确。
- litellm-config.yaml：YAML 合法。
- bash -n：setup.sh / forge-cli.sh 语法通过。

### 下一步建议
- 老板填 ModelScope SDK Token → 先直连 curl 验 ModelScope 通 → 再过 LiteLLM 网关验 V-GLM。
- 跑 V-Ollama / V-LiteLLM / V-Fallback / V-ClaudeCode。
- 全通过 = Phase 1 收尾 → Phase 2 选试点项目。

---

## 第 3 轮 · 2026-06-11

### 老板的真机验证反馈
- ✅ forge CLI 19 passed、forge --help 正常。
- ✅ Pattern 5 passed（core+HTTP 全过）；uvicorn 起服务成功。
- ✅ LiteLLM 在终端 A 启动成功，3 个模型全部加载（local/primary、local/fallback、cloud/glm-primary）。
- ✅ 自检 Python/uv/Ollama/Git/forge 骨架全过。
- ⚠️ 自检模型名显示乱码 `??请核对 tag）`。
- ⚠️ 自检报"未找到 litellm"（实际装在 ~/.venv，终端 B 未激活）。
- ⚠️ `ollama serve` 报 address already in use（实为服务已在运行）。
- ⚠️ pytest 警告 StarletteDeprecationWarning（无害）。

### 我做了什么
1. **修模型名乱码**：去掉 cut/子shell 切割，直接用全量 tag 在 ollama list 里 grep。沙箱验证显示正常 `✅ 已发现模型：qwen3.6:35b-a3b-q8_0`。
2. **改进 litellm 探测**：PATH 找不到时探测 ~/.venv、项目 .venv、./.venv，找到则提示"在 venv 里，激活即可"，消除误导。
3. **更新真机验证清单**：
   - V-Ollama：说明 "address already in use" = 服务已运行，无需重启。
   - V-LiteLLM：说明启动前先 source venv；35b 慢可先用 fallback 14b。
4. 全量回归通过（forge 19 / pattern 3 / setup 语法 OK）。

### 当前真机进度
Phase 1 退出条件：forge/pattern/自检/litellm启动 已过；**待验**：V-Ollama 对话、V-LiteLLM 网关→本地、V-GLM 网关→ModelScope、V-Fallback、V-ClaudeCode。

### 下一步建议
- 老板在激活 venv 的终端跑 V-LiteLLM 的 curl（本地链路）。
- 跑 V-GLM（先 curl 直连 ModelScope，再过网关）。
- 这两条通过基本等于 Phase 1 完成。

---

## 第 4 轮 · 2026-06-11

### 老板的反馈/新流程要求
1. ModelScope 经 LiteLLM 网关卡住（10 分钟无返回）。
2. 【新规则】补丁包以后只含改动文件，不全量。
3. 【新规则】老板会 push 测试产物到 GitHub，我拉取分析，不用手动粘贴。

### 真机日志诊断（关键）
- ✅ local/primary 经网关正常（本地链路通）。
- ✅ 直连 ModelScope（curl + Bearer）秒回 GLM-5（Key/端点/型号全对）。
- ❌ 经网关调 cloud/glm-primary，返回的 model 是 ollama/qwen3.6 → **GLM 调用失败被 fallback 静默切到本地**。
- 根因判断：ModelScope 端点首字节慢/偏流式（直连返回带 delta 字段），LiteLLM 非流式聚合 + 默认 120s timeout 导致久等才回退。
- 旁证：老板第一次因终端未激活 venv，litellm command not found，但旧网关仍在 → 用的是旧进程。

### 我做了什么（只改 litellm-config.yaml + 文档 + 新增诊断脚本）
1. **litellm-config.yaml**：
   - cloud/glm-primary 加 `stream_timeout: 20`（卡住快速失败，官方推荐用于 slow-start provider）+ `drop_params: true`。
   - 新增 `cloud/glm-debug` 模型：**无 fallback**，失败直接报真实错误，专用排障。
2. **新增 `_infra/diag-glm.sh`**：把 T1~T5 各种调用结果收集到一个文件，老板 push 上来我分析（落实新规则3）。
3. **REAL_MACHINE_VALIDATION.md**：V-GLM 更新诊断说明 + 新增 V-GLM-DEBUG；状态汇总更新真机进度（V-0/1/2/Ollama/LiteLLM 已 ✅）。
4. **HANDOFF.md**：写入两条新流程规则（补丁只含改动 / GitHub 拉产物）。

### 下一步建议
- 老板 `source ~/.venv/bin/activate` 重启 litellm（加载新配置），跑 `bash _infra/diag-glm.sh > diag-glm-output.txt 2>&1` 并 push。
- 我据 diag 输出定位：若 T4 流式通而 T5 非流式卡 → 给 glm-primary 默认走流式或加配置；若 T3 报具体错 → 对症修。

---
