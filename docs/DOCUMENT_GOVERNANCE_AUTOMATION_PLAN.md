<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-25 00:00:00
-->

# 文档治理自动化常态化方案

## 1. 背景

根目录 `DOCUMENT_AUDIT_REPORT.md` 已经指出：项目最大长期风险之一不是代码不可用，而是文档漂移、SSOT 冲突、历史文档误导和 ADR 缺失。

用户本轮反馈也验证了这个问题：虽然联网功能已经打通，但培训文档中仍缺少 Claude Code for VS Code 的主使用方式，全功能示例未覆盖高风险能力，部分历史文档仍杂乱。

因此文档治理必须从“靠每轮 Agent 自觉更新”升级为“自动化、常态化、可阻断”的机制。

---

## 2. 当前已存在的治理资产

| 资产 | 当前作用 | 问题 |
|---|---|---|
| `DOCUMENT_AUDIT_REPORT.md` | 首次系统审计报告 | 偏静态，不能自动阻断漂移 |
| `DOCUMENT_CHANGE_REPORT.md` | 首次治理变更记录 | 不是每轮自动生成 |
| `docs/GOVERNANCE_CHECK_LATEST.md` | 自动治理检查输出 | 原脚本 R5 判断过窄，已改进 |
| `scripts/governance_check.py` | 自动扫描 ADR/R5/ZIP/Agno/SSOT | 已升级为可 `--strict` 阻断 |
| `docs/adr/` | 工厂级 ADR SSOT | 需要强制新架构变更必须新增 ADR |
| `HANDOFF.md` | Agent 接手入口 | 需要把治理检查作为每轮 SOP |
| `TASK_BACKLOG.md` | 任务状态 SSOT | 状态变更仍依赖人工同步 |
| `docs/DEV_LOG.md` / `docs/CHANGELOG.md` | 开发流水 / 需求变更 | 容易重复，需要职责分离 |

---

## 3. 本轮已落地的自动化改进

### 3.1 升级 `scripts/governance_check.py`

已完成：

- R5 检查不再硬编码某个模型名，只检查是否存在 `创建/修改该文件的LLM大模型：`。
- 新增 `--strict` 模式，有阻断级问题时可非零退出。
- 新增核心 SSOT 文件存在性检查。
- 新增当前核心文档 Markdown 链接检查。
- 保留 ADR coverage、旧 Agno import、ZIP/_patches 活跃引用、ADR cross-reference 检查。
- 每次运行自动生成：
  - `docs/GOVERNANCE_CHECK_YYYY-MM-DD.md`
  - `docs/GOVERNANCE_CHECK_LATEST.md`

### 3.2 Makefile 增加常态化入口

已新增：

```bash
make governance-check
make docs-check
make network-test
```

含义：

- `make governance-check`：生成治理报告。
- `make docs-check`：严格治理检查 + compileall + git diff whitespace 检查。
- `make network-test`：Network 单元 + 安全测试。

---

## 4. 建议的常态化流程

### 4.1 每轮开发前

```bash
git pull --ff-only
cat HANDOFF.md
cat docs/PROJECT_STATE.md
grep -n "状态 SSOT" -A20 TASK_BACKLOG.md
```

确认：

- 当前状态从 `PROJECT_STATE.md` 读。
- 当前任务状态从 `TASK_BACKLOG.md` §10 读。
- 架构变更前先读 `docs/adr/README.md`。

### 4.2 每轮开发中

若改动影响以下任意一项，必须新增或更新文档：

| 改动类型 | 必须更新 |
|---|---|
| 任务状态 | `TASK_BACKLOG.md`、`docs/DEV_LOG.md` |
| 需求变化 | `docs/CHANGELOG.md` |
| 当前能力/测试基线 | `docs/PROJECT_STATE.md` |
| 架构/技术路线 | 新增 `docs/adr/ADR-xxx.md` |
| 用户手册/培训体验 | `docs/工厂使用手册.md`、`docs/全功能最小示例项目.md`、覆盖矩阵 |
| 接手流程变化 | `HANDOFF.md` |

### 4.3 每轮提交前

```bash
make docs-check
python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
```

若 `make docs-check` 失败：

- 不允许 commit。
- 先修文档治理阻断项。

### 4.4 每次重大变更后

