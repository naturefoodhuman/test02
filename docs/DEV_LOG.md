<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-15 03:45:00 CST
-->

# DEV LOG —— 逐轮开发日志

## 第 31 轮 · 2026-06-15
### 真实 LLM 端到端验证 + 节点级隐私校验 + HITL 恢复 + 流式输出优化

**已完成：**
1. **LLM 客户端节点级隐私二次校验**
   - `peer_review/llm_client.py` 在调用 API 模型前，根据 `privacy_context` 执行 `DataPrivacyGate.check()`
   - 若 `approved=False` 且含 `local_only` 字段，返回阻断响应
   - 若含 `human_approve` 字段，返回需先完成 CLI 确认提示
   - 本地模型不触发二次校验
2. **HITL 中断恢复流程**
   - 新增 `continue_langgraph_review(thread_id)` 函数，从 `human_review_gate` 中断点恢复
   - 新增 `debt continue <thread_id>` CLI 命令
   - `debt review` 输出中打印线程 ID，触发人工审核时提示 `debt continue` 命令
3. **Rich Live Display 流式进度展示**
   - `run_langgraph_review` 与 `continue_langgraph_review` 均支持 `use_live=True`
   - 实时展示节点状态：等待 / 完成 / 人工审核中断点
   - 不影响 `use_live=False` 的测试模式
4. **端到端验证脚本**
   - 新增 `scripts/e2e_review_test.py`
   - 支持 `--mock` 模式（沙箱/CI 无需外部模型）
   - 支持真实 LLM 模式（需启动 Ollama + LiteLLM）
   - 输出 Markdown 报告到 `runtime/e2e_review_<plan>_<timestamp>.md`
5. **测试补充**
   - `peer-review` 测试从 16 个增至 21 个
   - 新增：LLM 客户端隐私校验、模拟 LLM 端到端、HITL 恢复异常路径

**验证结果：**
- `peer-review` 21 个测试 ✅ 全通过
- `debt-collection` 32 个测试 ✅ 全通过
- `scripts/e2e_review_test.py --mock` ✅ 可生成完整报告
- 总计 53 个测试 ✅ 全通过

**遗留到下轮：**
- 在真实 LLM/Ollama 环境下运行 `scripts/e2e_review_test.py` 并记录输出质量评分
- 删除旧 Agno 文件（待 LangGraph 稳定 2 周后）

---

## 第 30 轮 · 2026-06-15
### DataPrivacyGate 实时确认门 + MemoryStore 自动记录

**已完成：**
1. **`debt review` 挂接 DataPrivacyGate 实时确认门**
   - 在 `projects/debt-collection/src/debt/cli.py` 中新增：
     - `_extract_privacy_fields()`: 将 `Debt` 字段映射到 `privacy_policy.yaml` 字段名
     - `_plan_uses_api()`: 判断激活方案是否使用任何 API 模型
   - 若方案使用 API 模型，启动图前自动检查 `chinese_api` 端点的数据出境策略
   - `local_only` 字段被阻断 → 中止并提示改用 `all-local` 方案
   - `human_approve` 字段 → 强制要求输入 `yes` 确认，否则中止
2. **`debt review` 结束后写入 MemoryStore**
   - 计时图执行总耗时
   - 从 `routing_plans.yaml` 解析预估成本
   - 生成 `ModelRunRecord` 并写入 `runtime/memory.db`
   - 输出提示："已记录运行到 MemoryStore：方案 X | 耗时 Ys | 分歧度 Z"
3. **测试补充**
   - 新增 `projects/debt-collection/tests/test_debt_review.py` 10 cases，全部通过

**验证结果：**
- `debt-collection` 32 个测试 ✅ 全通过（原 22 + 新增 10）
- `peer-review` 16 个测试 ✅ 全通过
- `make test` 全量通过 ✅

**遗留到下轮：**
- 真实 LLM 环境下验证 DataPrivacyGate 确认门与 HITL 中断点
- 在 `llm_client.py` 中做节点级数据出境二次校验（当前为 CLI 入口级）
- 删除旧 Agno 文件（待 LangGraph 稳定 2 周后）

---

## 第 29 轮 · 2026-06-15
### 架构升级：LangGraph 迁移启动（路径 A）

本轮按 `4-Final Architecture Design.md` 的 Phase A 线 1 启动 LangGraph 迁移，
同时完成线 2 平台层落地与项目状态对齐。

