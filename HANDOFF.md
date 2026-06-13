<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-13 14:40:00 CST
-->

# HANDOFF —— 接力交接文档（意外中止时，接续 Agent 必读）

> 这份文档的唯一目的：**让任何一个全新的 Agent，在不依赖原始对话的情况下，能在 5 分钟内接手本项目并继续开发。**
> 如果你是接手的 Agent：**先读完本文件，再读 `docs/PROJECT_STATE.md` 和 `docs/DEV_LOG.md`，然后才能动手。**

---

## 0.0.1 ⭐ 工作规则（老板第16-24轮修订，必须遵守）

- **R1 · 模型选型不限于本地已有**：涉及开源模型时，若某任务有**更合适的开源模型**，要主动建议老板（前提：本机硬件能满足，M1 Max 64GB）。
- **R2 · 决断前先调研主流方案**：任何需要老板做决断的点，**先调研当前世界上最新最主流的备选方案**（用 web 搜索），增加**反方评估**。
- **R3 · 操作指示必须保姆级详细**：给老板的每条操作指示都要写清——终端编号、绝对路径、虚拟环境激活命令、预期输出。
- **R4 · 所有 LLM 工作必须记录遥测**：每次 LLM 完成工作都要记录【事件+耗时+模型+成败等】。
- **R5 · 决策调研必须穷尽**：任何关键决策必须尽力把全世界能查到的主流方案调研清楚，而非找到一个能用的就停。
- **R6 · 知识获取不到要主动求助，不许假装**：建设领域专家时，若关键知识获取不到，必须明确告诉老板，征询是否由老板代为提供。
- **R7 · 文件头规范强制执行**：每个新建/修改的代码或文档头部必须注明 LLM 名称和北京时间。

## 0.0 ⭐ 项目定位

- **我们真正的产品 = 这套"AI 项目孵化工厂"本身**。
- 试点项目（如讨债系统）是“陪练沙包”，用来压测工厂。
- 重心永远是"工厂好不好用、边界在哪"。

---

## 2. 当前运行环境的真相（非常重要，别踩坑）

| 维度 | 老板的真机（目标环境） | 我们（Agent）的沙箱 |
|---|---|---|
| 系统 | macOS Sequoia 15.6.1 | Linux 云沙箱 |
| 芯片 | Apple M1 Max 64GB | x86 容器 |
| Python | 3.11 / 3.12 (MinerU) | 3.13（沙箱） |
| **MinerU 环境** | `projects/debt-collection/runtime/mineru_env` | 无 |
| **本地模型** | Ollama: deepseek-r1:32b (Primary Reasoning) / qwen3.6:35b (Execution) | 无 |
| **云端模型** | Pekpik (GPT-5.5) / SiliconFlow (DeepSeek-R1) / GLM | 无 |

**关键路径说明：**
- 项目根目录：`/Users/naturist/MusicProject/AI-Project-Incubation-Factory`
- 虚拟环境激活：`source .venv/bin/activate` (常规) 或 `source projects/debt-collection/runtime/mineru_env/.venv/bin/activate` (MinerU)

---

## 7. 维护文档清单（每轮必须同步更新）

| 文档 | 作用 |
|---|---|
| `HANDOFF.md` | 本文件，环境真相、规则、红线 |
| `docs/PROJECT_STATE.md` | 当前进度快照 + 下一步 + 待办 |
| `docs/DEV_LOG.md` | 逐轮开发日志 |
| `docs/DECISIONS.md` | 决策记录 |

---

## 8. 变更记录（本文件自身）

| 时间(CST) | 变更 | 模型 |
|---|---|---|
| 2026-06-10 23:03:36 | 初版创建 | Claude Sonnet 4.5 |
| 2026-06-13 14:40:00 | 重写：更新 MinerU 路径、R1 本地化、操作规范、R7 规则 | Claude Sonnet 4.5 |
