<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# 模型路由决策规则（人类可读）

> 这份文档是给人看的"为什么这样路由"。机器可读的路由由 `litellm-config.yaml` 的 fallbacks 实现。
> 原则：**高频任务用零成本本地模型；架构/安全等高质量节点用 GLM；GLM 挂了自动回退本地，不中断。**

## 路由决策矩阵

| 任务类型 | 首选 | Fallback-1 | Fallback-2 |
|---|---|---|---|
| 代码生成（标准，<100行） | local/primary | local/fallback | cloud/glm |
| 代码生成（复杂，跨文件重构） | cloud/glm | local/primary | local/fallback |
| 单测生成 | local/primary | local/fallback | — |
| 集成测试生成 | local/primary | cloud/glm | local/fallback |
| 架构设计 / ADR | cloud/glm | local/primary | Manual Gate |
| 安全审查（HARDEN） | cloud/glm | local/primary | Manual Gate |
| 代码探索（read-only） | local/primary | local/fallback | — |
| 依赖分析 / 文档摘要 | local/primary | local/fallback | — |
| 复杂推理 / 规划 | local/primary | cloud/glm | local/fallback |
| 复盘分析（RETRO） | local/primary | local/fallback | — |

- **Manual Gate** = 人工把文档送往 ChatGPT/Claude 网页端，结果手动写入 `docs/external-review/`（C1）。
- **GLM 不可用时**：LiteLLM 的 fallbacks 自动把 `cloud/glm-primary` 切到 `local/primary`，工作流不中断；
  仅在 RETRO 的 BUILD_LOG 记一笔"GLM 不可用，使用本地模型"。
- **对安全审查等高质量节点**：降级后必须在该阶段的 Exit Artifact 标注 **"待人工复核"**。

## 怎么在 Claude Code 里"选模型"

Claude Code 默认调一个模型名；要切到不同 forge 模型，方式有二：
1. 在 Claude Code 的模型设置里把模型名填成 LiteLLM 的 `model_name`（如 `cloud/glm-primary`）。
2. 或保持默认走 `local/primary`，需要 GLM 时由 Orchestrator（全局 CLAUDE.md 指引）提示老板手动切换。

> 注意：本矩阵是"建议"，最终由全局 CLAUDE.md 的"模型路由偏好"驱动 Orchestrator 行为。

## 变更记录
| 时间(CST) | 变更 | 模型 |
|---|---|---|
| 2026-06-10 23:03:36 | 初版，复刻架构书 3.2 路由矩阵 | Claude Sonnet 4.5 |
