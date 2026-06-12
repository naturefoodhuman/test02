<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-12 03:00:00 CST
-->

# RETRO —— debt-collection 试点复盘（Phase 5）

> ⚠️ 双重视角（本项目是工厂陪练，见 HANDOFF 0.0）：
> ① 对**试点项目本身**复盘；② 对**工厂**复盘（更重要——工厂才是产品）。
> 含【🟦 待真机数据】占位，等老板真机验证结果 push 回来后由 Agent 拉取填入。

---

## A. 试点项目（debt-collection）复盘

### A1. 成功经验（可复用）
- "动态案件博弈"建模（情报库+时间线+策略重算）比"一次性报告"贴近真实讨债——这是老板的关键洞察，应作为同类"持续博弈型"项目的范式。
- compliance 红线守门人 + knowledge 防法律幻觉，是法律类项目的标配双保险。
- 离线模板兜底：无 GLM 也能产出结构化报告，保证可用性下限。
- 复用工厂能力（ingestion/acquisition/data-quality）而非重造，SPEC→BUILD 提速明显。

### A2. 失败经验（避坑）
- 第一版处理器只"检测到库"不真正调用 → 输出空（第13轮才修）。**教训：集成外部工具必须真实端到端验证，不能只写接入点占位。**
- 默认把测试产物放用户根目录 → 污染（第16轮才改 runtime/）。**教训：产物默认放项目内。**
- 误以为"个人能查他人财产" → 调研后发现违法。**教训：领域项目先做合规调研。**

### A3. 改进建议（V2）
- 🟦 待真机：根据 GLM 实际策略质量，决定是否需要更强法律模型/RAG 接入判例。
- 社交情报(MediaCrawler)接入 intel 自动化（当前需手动）。
- DB 加密（SQLCipher）作为 V2 隐私增强。
- 文书生成（律师函/起诉状要点）作为独立 feature。

### A4. 五阶段执行记录
| 阶段 | 结果 | 备注 |
|---|---|---|
| DISCOVERY | ✅ | 拦截违法红线、6点补充意见 |
| SPEC | ✅ | 6 ADR；动态博弈升级(ADR-006) |
| BUILD | ✅ 12/13 | 55 测试全绿；model-ab-test 待真机 |
| HARDEN | ✅ | 自检11项过、无高危、决策落地(--model) |
| RETRO | 🟡 | 本文档 |

---

## B. 🏭 工厂复盘（核心产出）

### B1. 工厂验证通过的能力
- 五阶段状态机 + HITL 门控（forge CLI）真实驱动了一个完整项目。
- 能力可复用：试点直接调用了 ingestion/acquisition/data-quality 三个工厂 Pattern。
- 模型路由 + 离线降级：GLM/本地/离线三级可用。
- 规则体系（R1 模型不限本地 / R2 决断先调研 / R3 操作保姆级）有效约束了协作质量。

### B2. 工厂改进 backlog 状态（来自 FACTORY_ASSESSMENT）
| 编号 | 内容 | 状态 |
|---|---|---|
| FB-1 | forge check 只查文件存在，未校验字段完整性 | TODO |
| FB-2 | 阶段推断靠产物存在性，不准(需 .forge_phase) | TODO |
| FB-3 | 领域知识注入机制 | 部分(knowledge 是项目级,未抽象到工厂) |
| FB-5 | 数据质量(来源分级/定性转量化) | 已落 skill+sources.yaml |
| FB-6 | 取数层(L1清单/L2浏览器/L3) + 工具选型 | L1/L2 已建 |
| FB-8 | Ingestion 层 | ✅ 已建并真实接入 |
| FB-9 | 项目级存储 Pattern | 候选(debt 自建了 SQLite，可抽象) |

### B3. 工厂能力边界结论
- 🟦 待真机：本地 35b vs GLM 在"策略推理/架构设计"上的真实质量差距（model-ab-test）。
- 工厂擅长：结构化、风险拦截、规范产出、能力复用。
- 工厂当前弱项：自动校验深度(FB-1)、阶段自动化(FB-2)、领域知识注入工厂化(FB-3)、存储 Pattern(FB-9)。

### B4. 本试点为工厂新增的可复用资产（AC-008）
- 新 Skill：data-ingestion、data-quality、data-acquisition（3 个）。
- 新 Pattern：ingestion-pipeline、data-acquisition（2 个，均可运行+测试）。
- 新调研文档：资料整理工具对比、取数可行性、浏览器工具选型。
- → **远超 AC-008"每项目≥1 个新 Skill/Pattern"的要求。**

---

## C. 模型与成本（用于优化路由矩阵，AC-002/003）
- 🟦 待真机：各 Phase 耗时。
- 🟦 待真机：GLM 调用次数 / 估算成本。
- 🟦 待真机：本地模型占比（目标 ≥80%，AC-003）。
- 沙箱阶段：开发/测试全程零云端调用（纯逻辑+离线兜底）。

---

## D. 🟦 真机验证结果（等老板 push 后填）
> 老板 push `runtime/retro-data/*.txt` 后，Agent git pull 拉取，把以下填实：
- [ ] BUILD 测试结果（pytest，期望 18 passed）：________
- [ ] security_scan 结果（期望 11 项全过）：________
- [ ] GLM 策略报告样例（report --model cloud/glm-primary）：________
- [ ] 离线/本地 策略报告样例（对比用）：________
- [ ] GLM vs 本地 质量主观对比结论：________
- [ ] Ingestion 真实解析效果（MinerU 扫描件 / FunASR 录音）：________

## 退出门控
- 强制产出：本 RETRO + _factory/lessons/ 的 lesson 文件。
- 人工：HITL Gate-5（写入 _factory/ 的内容需老板审批，防错误知识污染）。