```bash
make governance-check
git add docs/GOVERNANCE_CHECK_*.md docs/GOVERNANCE_CHECK_LATEST.md
git commit -m "docs(governance): refresh governance health check"
```

重大变更包括：

- 新增/替换核心组件。
- 修改架构边界。
- 修改调用链。
- 新增外部依赖或 API provider。
- 改变文档 SSOT。
- 删除/迁移文档。

### 4.5 每 5 轮或每周

执行一次“人工审计 + 自动报告”：

```bash
make governance-check
```

然后检查：

- `DOCUMENT_AUDIT_REPORT.md` 中哪些问题仍未关闭。
- 是否出现新孤立文档。
- 是否有 CHANGELOG 历史引用已删除文件但未标注历史。
- 是否需要新 ADR。

---

## 5. 阻断级规则建议

`make docs-check` 应视为提交前门禁。建议阻断项：

| 规则 | 是否阻断 |
|---|---|
| 核心 SSOT 文件缺失 | 阻断 |
| 工厂级 ADR 少于 baseline | 阻断 |
| core docs 出现活跃 ZIP/_patches 流程 | 阻断 |
| 当前核心 onboarding 文档存在断链 | 阻断 |
| 架构变更但无 ADR | 阻断（当前需人工判断） |
| TASK_BACKLOG 状态变化但 DEV_LOG 未更新 | 阻断（建议后续脚本化） |
| DEV_LOG/CHANGELOG 最新索引未更新 | 警告，逐步升级为阻断 |
| R5 合规率低于阈值 | 警告，新增/修改文件必须阻断 |

---

## 6. 下一步自动化增强路线

### P0：当前已完成

- 升级 `governance_check.py`。
- 增加 `make docs-check`。
- 重写培训文档。
- 重建能力覆盖矩阵。

### P1：已于 2026-06-25 落地

1. **changed-files R5 检查**
   - `scripts/governance_check.py --strict` 会检查当前工作区新增/修改的 `.py/.md/.yml/.yaml/.sh` 文件是否包含 LLM 文件头。
   - 缺失即阻断。

2. **TASK_BACKLOG ↔ DEV_LOG 同步检查**
   - `TASK_BACKLOG.md` 发生变化但 `docs/DEV_LOG.md` 未变化时阻断。

3. **代码变化但 CHANGELOG 未更新则阻断**
   - 代码/配置/脚本类文件变化时，若 `docs/CHANGELOG.md` 未同步更新，则阻断。

4. **架构触发词提示 ADR**
   - diff 中出现 `architecture`、`orchestrator`、`workflow`、`provider`、`boundary`、`routing`、`privacy` 等高风险词时，输出 warning，提示人工判断是否需要 ADR。

5. **`docs/DOCUMENT_INDEX.md` 自动生成**
   - 每次运行 governance check 都会刷新文档索引，标记 SSOT / training / governance / reference / runtime-artifact。

### P2：长期增强

1. GitHub Actions / 本地 pre-commit 集成。
2. 每周 launchd 自动运行 governance check。
3. 自动生成 `docs/DOCUMENT_INDEX.md`：列出当前文档分类、SSOT、历史、废弃、培训。
4. 自动生成 “新 Agent 接手摘要”。

---

## 7. 当前治理状态评估

本轮运行：

```bash
python3 scripts/governance_check.py --strict
```

结果：

```text
Blockers: 0
Warnings: 0
R5 Python: 191/231
R5 Markdown: 147/171
Missing links: 0
```

说明：

- 当前核心 SSOT 文件齐全。
- 当前 onboarding 核心文档无断链。
- 活跃 ZIP/_patches 流程未复发。
- 旧 Agno bad import 未复发。
- R5 历史文件仍未 100%，但当前新增/修改文件已遵守；后续应采用 changed-files 阻断策略，避免一次性清理历史成本过高。

---

## 8. 最终建议

从下一轮开始，将以下命令作为每次提交前的固定动作：

```bash
make docs-check
python3 -m pytest _infra/network/tests/unit/ _infra/network/tests/security/ -q
```

每次重大文档或架构变更后固定动作：

```bash
make governance-check
git add docs/GOVERNANCE_CHECK_*.md docs/GOVERNANCE_CHECK_LATEST.md
```

这能把文档治理从“事后补救”变成“每轮自动体检 + 阻断级门禁”。