**已完成：**
1. **LangGraph 核心图结构** (`_factory/patterns/peer-review/src/peer_review/graph/`)
   - `state.py`: `ReviewState` TypedDict，并行字段使用 `Annotated` reducer
   - `review_graph.py`: HUB-SPOKE 状态图，`primary_expert` → 条件边 `Send` → 并行评审者 → `consensus_builder` → HITL/END
   - `checkpointer.py`: `SqliteSaver` 检查点持久化
   - `nodes/primary_expert.py`: 主专家节点 + 决策引擎铁闸
   - `nodes/reviewer.py`: 信息屏蔽评审者节点（只读 `case_context`）
   - `nodes/consensus.py`: 汇总 + 简化分歧度检测
2. **平台层** (`platform/`)
   - `routing_plan_engine.py`: 加载 A/B 文件并交叉验证，支持方案菜单与内存预检
   - `data_privacy_gate.py`: 执行 `privacy_policy.yaml` 策略（local_only / mask / human_approve / allow）
   - `memory_store.py`: `ModelRunRecord` SQLite 记录
   - `knowledge_hub.py`: 知识统一接口
   - `decision_engine.py`: 铁闸硬编码规则 + AI 参考/生成框架
3. **LLM 客户端** (`llm_client.py`): 优先 LiteLLM 网关，回退 Ollama 直连，再降级提示
4. **CLI 对齐** (`projects/debt-collection/src/debt/cli.py`)
   - 修复 `ROOT` 未定义 bug
   - `debt review` 切换到 `run_langgraph_review()`，参数改为 `--plan` 临时指定方案
5. **测试更新**
   - 删除过期的 `test_peer_review.py`（引用已不存在的旧类）
   - 新增 `test_peer_review_langgraph.py` 16 cases，全部通过
6. **配置与工程**
   - 更新 `.gitignore`: 排除专家目录生成的 JSON / index 文件（减小仓库体积）
   - 安装依赖：`langgraph`, `langgraph-checkpoint-sqlite`, `litellm`, `chromadb` 等

**验证结果：**
- `debt-collection` 22 个测试 ✅ 全通过
- `peer-review` 16 个新测试 ✅ 全通过
- `run_langgraph_review()` 在无 LLM 环境下可完成端到端图执行并返回完整状态

**遗留到下轮（第 30 轮已完成）：**
- ~~在 `debt review` 调用链中挂接 DataPrivacyGate 运行时确认门~~ ✅
- ~~在 `debt review` 结束后自动写入 MemoryStore~~ ✅
- 真实 LLM 环境下验证 HUB-SPOKE 并行输出质量
- 删除旧 Agno 文件（待稳定 2 周后）

---

## 第 28 轮 · 2026-06-13
### 核心架构重构 (v1.0.5 Agno + LlamaIndex)
1. **技术栈升级**：废弃手写架构，全面引入 Agno (Agent/Team/Memory) + LlamaIndex (RAG) + ChromaDB (Vector)
2. **隐私合规**：禁用 Agno 遥测 (`AGNO_TELEMETRY=false`)，模型请求全走本地 Ollama (127.0.0.1)
3. **修复项**：
   - `orchestrator.py`：修复 f-string 语法错误、移除废弃 Agent 参数、适配 Agno 2.6 Team API
   - `expert.yaml`：修复嵌套结构导致 ID 为空的问题，增加 model 别名映射
   - `cli.py`：修复 ModuleNotFoundError，增强 PYTHONPATH 解析逻辑

## 第 27 轮 · 2026-06-13
### 规范修复与知识库升级
1. **修复规范**：HANDOFF.md 重写（补全保姆级 SOP + 排障表 + 检查清单）
2. **R2 穷尽调研**：完成 Vibe-Trading、quant-mind、Hands-On-AI 调研与决策记录 (D-011)
3. **方案 A**：专家知识库大幅升级（新增 case_patterns.md, negation_cases.md 等）
4. **方案 B**：引入 SKILL.md 系统 + LayeredDecisionEngine 分层决策引擎

## 第 26 轮 · 2026-06-13
### FB-14 Peer-Review 基础架构
1. 核心架构：`_factory/patterns/peer-review/` 模块初始化
2. 新增 3 位评审专家定义
3. CLI 集成：`debt review` 命令
