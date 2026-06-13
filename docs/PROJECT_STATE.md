<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# PROJECT STATE —— 当前进度快照

> 接续 Agent：这是"我们现在在哪、下一步去哪"的唯一权威。先读 `HANDOFF.md`，再读本文件。

---

## 当前总进度

**演进路线**（来自架构书第 9 章）：
- **Phase 1：基础设施**（搭骨架）← ✅ 核心链路全部打通（本地/网关/GLM流式/Fallback/CLI/Pattern）
- Phase 2：首个试点项目（走通五阶段）← 🟡 **BUILD 骨架完成**：debt-collection 13任务完成12(55测试全绿)，仅剩 model-ab-test(需真机)
- Phase 2：首个试点项目（走通五阶段）← ⬜ 未开始
- Phase 3：多项目并行 ← ⬜ 未开始

---

## Phase 1 退出条件勾选表（架构书第 9 章）

| 退出条件 | 状态 | 说明 |
|---|---|---|
| Ollama 模型已就绪（35b + 14b 在列） | ✅ 真机确认 | 待验对话 V-Ollama |
| LiteLLM Proxy 启动成功（3 模型加载） | ✅ 真机确认 | 终端 A 已跑通 |
| LiteLLM Proxy → Ollama 链路 | ⬜ 待真机 | 待跑 V-LiteLLM 的 curl |
| LiteLLM → GLM 链路 | ✅ | 第8轮闭环：Key 填对后流式+非流式全绿(diag-v2 A1~B3)。旧"非流式不稳"是 Key 错误假象 |
| Fallback (GLM挂切本地) | ✅ | 已观察生效 |
| 本地扩充模型(coder+2 embedding) | ⬜ 待真机 | 配置已加，待跑 V-LocalModels |
| forge CLI / Pattern 真机测试 | ✅ 真机确认 | 19 passed / 5 passed |
| Fallback 验证（GLM 挂自动切本地） | ⬜ 待真机 | 配置已写 |
| Hooks：测试自动运行 + 熔断 | ✅ 沙箱已验证 | 熔断第5次 exit 2 已实测通过，真机复核 V-Hooks |
| `_factory/` 基础结构（≥3 Skill + 1 Pattern） | ✅ 完成 | 5 个 Skill + fastapi Pattern（core 测试已过） |

---

## 本轮（第 1 轮）目标 —— 全部完成 ✅

1. ✅ 接力维护文档体系（HANDOFF + PROJECT_STATE + DEV_LOG + DECISIONS + CHANGELOG + REAL_MACHINE_VALIDATION）
2. ✅ `_infra/`：litellm-config.yaml、model-routing-rules.md、forge-cli.sh、setup.sh、.env.example、CLAUDE.global.md
3. ✅ Hooks 脚本（post-tool-use / pre-commit / test-runner / lint-runner）—— 熔断已实测
4. ✅ `_factory/`：Skill 模板 + 4 个 Skill（discovery/arch/tdd/security）+ fastapi Pattern（可运行）+ lesson 模板
5. ✅ `_agents/`：arch-advisor / security-reviewer / code-explorer / retro-analyst
6. ✅ 全局 CLAUDE.md 模板 + 项目级 AGENTS.md/CLAUDE.md/coder/reviewer 模板
7. ✅ `forge` CLI（Python，零三方依赖）：状态机 + TASK_GRAPH 解析 + Gate 流转 + 文档校验
8. ✅ 测试：forge_tools **19 passed**；Pattern core **3 passed**；Hooks 熔断实测通过
9. ✅ 真机验证清单（含 GLM 404 坑的应对）
10. ✅ README + .gitignore 重写 + 补丁包

---

## 下一步（接续 Agent / 老板从这里继续）

**1. 收官 Phase 2 试点项目 (debt-collection)**
- ✅ 核心功能/安全自检/RETRO 记录。
- ✅ **HITL Gate-5 已通过**：项目正式结项，Lesson 已沉淀。
- ✅ **模型路由修复**：已实现“在线(GLM) -> 本地(35b) -> 离线模板”的三级降级机制。

**2. 启动 Phase 2.5: 工厂智力升级 (FB-11 专家系统)**
- ✅ **债务律师专家已初始化**：完成目录结构、`expert.yaml`、路由配置（新增 DeepSeek-R1）。
- ✅ **知识库库 A/B 初始化**：录入民间借贷/执行程序司法解释、92 条实务问答。
- ⏳ **知识获取**：按照 R6 规则，已在 `_gaps.md` 列出《民间借贷纠纷办案手册》等缺口，待老板提供。

**3. 持续打补丁 (FB-1/2/9/10)**
- 改进 forge CLI 校验深度 (FB-1)。
- 引入显式阶段状态 `.forge_phase` (FB-2)。
- 探索项目级存储 Pattern (FB-9)。

