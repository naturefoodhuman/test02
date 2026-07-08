<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-07-09 01:15:00
-->

# AI Parenting Copilot

家庭私有化 AI 育儿副驾驶系统。项目级源码与文档均位于
`projects/AI-Parenting-Copilot/`，不得把工厂根目录 Backlog 或 FEOS/Network 文档
当作本项目任务来源。

## 项目入口

- 项目架构基线：`docs/ARCHITECTURE_FINAL.md`
- 工程实现蓝图：`docs/ENGINEERING_DESIGN.md`
- 任务状态与验收：`docs/TASK_BACKLOG.md`
- 当前状态：`docs/PROJECT_STATE.md`
- 开发流水：`docs/DEV_LOG.md`
- 变更记录：`docs/CHANGELOG.md`
- 接手入口：`docs/HANDOFF.md`
- 工厂能力背景：工厂根目录 `../../PROJECT_DOSSIER_V5.md`

> 注意：项目内旧拷贝 `docs/PROJECT_DOSSIER_V5.md` 不是本项目执行 SSOT；如需工厂能力背景，直接读取工厂根目录 `PROJECT_DOSSIER_V5.md`。

## 当前实现状态

当前完成：`APC-T001`、`APC-T002`、`APC-T005`、`APC-T024`、`APC-T025`；`APC-T003/T004/T006/T007/T008` BLOCKED。

- 已创建项目骨架、基础配置、维护文档与 ADR。
- 已实现 FastAPI 应用壳、Settings、DI、公共错误、ULID、timezone-aware clock、Repository Protocol 与事件总线占位。
- 已实现 structlog JSON 日志、PII mask、Prometheus `/metrics`、OpenTelemetry 安全降级、请求日志 middleware 与健康端点。
- 已实现本地基础设施、Alembic 配置、核心 schema migration 与审计服务；因当前沙盒无 Docker/PostgreSQL，相关集成验收待用户 Mac 或可用 Docker 环境完成。
- 已实现 Model Gateway 与 Privacy Gateway 适配。
- 已实现 Auth/RBAC/JWT 与 dev/in-memory Auth API / seed 脚本；真实 DB 持久化待 PostgreSQL 验收。
- Android / firmware 目录已预留。

## 本地命令

```bash
cd projects/AI-Parenting-Copilot
make docs-check
make lint
make typecheck
make test
```

说明：`APC-T001` 阶段尚未引入完整服务端依赖；`lint` / `typecheck` 会在本地安装
`ruff` / `mypy` 时执行正式检查，否则给出明确跳过提示并保持骨架验证可运行。

## 架构保护

开发必须遵守：

1. 不改变 `docs/ARCHITECTURE_FINAL.md` 中的架构边界。
2. Factory-first：复用工厂 `_infra/`、Smart Proxy、Privacy Gateway、Local RAG、governance。
3. LLM 只经 Model Gateway。
4. 云端出站只经 Privacy Gateway。
5. 剂量、阈值、医疗判断只由 Rule Engine 产出。
6. 所有 mutating 操作必须审计；审计日志不可删除。
