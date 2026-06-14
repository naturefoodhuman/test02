<!--
创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
-->

# CHANGELOG —— 需求增删改 + 变动说明

> 老板每轮提出的"新增 / 删除 / 改动"需求，以及由此产生的文件变动，都记在这里。
> 格式：每轮一节，列出【需求变动】和【文件影响】。

---

## [第 1 轮] 2026-06-10

### 需求变动
- **新增**：建立 FORGE Factory 基础设施骨架（Phase 1）。
- **新增**：接力维护文档体系（应对意外中止可接续）—— 来自特殊要求 #1。
- **新增**：每轮需求增删改要同步到相关文档并写变动说明 —— 来自特殊要求 #2（本 CHANGELOG 即其落地）。
- **新增**：每轮改动后打 zip 补丁包 —— 来自补丁约定。

### 文件影响（新增）
- `HANDOFF.md`（接力总入口）
- `docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、`docs/DECISIONS.md`、`docs/CHANGELOG.md`、`docs/REAL_MACHINE_VALIDATION.md`
- `_infra/`、`_factory/`、`_agents/`、`projects/` 目录骨架及其内容（本轮陆续生成，见 PROJECT_STATE.md 勾选表）

### 文件影响（本轮最终清单）
**新增（_infra）**：litellm-config.yaml、model-routing-rules.md、forge-cli.sh、setup.sh、.env.example、CLAUDE.global.md、forge_tools/（pyproject + src/forge/{__init__,task_graph,phases,cli}.py + tests/{test_task_graph,test_phases,test_cli}.py）
**新增（_factory）**：skills/{_TEMPLATE,discovery-interview,arch-design,tdd-cycle,security-review}.skill.md、patterns/fastapi-backend/（README+pyproject+src/app/{__init__,core,config,main}.py+tests/{unit,integration}）、lessons/_TEMPLATE.lesson.md
**新增（_agents）**：arch-advisor、security-reviewer、code-explorer、retro-analyst
**新增（projects/_TEMPLATE）**：AGENTS.md、.claude/{CLAUDE.md,hooks/*,agents/*,*-runner.sh}、docs/{DISCOVERY,SPEC,RISK,BUILD_LOG,TASK_GRAPH}.md、docs/{adr,specs,harden,external-review}/*
**新增（根/docs）**：README.md、docs/REAL_MACHINE_VALIDATION.md
**改动**：`.gitignore` 由上个项目（soundproof-agent）残留规则改写为契合 forge 体系。

### 说明
- 这是项目第一轮，绝大多数为"从无到有"的新增，无删除/改动既有需求。
- GLM 型号/Key 为"待补全"状态（占位 glm-5.1），属约定中的占位，非遗漏。

---

## [第 2 轮] 2026-06-10

### 需求变动
- **改动**：GLM 云端接入由"智谱官网占位"改为"经 ModelScope（魔搭）接入 GLM-5"。
- **修复**：setup.sh 在 macOS 老 bash 下的 `unbound variable` 报错。
- **澄清**：Claude Code 接入方式（环境变量，非 settings.json）。

### 文件影响
- **改动**：`_infra/litellm-config.yaml`（cloud/glm-primary → ModelScope，model 加 openai/ 前缀）
- **改动**：`_infra/.env.example`（GLM_API_KEY 说明改为 ModelScope SDK Token）
- **改动**：`_infra/setup.sh`（修参数展开 bug、去 set -u、修 Ollama 版本判断）
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-GLM 改 ModelScope 双重验证；V-ClaudeCode 补充环境变量说明）
- **改动**：`docs/DECISIONS.md`（D-003 更新为 ModelScope 方案）

### 说明
- 本轮无新增功能需求，均为对第 1 轮产物的"改动/修复/澄清"，对应特殊要求 #2。

---

## [第 3 轮] 2026-06-11

### 需求变动
- **修复**：自检脚本模型名显示乱码。
- **改进**：自检脚本对 litellm 在 venv 中的探测与提示。
- **澄清**：`ollama serve` 端口占用含义、litellm 需先激活 venv。

### 文件影响
- **改动**：`_infra/setup.sh`（模型名查找去 cut；litellm 多路径探测）
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-Ollama / V-LiteLLM 补充真机情况说明）

### 说明
- 本轮均为对真机验证中暴露问题的修复/澄清，无新增/删除功能需求（对应特殊要求 #2）。

---

## [第 4 轮] 2026-06-11

### 需求变动
- **修复（诊断中）**：ModelScope 经 LiteLLM 网关卡住 → 加 stream_timeout/drop_params + 诊断模型。
- **新增**：GLM 链路诊断脚本 `_infra/diag-glm.sh`（配合 GitHub 拉取产物的新流程）。
- **新规则**：补丁包只含改动文件（不全量）。
- **新规则**：老板 push 测试产物到 GitHub，Agent 拉取分析。

### 文件影响
- **改动**：`_infra/litellm-config.yaml`（cloud/glm-primary 加 stream_timeout+drop_params；新增 cloud/glm-debug）
- **新增**：`_infra/diag-glm.sh`
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-GLM 诊断 + V-GLM-DEBUG + 状态汇总）
- **改动**：`HANDOFF.md`（两条新流程规则）
- **改动**：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`、`docs/DECISIONS.md`

