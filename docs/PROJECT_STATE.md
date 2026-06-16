<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-15 12:00:00 CST
-->

# PROJECT STATE —— 当前进度快照

## 架构阶段
- **Phase A (Infrastructure)**: ✅ 已完成。全面迁移至 LangGraph 1.0，落地双文件模型路由与隐私门控系统。
- **Phase B (Capability Activation)**: ✅ 已完成。集成 DecisionEngine，激活 MemoryStore 遥测，实现 SKILL.md 注入。
- **Phase C (Factory Capacity)**: ✅ 已完成。
  - `forge new` (Domain-driven): ✅ 已实现领域驱动专家初始化。
  - `forge status`: ✅ 已实现项目阶段自动扫描。
  - `forge stage`: ✅ 已实现阶段流转校验。
  - `forge retro`: ✅ 已实现基于 MemoryStore 的自动化经验提取工作流。
- **Phase D (Continuous Evolution)**: 🚀 启动中。
  - 目标 1：推理性能优化 (KV Cache/多框架兼容)。
  - 目标 2：高精模型矩阵路由设计与 A/B 测试。
  - 目标 3：区域化专家知识库自动化流水线。

**重要更新 (2026-06-16)**: 核心架构升级 (v1.1.0) 已彻底完成！详见 `docs/UPGRADE_COMPLETION.md`。
- LangGraph 真实执行 + HUB-SPOKE + MTPLX 真实调用 已通过真机验证 (eval --plans mtplx-hybrid 全 5 cases 成功)。
- 双文件模型体系、DataPrivacyGate、MemoryStore、DecisionEngine、去重 KnowledgeHub 全部落地。
- 升级目标（4-Final Architecture Design + Execution Plan 中的 P0/P1）全部达成，系统已达到“真正能用”状态。

## 核心资产状态
- **专家系统**: `debt-lawyer.expert` 及多领域专家库。
- **评审引擎**: `_factory/patterns/peer-review` (LangGraph HUB-SPOKE 模式)。
- **平台层**:
  - `RoutingPlanEngine`: A/B 文件路由。
  - `DataPrivacyGate`: 实时隐私策略执行。
  - `MemoryStore`: SQLite 运行记录存储。
  - `DecisionEngine`: 三层逻辑 (Iron Gate -> AI Ref -> AI Gen)。
- **工厂工具 (forge CLI)**:
  - `forge new <name> --domain <domain>`: 快速创建领域项目。
  - `forge retro generate/submit`: 闭环经验提取。
  - `forge compare-plans`: 数据驱动方案优化。
  - `forge check/tasks/advance`: 驱动五阶段 SOP 落地。
- **验证状态**: `peer-review` (21 cases) & `debt-collection` (32 cases) 全量通过。实机端到端验证 (Retro 闭环) ✅ 已完成。

## 已知限制 / 待完成
- [ ] `forge retro` AI 辅助分析：目前仅支持数据自动填充，定性分析仍需人工编写。
- [ ] 领域映射精细化：`forge new` 的领域匹配目前基于文件名关键字，需升级为映射表。
- [ ] 旧 Agno 文件清理：待验证期满后删除。

## 运行依赖
沙箱/真机需安装：
```bash
pip install -e projects/debt-collection -e _factory/patterns/peer-review
pip install langgraph>=1.0.10 langgraph-checkpoint-sqlite>=3.0.1 \
            litellm>=1.40 chromadb>=0.6 llama-index-core>=0.12 \
            pydantic>=2.10 pyyaml rich ollama httpx
```

## 核心资产状态
- **专家系统**: `debt-lawyer.expert` 及多领域专家库。
- **评审引擎**: `_factory/patterns/peer-review` (LangGraph HUB-SPOKE 模式)。
- **平台层**:
  - `RoutingPlanEngine`: A/B 文件路由。
  - `DataPrivacyGate`: 实时隐私策略执行。
  - `MemoryStore`: SQLite 运行记录存储。
  - `DecisionEngine`: 三层逻辑 (Iron Gate -> AI Ref -> AI Gen)。
- **工厂工具 (forge CLI)**:
  - `forge new <name> --domain <domain>`: 快速创建领域项目。
  - `forge retro generate/submit`: 闭环经验提取。
  - `forge compare-plans`: 数据驱动方案优化。
  - `forge check/tasks/advance`: 驱动五阶段 SOP 落地。
- **验证状态**: `peer-review` (21 cases) & `debt-collection` (32 cases) 全量通过。

## 已知限制 / 待完成
- [ ] `forge retro` AI 辅助分析：目前仅支持数据自动填充，定性分析仍需人工编写。
- [ ] 领域映射精细化：`forge new` 的领域匹配目前基于文件名关键字，需升级为映射表。
- [ ] 旧 Agno 文件清理：待验证期满后删除。

## 运行依赖
沙箱/真机需安装：
```bash
pip install -e projects/debt-collection -e _factory/patterns/peer-review
pip install langgraph>=1.0.10 langgraph-checkpoint-sqlite>=3.0.1 \
            litellm>=1.40 chromadb>=0.6 llama-index-core>=0.12 \
            pydantic>=2.10 pyyaml rich ollama httpx
```