---

## 变更记录

| 时间(CST) | 变更 | 模型 |
|---|---|---|
| 2026-06-10 23:03:36 | 初版创建 | Claude Sonnet 4.5 |
| 2026-06-10 23:30:00 | 第1轮收尾：基础设施骨架全部完成，更新勾选表与下一步 | Claude Sonnet 4.5 |
| 2026-06-10 23:55:00 | 第2轮：GLM 改 ModelScope、修 setup.sh、澄清 Claude Code 接入 | Claude Sonnet 4.5 |
| 2026-06-11 09:40:00 | 第3轮：修模型名乱码、litellm venv 探测；真机进度更新 | Claude Sonnet 4.5 |
| 2026-06-11 12:30:00 | 第4轮：GLM链路诊断(stream_timeout+glm-debug+diag脚本)；两条新流程规则 | Claude Sonnet 4.5 |
| 2026-06-11 15:10:00 | 第5轮：GLM根因定位(缺export Key)；新增 start-litellm.sh；流式已通 | Claude Sonnet 4.5 |
| 2026-06-11 15:45:00 | 第6轮：澄清GLM身份偏差；新增 verify-glm.sh；**Phase 1 收尾** | Claude Sonnet 4.5 |
| 2026-06-11 16:30:00 | 第7轮：诊断脚本 v2（流式/非流式分测+ModelScope对照） | Claude Sonnet 4.5 |
| 2026-06-11 17:00:00 | 第8轮：GLM根因闭环(Key错)；扩充本地模型coder+embedding；固化"工厂是产品"定位 | Claude Sonnet 4.5 |
| 2026-06-11 17:30:00 | 第9轮：用debt-collection沙包压测DISCOVERY；产出DISCOVERY.md+FACTORY_ASSESSMENT；待GATE-1 | Claude Sonnet 4.5 |
| 2026-06-11 18:10:00 | 第10轮：老板补充6点；资料整理工具横向对比；DISCOVERY深挖+AC-6；工厂backlog FB-5~8 | Claude Sonnet 4.5 |
| 2026-06-11 18:40:00 | 第11轮：取数(browser-use/封号)+数据质量可行性评估；定L1/L2/L3取数方案；定先建FB-8 | Claude Sonnet 4.5 |
| 2026-06-11 22:10:00 | 第12轮：建成FB-8 Ingestion层(7passed+CLI实跑)；data-ingestion/quality skill；sources.yaml初版 | Claude Sonnet 4.5 |
| 2026-06-11 23:10:00 | 第13轮：建成FB-6 L1取数层(8passed+CLI实跑)；sources.yaml审阅建议；Ingestion真机验证脚本 | Claude Sonnet 4.5 |

| 2026-06-12 00:10:00 | 第15轮：SETUP_GUIDE(MinerU/torch/browser-use选型)；--bu-model切换；产出SPEC+5ADR+TASK_GRAPH(待Gate-2) | Claude Sonnet 4.5 |

| 2026-06-12 00:50:00 | 第16轮：R1/R2规则；MinerU真实接入；修根目录污染；SPEC升级动态博弈(ADR-006)；进BUILD(核心7任务,13passed) | Claude Sonnet 4.5 |

| 2026-06-12 01:30:00 | 第17轮：浏览器工具三条腿选型；BUILD搭满(knowledge/strategy/cli端到端,18passed) | Claude Sonnet 4.5 |

| 2026-06-12 02:10:00 | 第18轮：规则R3；RUNBOOK保姆级验证步骤；HARDEN清单+自检脚本(11项全过) | Claude Sonnet 4.5 |

| 2026-06-12 02:40:00 | 第19轮：HARDEN决策落地(report --model可选)；SECURITY_REVIEW(无高危)；五阶段进HARDEN | Claude Sonnet 4.5 |

| 2026-06-12 03:00:00 | 第20轮：RETRO模板+lesson草稿+真机数据收集脚本；待老板push真机数据 | Claude Sonnet 4.5 |

| 2026-06-12 16:00:00 | 第21轮：R4遥测Pattern+实时计时器；合规v2(否定语境修复误判+递归整改)；真机数据分析填RETRO；62测试全绿 | Claude Sonnet 4.5 |

| 2026-06-12 17:30:00 | 第22轮：真机修复确认；Claude策略报告对比;反封号详尽调研+Higgsfield澄清;FB-10 | Claude Sonnet 4.5 |

| 2026-06-12 18:30:00 | 第23轮：规则R5/R6;开源模型全景调研;专家系统FB-11(设计+模板);工厂运转手册 | Claude Sonnet 4.5 |
| 2026-06-13 09:00:00 | 第24轮：接续 Agent 接手；确认 Phase 2 试点项目收官；提议启动 FB-11 专家系统 | Claude Sonnet 4.5 |
