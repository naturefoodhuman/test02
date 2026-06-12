<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-12 18:30:00 CST
-->

# FACTORY OPERATIONS —— 工厂怎么运转（老板第23轮）

> 回答："接下来我们的工厂要怎么运转？" 这是工厂从"建好"到"投产"的运行手册。

## 一、工厂现状（已具备的能力）
- **五阶段流水线**：DISCOVERY→SPEC→BUILD→HARDEN→RETRO（forge CLI 驱动 + HITL 门控）。
- **模型层**：LiteLLM 网关(本地 qwen ×3 + embedding ×2 + GLM 云端 + 离线兜底)。
- **通用能力 Pattern**：ingestion(资料整理)、data-acquisition(合规取数 L1/L2)、data-quality(来源分级)、llm-telemetry(遥测)、fastapi-backend(脚手架)。
- **知识体系**：skills(7)、patterns(5)、lessons、sources.yaml、即将上线的 **experts(专家系统)**。
- **规则体系**：R1 模型不限本地 / R2 决断先调研 / R3 操作保姆级 / R4 全程遥测 / R5 调研穷尽 / R6 缺知识求助不假装。
- **试点验证**：debt-collection 走通全五阶段(55+测试)。

## 二、工厂的运转模式（标准作业流程 SOP）
当老板提出一个新项目想法，工厂这样跑：

```
0. 想法     老板一句话想法
   ↓
1. DISCOVERY  Agent 调研(R5穷尽) + 拦红线 + 结构化提问 → DISCOVERY.md → HITL Gate-1
   ↓
2. SPEC      架构+ADR+任务图；★识别需要哪些"专家"，没有就先建专家 → HITL Gate-2
   ↓
3. BUILD     复用工厂 Pattern + 专家知识库；TDD；全程遥测(R4) → Hooks 门控
   ↓
4. HARDEN    安全/合规/隐私自检 + 决策(模型/加密) → HITL Gate-4
   ↓
5. RETRO     复盘"项目+工厂"；沉淀 lesson + 新 skill/pattern/expert → HITL Gate-5
```
每个项目都让工厂**更强**：新增可复用的 skill/pattern/expert，下个项目更快更好（复利）。

## 三、决策大脑 = 专家系统（核心升级，老板第23轮）
- 工厂的"智力上限"不只取决于 LLM，而取决于 **LLM + 沉淀的领域知识(专家系统)**。
- 每个领域项目先问："需要哪些专家？已有吗？" 没有→先建专家(四件套，见 expert-system-design.md)。
- 专家知识来自：书籍/指南/专家共识/行业规范/顶级论文/论坛报告/优质博客 → ingestion 结构化 → RAG。
- **缺知识就求助老板(R6)**，不假装。专家持续更新，越用越强。

## 四、外源知识的获取分工（弥补本地模型不够顶级）
| 知识类型 | 谁来获取 | 怎么获取 |
|---|---|---|
| 官方公开(法规/失信/工商) | 工厂自动 | data-acquisition L1 |
| 社交/论坛/博客 | 工厂半自动 | MediaCrawler + 代理(个人研究级) + 质量分级 |
| 网页文章(微信公众号等) | 老板人工辅助 | 老板浏览器打开→保存本地→工厂 ingestion |
| 付费文献(知网) | 老板人工辅助 | 老板下载摘要/全文→工厂 ingestion |
| 书籍/专著 | 老板代下载(R6) | Agent 列缺口清单→老板提供电子版→工厂 ingestion |
| 顶级闭源模型意见 | 老板人工(C1) | Manual Gate：文档→ChatGPT/Claude 网页→存回 external-review/ |

## 五、下一步路线（建议）
1. **收官当前试点**：debt-collection 走完 RETRO + Gate-5（验证五阶段闭环）。
2. **建专家系统(FB-11)**：把"债务律师专家"从讨债抽象为首个独立专家，跑通专家范式。
3. **沉淀运营机制**：以后每个新项目按本 SOP 运转，每轮让工厂长能力。
4. **持续补强 backlog**：FB-1~11（校验/阶段自动化/领域知识/存储Pattern/反封号/专家系统）。

## 六、老板要做的事（人机分工）
- **战略决策**：做什么项目、接受什么风险、过 HITL Gate、知识缺口代获取(R6)。
- **工厂(Agent)执行**：调研/设计/编码/测试/沉淀/遥测。
- 老板是产品负责人 + 知识供给者；工厂是可复利的执行与决策大脑。

## 变更记录
| 时间(CST) | 变更 | 模型 |
|---|---|---|
| 2026-06-12 18:30:00 | 初版：工厂运转 SOP + 专家系统 + 外源知识分工 + 路线 | Claude Sonnet 4.5 |
