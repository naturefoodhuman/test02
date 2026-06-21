<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-21 14:45:00 CST
-->

# FORGE Network（联网功能增量子模块）

**位置**：`_infra/network/`（现有 FORGE Factory 的**增量模块**）

本模块为 FORGE Factory 叠加：
- 本地公开搜索（SearXNG）
- 网页提取（Crawl4AI + 降级）
- 输入净化 + Privacy Gateway（7 层）
- MCP 安全治理 + 模式隔离
- 浏览器自动化（后续 Phase）
- 本地 RAG

**严格原则**：
- 复用现有 FORGE 架构（根 pyproject、config/、runtime/、forge CLI）
- 不创建独立 pyproject / 独立顶级 src
- 所有代码放在本目录下
- 配置统一使用根 `config/network.yaml`

更多详情见根目录 `NETWORK_ARCHITECTURE_FINAL.md` 和 `NETWORK_ENGINEERING_DESIGN.md`（已按增量模式调整）。

## 快速开发命令（未来）
```bash
# 启动网络服务
bash _infra/network/scripts/start_services.sh

# 健康检查
python -m forge.network health   # 或待实现 CLI 集成
```

当前阶段：骨架已创建。下一步将按 TASK_BACKLOG E1-C1-S1-T1 继续实现最小配置 + 搜索层。
