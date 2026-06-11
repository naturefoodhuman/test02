<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# DECISIONS —— 已拍板决策记录

> 老板拍板过的事记在这里。**接续 Agent 不得擅自推翻**，要改必须重新问老板。
> 这是项目级的轻量 ADR；架构级 ADR 仍按架构书写到 `projects/{name}/docs/adr/`。

---

## D-001 · 第一刀从基础设施切入
- **时间**：2026-06-10
- **决策**：先搭 FORGE Factory 基础设施骨架（架构书 Phase 1），而非先做独立 CLI 或直接上试点项目。
- **理由**：架构书钦定 Phase 1 = 基础设施；老板在 ask_user 中选择 `infra_first`。
- **状态**：生效中。

## D-002 · 沙箱与真机的对齐方式 = 两者都要
- **时间**：2026-06-10
- **决策**：沙箱里能跑通的纯逻辑就地写测试跑通；依赖真实模型/Claude Code 的链路给真机验证清单。
- **理由**：沙箱无 Ollama/GLM/Claude Code；老板选择 `both`。
- **状态**：生效中。

## D-003 · GLM 经 ModelScope 接入（第2轮更新，取代原"智谱官网占位"）
- **时间**：2026-06-10（第2轮更新）
- **决策**：GLM 改走 **ModelScope（魔搭）**，而非智谱官网直连。
  - base_url=`https://api-inference.modelscope.cn/v1`
  - model=`openai/ZhipuAI/GLM-5`（**LiteLLM 必须带 `openai/` 前缀**走 OpenAI 协议）
  - env=`GLM_API_KEY`（= ModelScope SDK Token，非智谱官网 Key）
- **理由**：老板真机选择经 ModelScope 调用 GLM-5。
- **原占位（已废弃）**：智谱官网 `open.bigmodel.cn/api/paas/v4` + `glm-5.1`。
- **坑提示**：① 漏 `openai/` 前缀 → "LLM Provider NOT provided"；② ModelScope base_url 必须带 `/v1`。
- **状态**：生效中，待老板填 SDK Token 后真机验证 V-GLM。

## D-004 · 每轮打 zip 补丁包
- **时间**：2026-06-10（第4轮更新）
- **决策**：每轮改动后在 `test02/patches/` 产出 `patch_YYYYMMDD_HHMMSS_<主题>.zip`，结构对齐项目根，老板 `unzip -o` 覆盖本地。
- **第4轮更新**：补丁包**只含本轮改动的文件/目录**，不再全量打包。
- **理由**：老板硬性要求。
- **状态**：生效中。

## D-005 · 通过 GitHub 双向同步真机产物（第4轮）
- **时间**：2026-06-11
- **决策**：老板把真机测试产物/日志/错误写成文件 push 到 GitHub 仓库，Agent `git clone/pull` 拉取分析；不再手动粘贴。
- **配套**：Agent 可主动生成诊断脚本（如 `_infra/diag-glm.sh`）供老板运行后 push 回。
- **理由**：老板要求，减少手动复制成本、提升排错效率。
- **状态**：生效中。

## D-006 · GLM 经 LiteLLM 调用的稳定性处理（第4-5轮）
- **时间**：2026-06-11（第5轮定论）
- **背景**：直连 ModelScope 秒回，但经 LiteLLM 调用卡住后被 fallback 静默切本地。
- **诊断结论（diag-glm-output.txt）**：
  1. 主因 = 启动 litellm 的进程**没 export GLM_API_KEY**（`source` 不 export）→ Missing credentials → fallback 本地。
  2. 次因 = GLM 经 ModelScope **流式稳定（T4 通过）、非流式不稳（T5 回退）**。
- **决策**：
  - 新增 `_infra/start-litellm.sh`，用 `set -a` 自动 export .env 后启动 litellm（**今后启动 litellm 一律用它**）。
  - glm-primary：timeout 60 / stream_timeout 30 / drop_params true；保留 fallback。
  - 日常使用走流式（Claude Code 默认流式），不受非流式不稳影响。
- **状态**：根因已定位，流式已验证通过；待老板用启动脚本复验后标记完工。

---

## 变更记录
| 时间(CST) | 变更 | 模型 |
|---|---|---|
| 2026-06-10 23:03:36 | 初版，记录 D-001~D-004 | Claude Sonnet 4.5 |
