<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-12 02:40:00 CST
-->

# SECURITY_REVIEW —— debt-collection（HARDEN Artifact）

> ⚠️ 本次安全审查由本地 Agent(Claude)执行；**待真机用 GLM 复核**(标注：待人工/GLM复核)。
> 自动自检见 security_scan.sh（沙箱已跑：11 项全过）。

## 威胁建模发现
| 项 | 状态 | 说明 |
|---|---|---|
| 敏感数据外泄 | 🟢 缓解 | 本地 SQLite + .gitignore(runtime/*.db/data) + 身份证脱敏；策略模型可选本地(不出本机) |
| 案件事实发云端 | 🟡 已知 | GLM 模式案件事实发 ModelScope；已加 --model 让用户对敏感案件选本地 |
| 法律幻觉 | 🟢 缓解 | knowledge 提供可信法条 + 免责声明 + 建议律师复核 |
| 违法催收建议 | 🟢 缓解 | compliance 拦 8 类入刑行为+非法查信息+骚扰第三人；strategy 强制过自检 |
| 取数封号/违法 | 🟢 缓解 | 仅 L1/L2，不自动爬强风控/非法查；社交情报经质量分级 |
| 输入异常崩溃 | 🟢 缓解 | DB/LLM/文件 IO 有异常处理与降级路径 |

## 高危项
- 无已知高危。最大注意点=GLM 模式案件事实出云端→已提供本地模型选项规避（HARDEN 决策1）。

## 待复核（降级标注）
- 本审查为本地 Agent 出具，建议真机起 GLM 网关后用 cloud/glm-primary 做一次安全复核。
