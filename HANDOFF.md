<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间：2026-06-15 03:45:00 CST
-->

# HANDOFF —— 接力交接文档（v2.0 第28轮修订版）

> 目标：任何 Agent 5 分钟内接手并继续开发。
> ⚠️ **任何 Agent 接手后，必须按以下顺序阅读**：
> 1. `DOCUMENT_AUDIT_REPORT.md`（最新治理审计 + 问题清单）
> 2. `HANDOFF.md`（本文件）
> 3. `docs/UPGRADE_COMPLETION.md` + `docs/adr/README.md`（架构完成状态 + 工厂级决策 SSOT，含 7 个核心 ADR）
> 4. `docs/PROJECT_STATE.md`（当前状态）
> 5. `docs/DEV_LOG.md` + `docs/DECISIONS.md`（历史演进，DECISIONS 已为 legacy） + `docs/CHANGELOG.md`

---

## 1. 项目定位
本产品为 **AI 项目孵化工厂 (FORGE Factory)**。
试点项目 `debt-collection` 是用来压测工厂能力的"沙包"，不作为正式开发目标。

**当前架构版本**：v1.1.0（LangGraph 迁移已启动，双文件体系 + DataPrivacyGate 已落地）

---

## 2. 运行环境与路径

### 老板真机路径
- **macOS 绝对路径：** `/Users/naturist/MusicProject/AI-Project-Incubation-Factory`
- **沙箱开发路径：** `/home/user/test02`（Agent 开发用，老板不用管）
- **GitHub 仓库：** `https://github.com/naturefoodhuman/test02.git`

### 同步方式
- （历史）早期曾使用 ZIP 补丁方式，已于 2026-06-16 正式废弃（Documentation Governance Phase 1）。当前唯一流程为公钥 + Deploy Key + git pull。
- 或者老板 `git pull` 拉取最新代码
- **标准化发布流程**：`make release` 或 `bash release.sh [patch|minor|major] "发布说明"` → 自动更新版本号、CHANGELOG、git tag → `git push origin main --tags`

### 虚拟环境 (Venv) 矩阵
| 环境 | 路径 | 用途 |
|------|------|------|
| 主工厂环境 | `.venv`（根目录） | 运行网关 (start-litellm.sh)、专家咨询、peer-review |
| MinerU 专用 | `projects/debt-collection/runtime/mineru_env` | PDF 深度解析 |
| forge CLI | `_infra/forge_tools/` 下独立安装 | 五阶段状态机 |

### 模型矩阵 (Ollama / 中国 API)
| 模型别名 | 来源 | 用途 |
|----------|------|------|
| `local-qwen35b` | Ollama `qwen3.5:35b-a3b-q8_0` | 本地执行核心（默认主专家） |
| `local-deepseek-r1` | Ollama `deepseek-r1:32b` | 本地推理核心 |
| `local-coder` | Ollama `qwen2.5-coder:32b` | 本地代码任务 |
| `local-fast` | Ollama `qwen2.5:7b` | 快速分类/路由 |
| `embedding` | Ollama `bge-m3` | 向量检索 |
| `deepseek-flash` | DeepSeek API | 外源快速评审 |
| `deepseek-pro` | DeepSeek API | 外源高质量汇总 |
| `qwen-plus` | Alibaba API | 超长上下文/中文法律 |
| `glm-5` | Zhipu API | 中文专项 |

> 完整配置见 `config/models.yaml`（A 文件）。节点如何调用见 `config/routing_plans.yaml`（B 文件），切换方案只改 `active_plan` 字段。

---

## 3. 核心规则（Agent 必须遵守）

- **R1 — 老板说的算**
- **R2 — 反方评估（穷尽调研）**
- **R3 — 保姆级指示**
- **R4 — 文档与变更记录**
- **R5 — 文件头 LLM 留痕规范**
- **R6 — 文档同步**
- **R7 — 不重复造轮子**
  - 同类功能，能利用 GitHub 等开源社区的成熟方案，绝不重复造轮子。调研时优先寻找已有的、活跃的、高星的开源项目，只有在确实不满足核心需求或成本/复杂度过高时才考虑自建。
- **R8 — 灵活的代码行数限制**
  - 放松对单个文件代码行数的硬性限制。特别是文档类文件（.md, .txt），不设行数上限，以保证内容的完整性和逻辑的连贯性。对于代码文件，优先考虑模块化设计，但在确有必要时（如复杂的业务逻辑单元）允许长文件存在，不以行数作为唯一评估标准。

