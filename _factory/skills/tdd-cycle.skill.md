<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

---
skill_id: tdd-cycle
name: TDD 内循环
phase: [BUILD]
load_when: "BUILD 阶段，逐个任务实现代码并自测时"
last_verified: 2026-06-10
version: 0.1
---

# 技能：TDD 内循环（BUILD 阶段核心，零成本本地完成）

## 何时用
- BUILD 阶段每个 Task 的实现（FR-001-11/12）。首选 local/primary（zero cost）。

## 核心步骤（内循环）
1. 读 `docs/specs/{feature}/acceptance.md`，把验收标准转成测试代码（首个 Task 的强制动作）。
2. **先写测试**（tests/unit/），再实现（src/）。
3. 跑测试（由 post-tool-use Hook 自动触发）。
   - 通过 → 更新 `docs/TASK_GRAPH.md` 该任务 `status: DONE` → 下一个 Task。
   - 失败 → 重新实现（最多 3 次）→ 仍失败 → Fallback 到 local/fallback。
   - 再失败 → 可升级 cloud/glm → 仍失败触发熔断（连续 5 次）→ HITL 介入。
4. 任务完成后 commit（pre-commit Hook 检查 lint + TASK_GRAPH 无 IN_PROGRESS）。

## 检查清单
- [ ] 每个 Task 有对应单测
- [ ] 测试客观通过（不接受"LLM 自评"，NFR-005）
- [ ] TASK_GRAPH status 已更新为 DONE（pre-commit 强制）
- [ ] 变更已 Git 追踪（FR-001-15）

## 反模式
- 跳过测试直接写实现。
- 测试失败仍标 DONE。
- 一次改一大坨（无法独立回滚）。

## 输出物
- `src/` 实现 + `tests/unit/` 测试 + TASK_GRAPH 状态更新 + Git commit
