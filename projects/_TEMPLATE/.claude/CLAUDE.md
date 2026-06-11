<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# CLAUDE.md — 项目级（Claude Code 专属配置）

> 这是项目级配置模板。AGENTS.md 是工具无关主入口，本文件是 Claude Code 专属的 Hooks/Subagent 注册。

## Hooks
### post-tool-use
任何 write/edit/create 工具执行后：运行 `.claude/hooks/post-tool-use.sh`（自动跑测试 + 熔断）。

### pre-commit
提交前：运行 `.claude/hooks/pre-commit.sh`（lint + TASK_GRAPH 状态检查）。

## Subagents
- `coder`（见 `.claude/agents/coder.md`）：BUILD 阶段，local/primary，可写 src/tests/，禁改 docs/。
- `reviewer`（见 `.claude/agents/reviewer.md`）：测试/lint 把关。

## 权限红线（由 Hooks 强制，不靠 Prompt）
- `docs/SPEC.md`、`docs/adr/` 只读，coder 禁改。
- BUILD 阶段每个 Task 完成必须更新 `docs/TASK_GRAPH.md` 的 status。
- 境外模型输出只能经 `docs/external-review/` 进入，不直接改代码。
