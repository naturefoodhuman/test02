<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# PROJECT STATE —— 当前进度快照

> 接续 Agent：这是"我们现在在哪、下一步去哪"的唯一权威。先读 `HANDOFF.md`，再读本文件。

---

## 当前总进度

**演进路线**（来自架构书第 9 章）：
- **Phase 1：基础设施**（搭骨架）← ✅ 核心链路全部打通（本地/网关/GLM流式/Fallback/CLI/Pattern）
- Phase 2：首个试点项目（走通五阶段）← 🟢 即将开始（下一轮选型）
- Phase 2：首个试点项目（走通五阶段）← ⬜ 未开始
- Phase 3：多项目并行 ← ⬜ 未开始

---

## Phase 1 退出条件勾选表（架构书第 9 章）

| 退出条件 | 状态 | 说明 |
|---|---|---|
| Ollama 模型已就绪（35b + 14b 在列） | ✅ 真机确认 | 待验对话 V-Ollama |
| LiteLLM Proxy 启动成功（3 模型加载） | ✅ 真机确认 | 终端 A 已跑通 |
| LiteLLM Proxy → Ollama 链路 | ⬜ 待真机 | 待跑 V-LiteLLM 的 curl |
| LiteLLM → GLM 链路 | ✅ | start-litellm.sh 加载Key成功；流式经网关返回真·GLM(带reasoning_content) |
| Fallback (GLM挂切本地) | ✅ | 已观察生效 |
| forge CLI / Pattern 真机测试 | ✅ 真机确认 | 19 passed / 5 passed |
| Fallback 验证（GLM 挂自动切本地） | ⬜ 待真机 | 配置已写 |
| Hooks：测试自动运行 + 熔断 | ✅ 沙箱已验证 | 熔断第5次 exit 2 已实测通过，真机复核 V-Hooks |
| `_factory/` 基础结构（≥3 Skill + 1 Pattern） | ✅ 完成 | 5 个 Skill + fastapi Pattern（core 测试已过） |

---

## 本轮（第 1 轮）目标 —— 全部完成 ✅

1. ✅ 接力维护文档体系（HANDOFF + PROJECT_STATE + DEV_LOG + DECISIONS + CHANGELOG + REAL_MACHINE_VALIDATION）
2. ✅ `_infra/`：litellm-config.yaml、model-routing-rules.md、forge-cli.sh、setup.sh、.env.example、CLAUDE.global.md
3. ✅ Hooks 脚本（post-tool-use / pre-commit / test-runner / lint-runner）—— 熔断已实测
4. ✅ `_factory/`：Skill 模板 + 4 个 Skill（discovery/arch/tdd/security）+ fastapi Pattern（可运行）+ lesson 模板
5. ✅ `_agents/`：arch-advisor / security-reviewer / code-explorer / retro-analyst
6. ✅ 全局 CLAUDE.md 模板 + 项目级 AGENTS.md/CLAUDE.md/coder/reviewer 模板
7. ✅ `forge` CLI（Python，零三方依赖）：状态机 + TASK_GRAPH 解析 + Gate 流转 + 文档校验
8. ✅ 测试：forge_tools **19 passed**；Pattern core **3 passed**；Hooks 熔断实测通过
9. ✅ 真机验证清单（含 GLM 404 坑的应对）
10. ✅ README + .gitignore 重写 + 补丁包

---

## 下一步（接续 Agent / 老板从这里继续）

**等老板做的事：**
1. 在 Mac 上解压补丁，按 `docs/REAL_MACHINE_VALIDATION.md` 逐项验证（尤其 V-Ollama / V-LiteLLM / V-GLM）。
2. 填 `_infra/.env` 的 `GLM_API_KEY`，确认 GLM 真实型号（当前占位 glm-5.1）。
3. 把验证失败的现象贴回来，我来修。

**✅ Phase 1 已收尾。下一步 = Phase 2：** 选一个真实小项目当试点，用 `projects/_TEMPLATE` 起步，
完整走通五阶段（DISCOVERY→SPEC→BUILD→HARDEN→RETRO）。
**接续 Agent 下一轮动作**：用 ask_user 给老板几个试点项目候选方向，选定后进入 DISCOVERY 阶段
（加载 `_factory/skills/discovery-interview.skill.md`，产出 `projects/{name}/docs/DISCOVERY.md`）。

---

## 变更记录

| 时间(CST) | 变更 | 模型 |
|---|---|---|
| 2026-06-10 23:03:36 | 初版创建 | Claude Sonnet 4.5 |
| 2026-06-10 23:30:00 | 第1轮收尾：基础设施骨架全部完成，更新勾选表与下一步 | Claude Sonnet 4.5 |
| 2026-06-10 23:55:00 | 第2轮：GLM 改 ModelScope、修 setup.sh、澄清 Claude Code 接入 | Claude Sonnet 4.5 |
| 2026-06-11 09:40:00 | 第3轮：修模型名乱码、litellm venv 探测；真机进度更新 | Claude Sonnet 4.5 |
| 2026-06-11 12:30:00 | 第4轮：GLM链路诊断(stream_timeout+glm-debug+diag脚本)；两条新流程规则 | Claude Sonnet 4.5 |
| 2026-06-11 15:10:00 | 第5轮：GLM根因定位(缺export Key)；新增 start-litellm.sh；流式已通 | Claude Sonnet 4.5 |
| 2026-06-11 15:45:00 | 第6轮：澄清GLM身份偏差；新增 verify-glm.sh；**Phase 1 收尾** | Claude Sonnet 4.5 |