---

## 4. 操作 SOP（保姆级）

### 启动 Ollama 服务（终端 A）
```
终端 A:
1. ollama serve
   → 预期输出：ollama listening on :11434
```

### 启动 LiteLLM 网关（终端 B，仅云端模型需要）
```
终端 B:
1. cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
2. source .venv/bin/activate
3. bash _infra/start-litellm.sh
   → 预期输出：📥 加载环境变量 → ✅ GLM_API_KEY 已加载 → 🚀 启动 LiteLLM
```

### 运行 Peer-Review 评审（终端 C）
```
终端 C:
1. cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
2. source .venv/bin/activate
3. 
4. debt review 1
   > **注意**：v1.1.0+ 已迁移到 LangGraph，`debt review` 默认使用 config/routing_plans.yaml 中的 active_plan。
   > 如需临时切换方案：debt review 1 --plan high-quality
   > 使用 API 模型时，若含 human_approve 字段会强制要求输入 yes 确认；local_only 字段会被阻断。
   → 预期输出：
     🔍 启动 Peer-Review 模块 (LangGraph)...
     ✅ peer_review 模块加载成功
     🚀 激活方案: default
     → 主专家完成
     → reviewer_1 完成
     → reviewer_2 完成
     → reviewer_3 完成
     → 汇总完成 (分歧度: 0.00)
     （主专家分析 + 最终汇总结论）
     📝 已记录运行到 MemoryStore：方案 default | 耗时 Xs | 分歧度 0.00
```

### 运行隐私安全模式（全部本地，无数据出境）
```
终端 C:
1. debt review 1 --plan all-local
   → 预期输出：使用 all-local 方案，数据完全不出本地，不触发确认门
```

### 从 HITL 中断点恢复评审
```
终端 C:
1. debt continue review-xxxx
   → 预期输出：从 human_review_gate 中断点继续，完成最终汇总
   > 注意：thread_id 来自前一次 `debt review` 输出
```

### 运行端到端验证脚本
```
终端 C:
1. cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
2. source .venv/bin/activate
3. python3 scripts/e2e_review_test.py --plan default
   → 真实 LLM 模式（需 Ollama + LiteLLM 已启动）
4. python3 scripts/e2e_review_test.py --mock
   → 模拟模式，无需外部模型，用于快速验证管道
   → 报告输出：runtime/e2e_review_default_<timestamp>.md
```

### 录入测试债务
```
终端 C:
debt add "张三" 50000 --evidence "微信转账"
→ 预期输出：✅ 已录入债务 #1：张三 50000.0元
```

---

## 5. 项目目录结构（快速索引）

```
AI-Project-Incubation-Factory/
├── HANDOFF.md                      # ⭐ 本文档（交接必读）
├── README.md                       # 项目总览
├── docs/
│   ├── PROJECT_STATE.md            # 当前进度快照
│   ├── DECISIONS.md                # 已拍板决策（不得擅自改）
│   └── DEV_LOG.md                  # 逐轮开发日志
├── _infra/                         # 基础设施（LiteLLM 网关、自检脚本）
├── _factory/
│   ├── skills/                     # SKILL.md 技能库
│   │   ├── prescription-risk.skill.md
│   │   ├── asset-search.skill.md
│   │   └── compliance-layered.skill.md
│   ├── patterns/
│   │   ├── peer-review/            # FB-14 多专家评审（v1.1.0 LangGraph）
│   │   │   ├── src/peer_review/
│   │   │   │   ├── graph/          # LangGraph 图结构
│   │   │   │   │   ├── review_graph.py
│   │   │   │   │   ├── nodes/
│   │   │   │   │   │   ├── primary_expert.py
│   │   │   │   │   │   ├── reviewer.py
│   │   │   │   │   │   └── consensus.py
│   │   │   │   │   └── checkpointer.py
│   │   │   │   ├── platform/       # 平台层（路由/隐私/记忆/知识/决策）
│   │   │   │   │   ├── routing_plan_engine.py
│   │   │   │   │   ├── data_privacy_gate.py
│   │   │   │   │   ├── memory_store.py
│   │   │   │   │   ├── knowledge_hub.py
│   │   │   │   │   └── decision_engine.py
│   │   │   │   ├── config/         # Pydantic 配置层
│   │   │   │   │   ├── schemas.py
│   │   │   │   │   └── loader.py
│   │   │   │   ├── orchestrator.py # LangGraph 兼容入口（保留 Agno 旧入口）
│   │   │   │   └── llm_client.py
│   │   │   └── tests/
│   │   │       ├── test_peer_review_langgraph.py
│   │   │       └── verify_architecture.py
│   │   ├── expert-consultant/
│   │   ├── ingestion-pipeline/
│   │   ├── data-acquisition/
│   │   └── llm-telemetry/
│   └── experts/
│       ├── debt-lawyer.expert/     # 主专家
│       ├── risk-assessor.expert/   # 评审专家
│       ├── compliance-auditor.expert/
│       └── execution-strategist.expert/
├── projects/
│   ├── _TEMPLATE/                  # 新项目脚手架
│   └── debt-collection/            # 试点项目
│       ├── src/debt/               # 债务助手核心代码
│       │   ├── cli.py              # CLI 入口（含 review 命令）
│       │   ├── models.py
│       │   └── strategy.py
│       └── tests/
# 注意：_patches/ 目录及所有 ZIP 补丁流程已于 2026-06-16 正式废弃（Documentation Governance Phase 1）。本目录树中已完全移除相关引用。
```

