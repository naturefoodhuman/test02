<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

---
skill_id: arch-design
name: 架构设计与 ADR
phase: [SPEC]
load_when: "SPEC 阶段，把 DISCOVERY.md 转成架构、技术选型、任务图时"
last_verified: 2026-06-10
version: 0.1
---

# 技能：架构设计与 ADR（SPEC 阶段核心）

## 何时用
- SPEC 阶段，需要从需求推导架构与技术选型（FR-001-5/6/7）。首选 cloud/glm，GLM 挂则 local/primary。

## 核心步骤
1. **提炼关键技术决策点**：列出 N 个必须拍板的决策（存储？框架？通信？部署？）。
2. **每个决策写 ADR**（FR-001-6）：用下方格式，记"为什么"，不只记"是什么"。
3. **技术选型对比**：候选方案 ≥2，对比维度（成本/复杂度/生态/契合度）。
4. **拆原子任务**（FR-001-7/8）：每个任务可独立测试、独立回滚，估算 50–300 行。
5. **写依赖关系**：任务图标 depends-on。
6. **风险清单**（FR-001-9）：技术/性能/成本风险 + 缓解措施 → `docs/RISK.md`。

## ADR 格式（写到 docs/adr/ADR-NNN-<slug>.md）
```
# ADR-001：<决策标题>
- 状态：提议 / 已接受 / 已废弃
- 日期：YYYY-MM-DD
- 背景：为什么要做这个决策？约束是什么？
- 决策：我们决定 X。
- 备选：A（弃因…）、B（弃因…）
- 后果：好处 / 代价 / 引入的风险
```

## 检查清单
- [ ] ADR 数量 ≥ 关键技术决策数量
- [ ] 每个 Feature 有 acceptance.md
- [ ] TASK_GRAPH 每个任务粒度 50–300 行估算
- [ ] RISK.md 覆盖技术/性能/成本

## 反模式
- 只记结论不记理由（事后没人知道为什么这么选）。
- 任务粒度过大，无法独立测试/回滚。

## 输出物
- `docs/SPEC.md`、`docs/specs/{feature}/spec.md` + `acceptance.md`、`docs/adr/ADR-*.md`、`docs/TASK_GRAPH.md`、`docs/RISK.md`
