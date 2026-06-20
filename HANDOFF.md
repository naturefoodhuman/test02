<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间：2026-06-21 16:30:00 CST
-->

# HANDOFF —— 接力交接文档 (v1.2.5 第42轮修订版)

> 目标：任何 Agent 5 分钟内接手并继续开发。
> ⚠️ **接手必读顺序**：
> 1. `HANDOFF.md`（本文件，最高规则 SSOT）
> 2. `docs/ARCHITECTURE.md`（动态调度网关架构）
> 3. `docs/PROJECT_STATE.md`（当前状态与 VRAM 水位）
> 4. `docs/CHANGELOG.md`（最近一轮 64G 显存优化记录）

---

## 0. 最高规则 (Supreme Rules)

### R0 — 不重复造轮子 (DRY at Scale)
同类功能，能利用 GitHub 等开源社区的成熟方案，绝不重复造轮子。调研时优先寻找已有的、活跃的、高星的开源项目（如 LiteLLM, LangGraph），只有在确实不满足核心需求或成本/复杂度过高时才考虑自建。

### R1 — 老板说的算
老板拍板的决策（见 `docs/adr/`）不得擅自推翻。

### R2 — 反方评估
决策前必须穷尽调研业界主流方案，给出优劣对比表，等老板认可后再执行。

---

## 1. 项目定位与架构版本
本产品为 **AI 项目孵化工厂 (FORGE Factory)**。
**当前版本**：v1.2.5 (Dynamic VRAM Loading Edition)
**核心特性**：实现了 Mac M1 Max 64G 显存下的 **“自检-卸载-按需加载”** 闭环。

---

## 2. 运行环境与路径 (Mac M1 Max)
- **主工厂路径**：`/Users/naturist/MusicProject/AI-Project-Incubation-Factory`
- **模型服务器**：`~/LocalAI/servers`
- **GGUF 路径**：`~/LocalAI/gguf-models/`

### 虚拟环境
- `source .venv/bin/activate` (根目录，包含 litellm, langgraph, fastapi)

---

## 3. 操作 SOP (保姆级)

### A. 每日开工 (启动网关)
```bash
终端 A:
1. cd /Users/naturist/MusicProject/AI-Project-Incubation-Factory
2. source .venv/bin/activate
3. bash scripts/forge-start.sh
   → 预期：执行全量端口冷启动自检，成功后自动释放显存。
4. python3 _infra/smart_proxy.py
   → 预期：启动 4000 端口智能网关。
```

### B. 开启工作 (Claude Code)
```bash
终端 B:
1. claude
   → 预期：遇到模型请求时，网关会自动弹窗拉起对应模型。
```

### C. 运行业务压测
```bash
终端 B:
1. export PYTHONPATH=$PYTHONPATH:$(pwd)/_factory/patterns/peer-review/src
2. python3 scripts/benchmark_test.py
```

---

## 4. 显存管理规则 (R11)
- **VRAM 红线**：48GB (统一内存)。
- **回收机制**：Smart Proxy 采用 LRU 算法。若新请求会导致显存 > 48G，将自动 pkill 最久未使用的模型。
- **强制泄洪**：若系统卡顿，运行 `bash scripts/purge_vram.sh`。

---

## 5. 治理与规范
- **R5 文件头**：所有文件顶部必须有“创建/修改模型 + 北京时间”。
- **R8 行数限制**：文档与复杂逻辑代码不设硬性行数限制。
- **过期处理**：所有旧代码、旧设计文档均在 `_obsolete/` 目录下。


---


---

## 6. 仓库清理与过期资产规则
- 最新仓库资产盘点见 `docs/repository-audit.md`。
- 清理报告见 `docs/repository-cleanup-report.md`。
- `_obsolete/` 为本地归档目录，已加入 `.gitignore`，禁止 push 到 GitHub。
- 用户明确要求保留：`projects/legal-bot/`、`projects/project-b/`、`retro-data-share/`；不得擅自迁移。
- 源码与文档不一致时，以当前源码和配置为准，并在审计/清理报告中记录差异。