---

## 6. 常见排障

| 现象 | 原因 | 解决方案 |
|------|------|---------|
| `OPENAI_API_KEY not set` | Team 未指定本地模型，默认走 OpenAI | 确保 `orchestrator.py` 中 Team 传入了 `model=Ollama(id=...)` |
| `ModuleNotFoundError: No module named 'agno'` | 依赖未安装 | `uv pip install agno llama-index-core chromadb` |
| `f-string expression part can include a backslash` | Python 3.11 语法限制 | f-string 花括号内不能有 `\n` 等转义字符，改用变量拼接 |
| `ModuleNotFoundError: No module named 'debt'` | PYTHONPATH 未设置 | `export PYTHONPATH=$PYTHONPATH:$(pwd)/projects/debt-collection/src` |
| `cannot import name 'Mode' from 'agno.team.mode'` | Agno 2.6 API 变更 | `mode="sequential"` 替换 `mode=Mode.SEQUENTIAL` |
| `Agent.__init__() got an unexpected keyword argument 'add_history_to_messages'` | Agno 参数废弃 | 移除 `add_history_to_messages` 和 `markdown` 参数 |
| 日志显示 `正在构建专家  向量索引`（ID 为空） | YAML 缺 `id` 字段 | 在专家 YAML 第一行加 `id: xxx` |
| `debt review` 输出 "模型调用不可用" | LiteLLM 网关和 Ollama 都未启动 | 终端 A 启动 `ollama serve`，终端 B 启动 `bash _infra/start-litellm.sh` |
| `InvalidUpdateError: Can receive only one value per step` | 旧版测试或旧代码未使用 LangGraph `Annotated` reducer | 确保使用 `test_peer_review_langgraph.py` 新测试，旧版已删除 |
| `ModuleNotFoundError: No module named 'langgraph'` | 依赖未安装 | `pip install langgraph>=1.0.10 langgraph-checkpoint-sqlite>=3.0.1` |
| `debt continue` 提示 "找不到线程状态" | 输入的 thread_id 错误或检查点已丢失 | 确认 thread_id 与 `debt review` 输出完全一致 |

---

## 7. 给接手 Agent 的检查清单

接手后按顺序执行：
- [ ] 读本文档（HANDOFF.md）
- [ ] 读 `docs/PROJECT_STATE.md` 了解当前进度
- [ ] 读 `docs/DECISIONS.md`（legacy，早于 2026-06-16 治理；当前工厂级决策见 `docs/adr/` + `docs/adr/README.md`）
- [ ] 读 `docs/DEV_LOG.md` 最后一轮了解最近做了什么
- [ ] 读 `DOCUMENT_AUDIT_REPORT.md` + `docs/UPGRADE_COMPLETION.md` 了解文档健康状态和架构完成度
- [ ] 确认老板的下一个需求是什么（如果老板没说，主动问）
- [ ] **任何新功能/架构变更前，先做 R2 调研**（穷尽→正反评估→老板认可→执行）
- [ ] 改完文件后同步更新所有相关文档（必须遵循 Code → Tests → Documentation → CHANGELOG → ADR（如需）流程）
- [ ] 运行对应测试确保通过
- [ ] 给老板保姆级操作指令（终端号/路径/环境/预期输出）
- [ ] 直接 push（已建立 Deploy Key 协议）→ 老板 Mac `git pull origin main`
- [ ] 执行 Continuous Governance 检查（发现漂移/缺失 ADR/SSOT 冲突等必须优先修复）
