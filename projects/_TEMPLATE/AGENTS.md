<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# AGENTS.md — 项目主入口（工具无关规范）

> ⭐ 这是项目的**工具无关主入口**（KR-002-3）。即使换掉 Claude Code，这份规范还在。
> 兼容 Claude Code / Codex CLI / Cline / Roo Code 等的读取方式。

## 项目身份
- 项目名：`<填项目名>`
- 类型：`<CLI / Web后端 / RAG / MCP ...>`
- 当前 Phase：`DISCOVERY`（随进展更新，这是活文档 KR-002-2）

## 架构约定（SPEC 阶段填）
- 技术栈：…
- 关键模块：…
- ADR 摘要：见 `docs/adr/`

## 编码规范（继承全局，需求 8.4）
- PEP 8，函数签名带类型注解。
- 关键函数中文 docstring（Google 风格）。
- 复杂逻辑加行内中文注释；关键决策点注明理由。
- 面向用户输出强制中文；异常日志英文原文 + 中文注释。
- 每个新建/修改文件头部写"LLM 模型名 + 北京时间(秒)"。

## 质量门控
- 代码变更后跑测试（Hooks 自动）。
- 任务完成更新 `docs/TASK_GRAPH.md`。
- 提交前 lint + TASK_GRAPH 无 IN_PROGRESS。

## 配置管理
- 可变参数走 `config.yaml` / env，禁止硬编码（需求 8.6）。
- 提供 `.env.example`。

## 五阶段与 Gate
- DISCOVERY → SPEC → BUILD → HARDEN → RETRO
- HITL Gate-1..5 不得绕过（见 HANDOFF / 架构书 5）。