### 说明
- 本轮聚焦 GLM 链路诊断与流程优化，对应特殊要求 #2。

---

## [第 5 轮] 2026-06-11

### 需求变动
- **修复**：GLM 经网关失败根因 = 启动进程缺 export GLM_API_KEY（非 ModelScope 问题）。
- **新增**：LiteLLM 启动脚本 `_infra/start-litellm.sh`（自动 export .env）。
- **明确**：GLM 流式可用、非流式不稳（Claude Code 默认流式，不影响日常）。

### 文件影响
- **新增**：`_infra/start-litellm.sh`
- **改动**：`_infra/litellm-config.yaml`（glm-primary 诊断结论注释、timeout/stream_timeout 调整）
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-GLM 改启动脚本+流式；状态汇总）
- **改动**：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`、`docs/DECISIONS.md`

### 说明
- 首次走通"老板 push 产物 → Agent git pull 分析"流程（D-005）。

---

## [第 6 轮] 2026-06-11

### 需求变动
- **澄清**：GLM 自报"通义千问"是模型身份认知偏差，非 fallback、非调用错误。
- **新增**：GLM 终极验证脚本 `_infra/verify-glm.sh`（基于 x-litellm-model-id）。
- **里程碑**：Phase 1 基础设施核心链路全部打通。

### 文件影响
- **新增**：`_infra/verify-glm.sh`
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-GLM 标记✅ + 身份偏差澄清 + x-litellm-model-id 方法）
- **改动**：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`

### 说明
- 本轮以澄清+验证工具为主，无功能性需求增删。

---

## [第 7 轮] 2026-06-11

### 需求变动
- **修复**：verify-glm.sh 误报"被 fallback"（v1 只测非流式的设计缺陷）。
- **改进**：diag-glm.sh 增加"直连 ModelScope 非流式"对照项，精准分离根因。

