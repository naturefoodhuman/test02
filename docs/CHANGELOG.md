<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# CHANGELOG —— 需求增删改 + 变动说明

> 老板每轮提出的"新增 / 删除 / 改动"需求，以及由此产生的文件变动，都记在这里。
> 格式：每轮一节，列出【需求变动】和【文件影响】。

---

## [第 1 轮] 2026-06-10

### 需求变动
- **新增**：建立 FORGE Factory 基础设施骨架（Phase 1）。
- **新增**：接力维护文档体系（应对意外中止可接续）—— 来自特殊要求 #1。
- **新增**：每轮需求增删改要同步到相关文档并写变动说明 —— 来自特殊要求 #2（本 CHANGELOG 即其落地）。
- **新增**：每轮改动后打 zip 补丁包 —— 来自补丁约定。

### 文件影响（新增）
- `HANDOFF.md`（接力总入口）
- `docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、`docs/DECISIONS.md`、`docs/CHANGELOG.md`、`docs/REAL_MACHINE_VALIDATION.md`
- `_infra/`、`_factory/`、`_agents/`、`projects/` 目录骨架及其内容（本轮陆续生成，见 PROJECT_STATE.md 勾选表）

### 文件影响（本轮最终清单）
**新增（_infra）**：litellm-config.yaml、model-routing-rules.md、forge-cli.sh、setup.sh、.env.example、CLAUDE.global.md、forge_tools/（pyproject + src/forge/{__init__,task_graph,phases,cli}.py + tests/{test_task_graph,test_phases,test_cli}.py）
**新增（_factory）**：skills/{_TEMPLATE,discovery-interview,arch-design,tdd-cycle,security-review}.skill.md、patterns/fastapi-backend/（README+pyproject+src/app/{__init__,core,config,main}.py+tests/{unit,integration}）、lessons/_TEMPLATE.lesson.md
**新增（_agents）**：arch-advisor、security-reviewer、code-explorer、retro-analyst
**新增（projects/_TEMPLATE）**：AGENTS.md、.claude/{CLAUDE.md,hooks/*,agents/*,*-runner.sh}、docs/{DISCOVERY,SPEC,RISK,BUILD_LOG,TASK_GRAPH}.md、docs/{adr,specs,harden,external-review}/*
**新增（根/docs）**：README.md、docs/REAL_MACHINE_VALIDATION.md
**改动**：`.gitignore` 由上个项目（soundproof-agent）残留规则改写为契合 forge 体系。

### 说明
- 这是项目第一轮，绝大多数为"从无到有"的新增，无删除/改动既有需求。
- GLM 型号/Key 为"待补全"状态（占位 glm-5.1），属约定中的占位，非遗漏。

---

## [第 2 轮] 2026-06-10

### 需求变动
- **改动**：GLM 云端接入由"智谱官网占位"改为"经 ModelScope（魔搭）接入 GLM-5"。
- **修复**：setup.sh 在 macOS 老 bash 下的 `unbound variable` 报错。
- **澄清**：Claude Code 接入方式（环境变量，非 settings.json）。

### 文件影响
- **改动**：`_infra/litellm-config.yaml`（cloud/glm-primary → ModelScope，model 加 openai/ 前缀）
- **改动**：`_infra/.env.example`（GLM_API_KEY 说明改为 ModelScope SDK Token）
- **改动**：`_infra/setup.sh`（修参数展开 bug、去 set -u、修 Ollama 版本判断）
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-GLM 改 ModelScope 双重验证；V-ClaudeCode 补充环境变量说明）
- **改动**：`docs/DECISIONS.md`（D-003 更新为 ModelScope 方案）

### 说明
- 本轮无新增功能需求，均为对第 1 轮产物的"改动/修复/澄清"，对应特殊要求 #2。

---

## [第 3 轮] 2026-06-11

### 需求变动
- **修复**：自检脚本模型名显示乱码。
- **改进**：自检脚本对 litellm 在 venv 中的探测与提示。
- **澄清**：`ollama serve` 端口占用含义、litellm 需先激活 venv。

### 文件影响
- **改动**：`_infra/setup.sh`（模型名查找去 cut；litellm 多路径探测）
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-Ollama / V-LiteLLM 补充真机情况说明）

### 说明
- 本轮均为对真机验证中暴露问题的修复/澄清，无新增/删除功能需求（对应特殊要求 #2）。

---

## [第 4 轮] 2026-06-11

### 需求变动
- **修复（诊断中）**：ModelScope 经 LiteLLM 网关卡住 → 加 stream_timeout/drop_params + 诊断模型。
- **新增**：GLM 链路诊断脚本 `_infra/diag-glm.sh`（配合 GitHub 拉取产物的新流程）。
- **新规则**：补丁包只含改动文件（不全量）。
- **新规则**：老板 push 测试产物到 GitHub，Agent 拉取分析。

### 文件影响
- **改动**：`_infra/litellm-config.yaml`（cloud/glm-primary 加 stream_timeout+drop_params；新增 cloud/glm-debug）
- **新增**：`_infra/diag-glm.sh`
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-GLM 诊断 + V-GLM-DEBUG + 状态汇总）
- **改动**：`HANDOFF.md`（两条新流程规则）
- **改动**：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`、`docs/DECISIONS.md`

### 说明
- 本轮聚焦 GLM 链路诊断与流程优化，对应特殊要求 #2。

---
