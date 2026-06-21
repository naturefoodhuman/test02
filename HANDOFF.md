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

**当前架构版本**：v1.1.0（LangGraph 已迁移，双文件体系 + DataPrivacyGate 已落地）

---

## 2. 运行环境与路径

### 老板真机路径
- **macOS 绝对路径：** `/Users/naturist/MusicProject/AI-Project-Incubation-Factory`
- 硬件配置：M1 max 64G
### 虚拟环境 (Venv) 矩阵
| 环境 | 路径 | 用途 |
|------|------|------|
| 主工厂环境 | `.venv`（根目录） | 运行网关 (start-litellm.sh)、专家咨询、peer-review |
| MinerU 专用 | `projects/debt-collection/runtime/mineru_env` | PDF 深度解析 |
| forge CLI | `_infra/forge_tools/` 下独立安装 | 五阶段状态机 |

### 模型矩阵 (Ollama / 中国 API)
| 模型别名 | 来源 | 用途 |
|----------|------|------|


> 完整配置见 `config/models.yaml`（A 文件）。节点如何调用见 `config/routing_plans.yaml`（B 文件），切换方案只改 `active_plan` 字段。

---

## 3. 核心规则（Agent 必须遵守）

### R1 — 老板说的算
- 老板拍板的决策（见 `docs/DECISIONS.md`）**不得擅自推翻**，要改必须先问老板。

### R2 — 反方评估（穷尽调研）
- 决策前必须调研业界主流方案，给出优劣对比表。
- 不重复造轮子 (DRY at Scale)：同类功能，能利用 GitHub 等开源社区的成熟方案，绝不重复造轮子。调研时优先寻找已有的、活跃的、高星的开源项目（如 LiteLLM, LangGraph），只有在确实不满足核心需求或成本/复杂度过高时才考虑自建。
- 调研原则：**穷尽全世界相关项目** → 正方分析（优点/可借鉴） → 反方分析（缺点/不适用） → 给出推荐方案 → **等老板认可后再执行**。
- 老板说"没用或不适合的项目不能随便拉取下来用，只用最好最适合的"。

### R3 — 保姆级指示
- 给老板的每条操作指令必须包含 **四要素**：
  1. **终端编号**（终端 A / 终端 B / …）
  2. **当前路径**（`cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory`）
  3. **虚拟环境状态**（`source .venv/bin/activate` 或说明不需激活）
  4. **预期输出**（终端会打印什么，成功/失败的标志）
- **禁止** 给模糊指令如"你试试看""跑一下"。

### R4 — 文档与变更记录（治理强化）
- 每次有意义变更必须遵循：Code → Tests → Documentation → CHANGELOG → ADR（如为重大架构决策）→ Commit。
- 禁止静默修改文档或让代码与文档长期不一致。
- 任何 Agent 接手后必须阅读 `DOCUMENT_AUDIT_REPORT.md`（最新审计报告）和 `docs/UPGRADE_COMPLETION.md`。

### R5 — 文件头 LLM 留痕规范（强制，必须严格遵守）
**目的**：让任何未来 Agent（包括你自己）能快速知道某个文件是哪个模型在什么时间创建或最后修改的，实现可追溯。

**硬性要求（每次新建或修改文件时必须执行）**：
1. 在文件**最顶部**（第一行或前几行）立即添加以下格式的头部注释。
2. **不同文件类型使用不同注释风格**：
   - **Python (.py)**：使用 `#` 注释
   - **Markdown (.md)**：使用 HTML 注释 `<!-- -->`
   - **YAML (.yaml / .yml)**：使用 `#` 注释
   - **其他文本**：优先使用对应语言的注释风格

**标准格式（示例）**：

对于 Python / YAML：
```
# 创建/修改该文件的LLM大模型：Claude-Sonnet-4-6
# 创建时间（北京时间）：2026-06-16 14:30:00
```

对于 Markdown：
```
<!--
创建/修改该文件的LLM大模型：Claude-Sonnet-4-6
创建时间（北京时间）：2026-06-16 14:30:00
-->
```

**执行规则**：
- **新建文件**：创建后第一件事就是加头部。
- **修改文件**：修改前或修改后必须更新“创建/修改”行（把大模型名更新当前实际使用的模型，时间更新为本次修改时间）。
- **时间格式**：严格使用 `YYYY-MM-DD HH:MM:SS`（北京时间）。
- **模型名称**：必须写当前实际使用的模型比如 `Gpt 5.5 pro` 。
- **位置**：必须是文件的最前面内容（在任何其他内容之前）。

**禁止行为**：
- 忘记加头部
- 把头部放在文件中间或末尾
- 在 .py / .yaml 文件中使用 `<!-- -->`
- 只改代码不更新头部

**为什么重要**：这是实现 “Auditable + Traceable + Self-Documenting” 的基础机制。未来 Agent 接手时会依赖这些头部快速建立文件历史心智模型。

**检查清单**（每次提交前自检）：
- [ ] 本轮新建/修改的所有文件都已加头部
- [ ] 头部在文件最顶部
- [ ] 时间是本次操作的北京时间
- [ ] 注释风格正确（.md 用 <!-- -->）

### R6 — 文档同步
- 改了什么模块 → 同步更新 `docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、`docs/DECISIONS.md`。
- 如果 HANDOFF.md 里的操作 SOP 过时了 → **直接修正 HANDOFF.md**，不要等老板提醒。

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
# 注意：experts/中的内容可能已经过时，应以 `config/models.yaml`为准。
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
