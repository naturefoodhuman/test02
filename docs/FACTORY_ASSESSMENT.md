<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-11 17:30:00 CST
-->

# FACTORY ASSESSMENT —— 工厂能力评估 & 改进 backlog

> ⭐ 这是"陪练"的核心产出（见 HANDOFF 0.0：工厂本身才是产品）。
> 用试点项目（debt-collection）压测工厂时，把"工厂哪里好用、哪里卡手、要改什么"记在这里。
> 这份文档比试点项目的代码更重要。

## 一、能力验证记录（✅ 表现达标 / 🟡 待观察 / ❌ 缺陷）

### DISCOVERY 阶段（第8轮压测）
| 能力 | 评估 | 证据 |
|---|---|---|
| 违法/风险红线识别（FR-001-2 补全矛盾）| ✅ | 主动调研拦截"个人非法查财产"刑事红线，重定义为合法方向 |
| 调研同类/失败案例（FR-001-3）| ✅ | 完成同类产品 + 3 类已知失败案例调研 |
| 结构化提问收敛模糊需求 | ✅ | 3 组 ask_user 把"高效要债"收敛为可执行边界 |
| 产出合规的 DISCOVERY.md（含验收草案 FR-001-4）| ✅ | 6 大必需字段齐全 + 验收标准草案 |
| forge CLI 阶段状态机 / HITL 门控 | ✅ | status/check/advance 正确识别阶段、产物、卡 GATE-1 |
| 本地模型参与 DISCOVERY | 🟡 | 本轮调研/写作由 Agent(Claude)驱动；尚未用 local/primary 实跑，能力边界待 SPEC 对比 |

## 二、发现的工厂缺陷 / 改进 backlog（按优先级）

| # | 缺陷 | 影响 | 优先级 | 状态 |
|---|---|---|---|---|
| FB-1 | forge CLI 的 `check` 只查"文件是否存在"，未真正校验文档**字段完整性**（架构书 Exit Gate 要求 DISCOVERY.md 字段完整性自动检查）| Gate 自动校验不到位，可能放过空壳文档 | 中 | TODO |
| FB-2 | 工厂全程靠 Agent 手动驱动阶段流转，没有"一键推进/记录当前阶段"的状态文件（如 .forge_phase）| 接力时要靠读文档推断阶段 | 中 | TODO |
| FB-3 | 没有"法律/领域知识注入"机制；试点涉及法律，LLM 易幻觉，但工厂的 skills/ 里无领域知识加载约定 | 专业领域项目质量无保障 | 中 | TODO |
| FB-4 | 缺少 DISCOVERY 阶段的 Skill 自动加载验证（架构书要求按需注入 Skill）| 知识注入靠 Agent 自觉 | 低 | TODO |
| FB-5 | ⭐**数据能力**未抽象为工厂通用能力：收集/整理/提炼/复用 + 多源权重分配 + 数据质量把控(辨别干货vs夹带私货) | 各项目重造轮子、数据质量无保障 | **高** | 已调研选型(来源分级+定性转量化)，待实现（老板要点2）|
| FB-6 | ⭐本地模型**无联网取数能力**，工厂缺统一"取数抽象层" | 涉及外部数据的项目无法自动取数 | **高** | ✅**L1已实现**(第13轮)：_factory/patterns/data-acquisition，8 passed+CLI实跑；L2/L3 待真机增强 |
| FB-7 | DISCOVERY 阶段缺"深度讨论自检清单"，Agent 易急于推进进 SPEC | 需求挖不深，影响落地成功率 | 中 | TODO（老板要点5）|
| FB-9 | 缺『项目级 SQLite/存储』可复用 Pattern（多数项目都要存数据） | 每项目重写存储层 | 中 | 候选(第15轮 debt-collection SPEC 暴露) |
| FB-8 | ⭐缺通用 **Ingestion 能力层**(图片/PDF/录音→结构化) | 多格式资料无法统一进 RAG/分析 | **高** | ✅**已实现**(第12轮)：_factory/patterns/ingestion-pipeline，7 passed+CLI实跑；skill已建 |

### ⭐ 老板要点 → 工厂通用能力映射（第10轮）
老板用讨债沙包提出的 6 点中，4 点是工厂级通用能力需求（这正是陪练的价值——沙包帮工厂长能力）：
- 要点2 → FB-5 数据质量与复用能力
- 要点3 → FB-6 统一取数抽象层（含"授权账号登录但须保账号安全"的硬约束）
- 要点5 → FB-7 DISCOVERY 深度自检
- 要点6 → FB-8 通用 Ingestion 层（选型见 docs/research/ingestion-tools-comparison.md）
讨债项目本身的要点（要点4 执行可行性优先）→ 已并入 debt-collection 的 AC-6。

## 二·五、工厂新增能力（已落地）
- ✅ **FB-8 Ingestion 层**（第12轮）：`_factory/patterns/ingestion-pipeline`
  - 多格式(PDF/图片/录音/Office/文本)→统一 StructuredDoc(Markdown+JSON)；核心零依赖+优雅降级；7 passed + CLI 实跑。
  - 真机增强：MinerU(中文PDF)/MarkItDown(多格式)/FunASR(录音+说话人)，缺则降级并提示。
  - 配套 skill：`_factory/skills/data-ingestion.skill.md`、`data-quality.skill.md`。
- ✅ **FB-5 数据质量机制（初步）**：data-quality.skill + 项目级 sources.yaml（系统调研初版，老板微调）。
  - 首例：`projects/debt-collection/sources.yaml`（含官方权威源分级 + 取数风险提示）。
- 这是工厂"从调研→落地一个新通用能力"的首个完整闭环，验证了工厂的造血能力。
- ✅ **FB-6 取数层 L1**（第13轮）：`_factory/patterns/data-acquisition`
  - 合规取数协调器：给债务人生成官方渠道"待查清单"+结果结构化归档；**不暴力爬/不封号/不替登录账号**。
  - 覆盖：中国执行信息公开网/裁判文书网/gsxt/国家法律法规库；三层：L1清单(已实现)+L2浏览器人在环(第14轮已实现)+L3账号(默认关)。
  - 8 passed + CLI 实跑（为"张三"生成 4 项官方渠道清单）。配套 skill：data-acquisition.skill.md。
- ✅ **FB-5 数据质量**：sources.yaml 初版 + 第13轮系统审阅建议（哪些该拉黑/如何评级），老板微调共维护。
- ✅ **Ingestion 真实接入**（第14轮）：处理器真实调用 MarkItDown/FunASR/MinerU/pypdf（修复上一版空内容占位问题）；沙箱用真 markitdown 验证 .md 真解析。
- ✅ **FB-6 L2 浏览器辅助**（第14轮）：browser_assist.py，browser-use 接 GLM，遇验证码/登录暂停等人工；CLI --l2。

## 三、能力边界结论（持续更新）
- 工厂**擅长**：把模糊想法结构化、识别风险红线、产出规范文档、用 CLI 管理阶段与门控。
- 工厂**当前弱项**：自动校验深度不足（只查存在性）、领域知识注入缺机制、阶段流转自动化程度低。
- 这些弱项**正是后续要打磨工厂的方向**（比做完讨债项目本身更有价值）。

## 变更记录
| 时间(CST) | 变更 | 模型 |
|---|---|---|
| 2026-06-11 17:30:00 | 初版：DISCOVERY 阶段压测记录 + 4 个改进项 | Claude Sonnet 4.5 |