### 文件影响
- **改动**：`_infra/diag-glm.sh`（v2 重写，新增 A1 对照 + 判读指引）
- **改动**：`_infra/verify-glm.sh`（v2 重写，流式/非流式分别判定）
- **改动**：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/REAL_MACHINE_VALIDATION.md`

### 说明
- 非流式不稳的根治方案待 diag v2 输出确认后实施；本轮聚焦"把诊断做准"。

---

## [第 8 轮] 2026-06-11

### 需求变动
- **明确定位**：工厂本身=产品，试点项目=陪练（非正式开发目标）。角色=教练&陪练。
- **闭环**：GLM 非流式问题根因=Key 填错，已解决，全链路正常。
- **新增**：3 个本地模型接入（编程专用 + 2 个向量嵌入）。

### 文件影响
- **改动**：`_infra/litellm-config.yaml`（新增 local/coder、local/embedding、local/embedding-large；GLM 注释更新）
- **改动**：`_infra/model-routing-rules.md`（新增模型清单表 + 用法）
- **改动**：`HANDOFF.md`（新增 0.0 项目定位）、`docs/DECISIONS.md`（D-007、D-008）
- **改动**：`docs/REAL_MACHINE_VALIDATION.md`（V-GLM✅、新增 V-LocalModels）
- **改动**：`docs/DEV_LOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_STATE.md`

### 说明
- 第7-8两轮合并记录（GLM诊断收尾 + 模型扩充 + 定位澄清）。

---

## [第 9 轮] 2026-06-11

### 需求变动
- **新增**：试点项目 debt-collection（个人合法讨债助手），用于压测工厂 DISCOVERY 阶段。
- **明确边界**：仅合法路径；查财产=指引合法渠道/律师调查令，不自行非法查询；不做施压催收。
- **新增**：工厂能力评估文档 FACTORY_ASSESSMENT.md（陪练核心产出）。

### 文件影响
- **新增**：projects/debt-collection/（复制 _TEMPLATE）+ docs/DISCOVERY.md（填充）+ AGENTS.md（更新项目身份/红线）
- **新增**：docs/FACTORY_ASSESSMENT.md（工厂能力评估 + 改进 backlog FB-1~FB-4）
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

### 说明
- 进入 Phase 2 试点。重心是压测工厂、记录能力边界与缺陷，非交付讨债系统本身。

---

## [第 10 轮] 2026-06-11

### 需求变动（老板补充 6 点）
- **新增(工厂级)**：数据收集/整理/提炼/复用能力 + 多源权重 + 数据质量把控（FB-5）。
- **新增(工厂级)**：本地模型联网取数抽象层；授权账号登录须保账号安全（FB-6）。
- **新增(工厂级)**：DISCOVERY 深度讨论自检（FB-7）。
- **新增(工厂级)**：通用 Ingestion 能力层（图片/PDF/录音→结构化），已选型（FB-8）。
- **改动(讨债项目)**：核心标准=实际讨回率；新增 AC-6（执行可行性+回款概率优先，反老赖执行难）。
- **流程**：按老板要求 DISCOVERY 延长，暂不进 SPEC。

### 文件影响
- **新增**：docs/research/ingestion-tools-comparison.md（资料整理工具横向对比）
- **改动**：projects/debt-collection/docs/DISCOVERY.md（第8/9节 + AC-6）
- **改动**：docs/FACTORY_ASSESSMENT.md（FB-5~FB-8 + 要点映射）
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

---

## [第 11 轮] 2026-06-11

### 需求变动（老板决策）
- **FB-6 取数**：定为三层方案(L1公开/L2人在环/L3授权账号默认关)；强风控平台优先官方API不用账号爬。
- **FB-5 数据质量**：定为来源分级+定性转量化(老板打定性标签/黑名单，系统量化)+多源交叉+忠实度校验。
- **优先级**：先建 Ingestion 层(FB-8)作为工厂第一个新增通用能力。

### 文件影响
- **新增**：docs/research/data-acquisition-feasibility.md（取数+数据质量可行性评估）
- **改动**：projects/debt-collection/docs/DISCOVERY.md（要点2/3 调研结论）
- **改动**：docs/FACTORY_ASSESSMENT.md（FB-5/FB-6 状态）
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

---

## [第 12 轮] 2026-06-11

### 需求变动
- **实现**：FB-8 工厂通用 Ingestion 层（多格式→结构化）。
- **新增**：data-ingestion / data-quality 两个工厂 skill。
- **新增**：系统调研产出的 sources.yaml 初版（老板后续微调共同维护）。

### 文件影响
- **新增**：_factory/patterns/ingestion-pipeline/（models/processors/pipeline/cli + tests + README + pyproject）
- **新增**：_factory/skills/data-ingestion.skill.md、_factory/skills/data-quality.skill.md
- **新增**：projects/debt-collection/sources.yaml（数据源可信度初版）
- **改动**：docs/FACTORY_ASSESSMENT.md（FB-8✅ + 新增能力节）
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

### 说明
- 工厂首次完成"调研→落地通用能力"闭环。数据源/质量按老板要求重点对待。

---

## [第 13 轮] 2026-06-11

### 需求变动（老板三件）
- **实现**：FB-6 取数层 L1（官方公开渠道合规取数协调器，不爬不封号）。
- **新增**：sources.yaml 系统审阅建议（拉黑标准/评级原则）。
- **新增**：Ingestion 真机验证脚本（老板装库后验真实解析）。

### 文件影响
- **新增**：_factory/patterns/data-acquisition/（registry/models/planner/cli + tests + README + pyproject）
- **新增**：_factory/skills/data-acquisition.skill.md
- **新增**：_factory/patterns/ingestion-pipeline/verify-real.sh
- **改动**：projects/debt-collection/sources.yaml（审阅建议+黑名单填法）
- **改动**：docs/FACTORY_ASSESSMENT.md（FB-6 L1✅）、DEV_LOG/CHANGELOG/PROJECT_STATE

### 说明
- 取数层坚持"协调器而非爬虫"，落实账号安全+合规硬约束。

---

## [第 14 轮] 2026-06-11

### 需求变动
- **修复**：Ingestion 处理器从"占位"改为"真实调用"(MarkItDown/FunASR/MinerU/pypdf)；空内容问题解决。
- **实现**：FB-6 L2 浏览器辅助(人在环)——browser-use 接 GLM，遇验证码/登录停下等人工。
- **改进**：跳过 .DS_Store 等垃圾文件；markitdown 安装提示改 [all]。

### 文件影响
- **改动**：_factory/patterns/ingestion-pipeline/src/ingestion/processors.py（真实接入重写）、pipeline.py（跳垃圾文件）、verify-real.sh、pyproject、tests
- **新增**：_factory/patterns/data-acquisition/src/acquisition/browser_assist.py（L2）
- **改动**：data-acquisition 的 cli.py(--l2)、tests、README、data-acquisition.skill.md
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md、docs/FACTORY_ASSESSMENT.md

---

## [第 15 轮] 2026-06-12

### 需求变动
- **新增**：真机安装指南 SETUP_GUIDE.md(MinerU/FunASR torch/browser-use 模型选型)。
- **新增**：data-acquisition CLI --bu-model 切换 L2 模型。
- **产出**：debt-collection SPEC(架构+5 ADR+RISK+10任务 TASK_GRAPH)，待 HITL Gate-2。

### 文件影响
- **新增**：docs/SETUP_GUIDE.md
- **改动**：_factory/patterns/data-acquisition/src/acquisition/cli.py(--bu-model)
- **新增/改动**：projects/debt-collection/docs/{SPEC.md, RISK.md, TASK_GRAPH.md, adr/ADR-001~005}, AGENTS.md(phase)
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md、docs/FACTORY_ASSESSMENT.md

---

## [第 16 轮] 2026-06-12

### 需求变动
- **新增规则**：R1 模型选型不限本地、R2 决断前先调研主流方案(HANDOFF 0.0.1)。
- **升级**：debt-collection 从"一次性报告"→"动态案件博弈"(情报库+时间线+动态重算+合法筹码，ADR-006)。
- **修复**：MinerU 真实接入 ingestion(SDK+CLI)；根目录污染(产物移至项目 runtime/)。
- **进入 BUILD**：实现 models/ledger/timeline/intel/compliance(13 passed)。

### 文件影响
- **改动**：HANDOFF.md(R1/R2)、docs/SETUP_GUIDE.md(项目内环境+清理)、.gitignore(runtime/)
- **改动**：_factory/patterns/ingestion-pipeline/{processors.py(MinerU真实接入), verify-real.sh}
- **改动/新增**：projects/debt-collection/docs/{SPEC.md(动态升级), TASK_GRAPH.md, adr/ADR-006}
- **新增**：projects/debt-collection/{pyproject.toml, .gitignore, src/debt/{models,ledger,timeline,intel,compliance}.py, tests/test_debt.py}
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

---

## [第 17 轮] 2026-06-12

### 需求变动
- **新增**：浏览器工具三条腿选型(browser-use+browser-act+MediaCrawler)，社交情报源纳入。
- **完成**：BUILD 骨架搭满(knowledge/llm_client/strategy/integrations/cli)，13任务完成12。

### 文件影响
- **新增**：docs/research/browser-automation-tools-selection.md
- **新增**：projects/debt-collection/src/debt/{knowledge,llm_client,strategy,integrations,cli}.py
- **改动**：projects/debt-collection/tests/test_debt.py(18 passed)、docs/TASK_GRAPH.md
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md、docs/FACTORY_ASSESSMENT.md

---

## [第 18 轮] 2026-06-12

### 需求变动
- **新增规则 R3**：操作指示必须保姆级详细。
- **新增**：RUNBOOK_BUILD_VERIFY.md(真机验BUILD/GLM对比/工具安装 逐步)。
- **HARDEN 准备**：HARDEN_CHECKLIST.md + security_scan.sh(自检11项全过)。

### 文件影响
- **改动**：HANDOFF.md(R3)
- **新增**：docs/RUNBOOK_BUILD_VERIFY.md
- **新增**：projects/debt-collection/docs/harden/{HARDEN_CHECKLIST.md, security_scan.sh}
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

---

## [第 19 轮] 2026-06-12

### 需求变动
- **HARDEN 决策**：策略模型每次可选(--model)；DB 暂明文。
- **实现**：report --model 隐私/质量切换。
- **产出**：SECURITY_REVIEW.md(威胁建模,无高危,待GLM复核)。

### 文件影响
- **改动**：projects/debt-collection/src/debt/cli.py(--model)
- **改动**：projects/debt-collection/docs/harden/HARDEN_CHECKLIST.md(决策落地)
- **新增**：projects/debt-collection/docs/harden/SECURITY_REVIEW.md
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

---

## [第 20 轮] 2026-06-12

### 需求变动
- **新增**：RETRO 复盘模板(双视角+待真机占位) + lesson 草稿 + 真机数据一键收集脚本。

### 文件影响
- **新增**：projects/debt-collection/docs/RETRO.md
- **新增**：_factory/lessons/2026-Q2-debt-collection.lesson.md
- **新增**：projects/debt-collection/docs/collect-retro-data.sh
- **改动**：docs/DEV_LOG.md、docs/CHANGELOG.md、docs/PROJECT_STATE.md

---

## [第 21 轮] 2026-06-12

### 需求变动
- **新增规则 R4**：所有 LLM 工作记录遥测(事件+耗时+实时计时器+JSONL储备)。
- **重构**：合规判定 v2(否定语境识别修复误判+分级+结构化整改+递归重生成)。
- **新增**：工厂 Pattern llm-telemetry。

### 文件影响
- **新增**：_factory/patterns/llm-telemetry/(telemetry.py+pyproject+README+tests)
- **改动**：HANDOFF.md(R4)
- **重构**：projects/debt-collection/src/debt/compliance.py(v2)
- **改动**：projects/debt-collection/src/debt/{strategy.py(递归整改+遥测), integrations.py(注入遥测path), cli.py(整改理由)}
- **改动**：projects/debt-collection/tests/test_debt.py(22 passed)、docs/harden/security_scan.sh(UTF-8)
- **改动**：docs/RETRO.md(真机结果)、FACTORY_ASSESSMENT.md、DEV_LOG.md、CHANGELOG.md、PROJECT_STATE.md

---

## [第 22 轮] 2026-06-12

### 需求变动
- **新增**：反封号爬取详尽调研报告(含 Higgsfield 澄清)。
- **新增**：Claude 独立策略报告样例(对比 GLM)。
- **新增**：工厂 backlog FB-10(反封号取数+数据流水线)。

### 文件影响
- **新增**：docs/research/anti-ban-crawling-strategy.md
- **新增**：projects/debt-collection/docs/strategy-sample-claude.md
- **改动**：docs/FACTORY_ASSESSMENT.md、DEV_LOG.md、CHANGELOG.md、PROJECT_STATE.md

---

## [第 23 轮] 2026-06-12

### 需求变动(方法论级)
- **新增规则 R5(调研穷尽)、R6(缺知识求助不假装)**。
- **新增工厂核心能力 FB-11：专家系统/决策大脑**(独立可复用领域专家)。
- **新增**：开源模型全景调研、专家系统设计、专家模板、工厂运转手册。

### 文件影响
- **改动**：HANDOFF.md(R5/R6)
- **新增**：docs/research/expert-system-design.md、docs/FACTORY_OPERATIONS.md
- **新增**：_factory/experts/_TEMPLATE.expert/(expert.yaml/README/knowledge/_gaps.md/_sources.yaml)
- **改动**：docs/FACTORY_ASSESSMENT.md(FB-11+方法论修正)、DEV_LOG.md、CHANGELOG.md、PROJECT_STATE.md

---

---

## [第 29 轮 · Wave 1 + Wave 2 Task 1] 2026-06-14

### 需求变动
- **Wave 1 基础设施稳定化**：
  - 测试阻塞修复：`__init__.py` HTML 注释 → Python 注释
  - Editable Install：`pip install -e .` 成功，移除 `cli.py` 中 `sys.path.insert`
  - Git 发布流程：`Makefile` + `release.sh` (语义化版本 + CHANGELOG + git tag)
  - 数据备份自动化：`backup.sh` 每日备份 runtime/，保留 30 天
  - Baseline Benchmark：`docs/benchmark.md` 记录 MLX 基线指标
- **Wave 2 Task 1 Pydantic 配置体系 (双文件模型管理)**：
  - `config/models.yaml` (A 文件)：10 模型定义 (本地 6 + 中国 API 4)
  - `config/routing_plans.yaml` (B 文件)：5 方案 (default/high-quality/all-local/fast/manual-override)
  - `config/privacy_policy.yaml`：9 字段 × 3 端点，4 种策略类型
  - `peer_review.config.schemas`：完整 Pydantic Schema (ExpertConfig, ModelConfig, PlanConfig 等)
  - `peer_review.config.loader`：统一加载入口 `load_all_configs()`，启动时交叉验证
  - 专家 ID 强制校验格式，模板目录 `_TEMPLATE.expert` 自动跳过
  - 专家 YAML 统一引用 `local-qwen35b` (models.yaml 键名)

### 文件影响
- **新增**：`config/models.yaml`、`config/routing_plans.yaml`、`config/privacy_policy.yaml`
- **新增**：`_factory/patterns/peer-review/src/peer_review/config/{schemas.py, loader.py, __init__.py}`
- **新增**：`Makefile`、`backup.sh`、`release.sh`、`docs/benchmark.md`
- **改动**：`_factory/patterns/peer-review/src/peer_review/__init__.py` (修复语法)
- **改动**：`projects/debt-collection/src/debt/cli.py` (移除 sys.path.insert)
- **改动**：4 个专家 YAML (统一 model 键名)
- **改动**：`HANDOFF.md` (发布流程、CLI 使用方式)、`docs/PROJECT_STATE.md`、`docs/DEV_LOG.md`、`docs/DECISIONS.md`
- **Git 标签**：`v1.1.0-wave1-complete` 已推送

### 验收
- `make test` 全通过 (verify_architecture + 22 debt tests)
- 配置加载成功：10 模型、5 方案、4 专家
- 交叉验证通过 (A/B 文件一致性、专家引用检查)
- CLI 正常运行：`debt review 1 --model local/primary`
