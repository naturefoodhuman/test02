<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-12 03:00:00 CST
-->

---
lesson_id: 2026-Q2-debt-collection
project_name: debt-collection（个人合法讨债助手 / 工厂首个陪练）
project_type: 本地 CLI 工具（动态案件博弈）
tech_stack: Python 3.11 + SQLite + LiteLLM 网关(GLM/qwen) + 工厂 Pattern(ingestion/acquisition)
model_versions: qwen3.6-35b / GLM-5(ModelScope) / 离线模板兜底
date: 2026-06-12
status: 草稿（待真机数据补全 + HITL Gate-5 审批）
---

# 经验教训：debt-collection（工厂首个完整五阶段陪练）

> ⚠️ 写入 _factory/ 前需 HITL Gate-5 审批（防错误知识污染后续项目）。当前为草稿。

## 1. 成功经验（可复用的）
- **陪练定位救了方向**：把试点当"压测工厂的沙包"，每轮都同时产出"工厂能力/缺陷"，比只做项目价值大。
- **合规调研前置**：法律/强监管领域，DISCOVERY 阶段先做合规调研，成功拦截"个人非法查财产"的刑事红线。
- **动态博弈范式**：情报库+时间线+策略重算，适用于一切"持续博弈型"项目（不只讨债）。
- **三级模型可用性**：GLM→本地→离线模板，任何环境都有可用下限。
- **能力复用**：工厂 Pattern 让 SPEC→BUILD 提速；新项目优先复用而非重造。

## 2. 失败经验（避坑的）
- **集成外部工具必须真实端到端验证**：只写"检测到库"的占位 → 真机输出空（Ingestion 踩过）。
- **产物默认放项目内 runtime/**：放用户根目录会污染（踩过）。
- **领域认知先调研**：别想当然（"个人能查他人财产"是违法的）。
- **GLM 经网关要用对 Key + export**：Key 填错/没 export 会静默 fallback 到本地（GLM 链路排查多轮）。
- **markitdown 要装 [all]**：否则 docx/pptx 失败；扫描件必须 MinerU OCR。

## 3. 改进建议（未来可做的）
- 工厂：补 FB-1(字段完整性校验)、FB-2(.forge_phase 阶段状态)、FB-3(领域知识工厂化)、FB-9(存储 Pattern)。
- 项目：社交情报自动入 intel、DB 加密、文书生成 feature。

## 4. 本项目产出的新 Skill / Pattern（AC-008）
- 新 Skill：data-ingestion、data-quality、data-acquisition。
- 新 Pattern：ingestion-pipeline（多格式→结构化）、data-acquisition（合规取数协调器）。
- （均可运行 + 有测试，满足 KR-004-2）

## 5. 模型与成本（用于优化路由矩阵）
- 🟦 各 Phase 耗时：待真机
- 🟦 GLM 调用次数 / 成本：待真机
- 🟦 本地模型占比（目标 ≥80%）：待真机
- 沙箱开发期：云端调用为 0（纯逻辑+离线兜底）。

## 6. 关键决策回顾（ADR/规则）
- ADR-001~006：本地CLI+SQLite / GLM防幻觉 / 合规取数 / 执行可行性优先 / 敏感数据本地 / 动态博弈。
- 规则 R1/R2/R3：模型不限本地 / 决断先调研 / 操作保姆级。
