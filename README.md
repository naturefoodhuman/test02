<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# FORGE Factory（AI 项目孵化工厂）

> 在 macOS M1 Max 单机上，把"模糊想法"反复、可重复地变成"能跑的 AI 软件项目"的工作体系。
> 不是一个单体软件，而是 **脚手架 + 配置 + 脚本 + 知识库 + 五阶段工作流**，驱动 VS Code 里的 Claude Code 运行。

## 快速开始
```bash
bash _infra/setup.sh --check          # 环境自检
cp _infra/.env.example _infra/.env    # 填 GLM_API_KEY 等
cd _infra/forge_tools && uv pip install -e ".[dev]" && python -m pytest -q   # forge CLI 自测
```
完整真机验证见 `docs/REAL_MACHINE_VALIDATION.md`。

## 目录速览
```
.
├── HANDOFF.md                 # ⭐ 接力总入口（意外中止时接续 Agent 必读）
├── README.md                  # 本文件
├── _infra/                    # 基础设施：LiteLLM 路由 / 环境 / Manual Gate / forge CLI
│   ├── litellm-config.yaml    # 模型路由 + Fallback + 成本日志
│   ├── model-routing-rules.md # 路由决策（人类可读）
│   ├── forge-cli.sh           # Manual Gate 辅助（境外模型手动接入）
│   ├── setup.sh               # 一键自检
│   ├── .env.example           # 环境变量模板
│   ├── CLAUDE.global.md       # 全局 Orchestrator 配置模板（→ ~/.claude/CLAUDE.md）
│   └── forge_tools/           # forge CLI（Python，零三方依赖，沙箱已测 19 passed）
├── _factory/                  # 工厂知识库（跨项目共享）
│   ├── skills/                # 5 个技能（discovery/arch/tdd/security + 模板）
│   ├── patterns/              # 可运行脚手架（fastapi-backend，core 测试已过）
│   └── lessons/               # 复盘模板
├── _agents/                   # 全局 Agent 定义（arch/security/explorer/retro）
├── projects/                  # 项目目录
│   └── _TEMPLATE/             # 新项目脚手架（含 .claude Hooks + docs 全套模板）
└── docs/                      # 需求书/架构书 + 维护文档体系
```

## 五阶段
DISCOVERY → SPEC → BUILD → HARDEN → RETRO，每阶段有进入条件、退出产物、HITL Gate。

## forge CLI 常用命令（在项目目录内）
```bash
forge status     # 当前阶段 + 任务图概览
forge check      # 校验任务图（status/依赖/循环）+ 退出产物
forge tasks      # 列出可执行任务（依赖已满足）
forge advance    # 能否进入下一阶段 + 需过哪个 Gate
forge gate GATE-2
```

## 给接手的人 / Agent
出问题或要接续开发，先读 `HANDOFF.md`，再读 `docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、`docs/DECISIONS.md`。
