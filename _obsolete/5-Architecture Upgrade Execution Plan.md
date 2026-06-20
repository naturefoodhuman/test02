FORGE Factory — Architecture Upgrade Execution Plan

版本： v1.0 | 日期： 2026-06-14 | 总架构师： Architecture Transformation Director 基于： Project Dossier v1.0.5 + Feasibility Review Report v1.0 状态： 📋 待执行
1. Executive Summary
一句话定义

本计划将 FORGE Factory 从"能跑但脆弱"的 v1.0.5 状态，通过 5 个升级波次、14 个里程碑，安全演进到"稳定、可维护、成本可控"的生产就绪状态。
核心判断
维度	当前状态	目标状态	差距等级
可维护性	🔴 单文件500+行	🟢 3模块各<300行	高
启动性能	🔴 每次重建索引	🟢 去重跳过	中
推理速度	🟠 15-25min/评审	🟢 流式+MLX，体感<10min	高
数据合规	🔴 无出境控制	🟢 技术门控	高
外部API	🔴 未接入	🟢 DeepSeek自动路由	中
配置稳定	🔴 手写解析器	🟢 Pydantic校验	中
部署流程	🟠 ZIP补丁	🟢 Git标准化	低
记忆系统	🔴 未激活	🟢 跨会话持久化	中
执行原则

text

系统可运行 > 逐步升级 > 快速见效 > 完美设计
禁止：Big Bang Rewrite
优先：增量演进，每个 Wave 结束后系统必须可独立运行

时间预算（独立开发者 4-6h/天）

text

Wave 1（基础设施稳定）：第 1-3 天    ← 最高ROI
Wave 2（核心代码重构）：第 4-8 天    ← 消除最大风险
Wave 3（能力激活）：   第 9-13 天   ← 解锁已有功能
Wave 4（外部集成）：   第 14-18 天  ← 扩展能力边界
Wave 5（优化收敛）：   第 19-25 天  ← 长期健康
总计：约 4 周（25 个工作日）

2. Gap Analysis
2.1 能力缺口
缺口ID	描述	当前状态	目标状态	影响等级
CAP-01	数据出境审核门	❌ 不存在（数据可静默出境）	✅ CLI强制确认 + 数据分级标注	🔴 P0 合规
CAP-02	跨会话持久化记忆	❌ SqliteMemoryDb已导入未挂载	✅ Agent挂载，历史对话可检索	🟠 P1
CAP-03	流式输出	❌ 等待全量完成后打印	✅ stream=True 实时输出	🟠 P1 用户体验
CAP-04	中国商业API路由	❌ LiteLLM骨架存在，未接入DeepSeek	✅ DeepSeek V4 Pro自动路由	🟠 P1
CAP-05	SKILL.md技能注入	❌ 仅元数据定义，未接主流程	决策：接入 OR 删除	🟡 P2
CAP-06	分层决策引擎集成	❌ LayeredDecisionEngine孤岛	✅ Team流程中调用	🟡 P2
CAP-07	MLX推理加速	❌ 默认Metal后端，未启用MLX	✅ MLX后端激活，约2x速度	🟠 P1
CAP-08	索引去重机制	❌ 每次启动重建ChromaDB索引	✅ collection存在性检查	🔴 P0 性能
2.2 技术缺口
缺口ID	描述	当前状态	目标状态	影响等级
TECH-01	orchestrator.py单文件	🔴 500+行，职责混合	✅ 拆分为3模块，各<300行	🔴 P0 可维护性
TECH-02	YAML手写解析器	🔴 _load_yaml_simple脆弱	✅ Pydantic BaseModel校验	🔴 P0 稳定性
TECH-03	PYTHONPATH硬编码	🟠 sys.path.insert脆弱	✅ pyproject.toml editable install	🟠 P1
TECH-04	防御性try-except过多	🟡 掩盖真实错误	✅ 启动时一次性检查 + 明确报错	🟡 P2
TECH-05	专家ID提取偶现空值	🟠 id:字段依赖位置	✅ Pydantic强制校验id字段	🟠 P1
TECH-06	Agno框架深度绑定	🔴 无抽象层	✅ Agent接口抽象层（隔离Agno）	🟡 P2 长期
TECH-07	无日志系统	🟡 仅终端Rich输出	✅ logging模块 → runtime/logs/	🟡 P2
TECH-08	ChromaDB无版本标记	🟠 脏索引无法识别	✅ 知识库版本hash标记	🟠 P1
2.3 流程缺口
缺口ID	描述	当前状态	目标状态	影响等级
PROC-01	部署流程	🟠 ZIP补丁手动覆盖	✅ Git tag标准化发布	🟡 P2
PROC-02	测试前置	🟡 pytest存在但不强制运行	✅ pre-commit hook或Makefile enforce	🟡 P2
PROC-03	HITL文档交换格式	❌ 无标准化	✅ decisions/<日期>-<ID>-human-review.md规范	🟠 P1
PROC-04	框架升级流程	❌ 无保护机制	✅ 升级分支 → 全量测试 → 合并	🔴 P0
PROC-05	数据备份流程	❌ runtime/无备份策略	✅ 每日SQLite备份脚本	🟠 P1
2.4 知识缺口
缺口ID	描述	影响
KNW-01	orchestrator.py内部逻辑无API文档	修改前必须靠读代码理解全局
KNW-02	无故障排查手册	常见错误需重新摸索解决
KNW-03	性能基准数据缺失	无法量化优化效果
KNW-04	DeepSeek/GLM API接入SOP缺失	每次新接口重复探索
KNW-05	HITL节点操作规范缺失	Claude/ChatGPT手动交互无标准格式
2.5 自动化缺口
缺口ID	描述	当前	目标
AUTO-01	索引构建自动化（去重）	手动/每次重建	条件触发，存在则跳过
AUTO-02	数据备份自动化	无	cron/脚本每日备份
AUTO-03	测试自动化触发	手动	Makefile test命令 + 可选pre-commit
AUTO-04	模型路由自动化	手动选择	任务类型→自动路由规则
AUTO-05	敏感数据检测自动化	无	数据分级标注 + 出境前自动拦截
3. Work Breakdown Structure

text

FORGE Factory Architecture Upgrade
│
├── EPIC-1: 基础设施稳定化
│   ├── CAP-1.1: 环境标准化
│   │   ├── PROJ-1.1.1: pyproject.toml editable install
│   │   │   ├── TASK-1.1.1.1: 修改peer-review/pyproject.toml，配置[tool.hatch.build]
│   │   │   ├── TASK-1.1.1.2: 修改debt-collection/pyproject.toml
│   │   │   ├── TASK-1.1.1.3: 删除所有 sys.path.insert 调用
│   │   │   └── TASK-1.1.1.4: 更新HANDOFF.md中的环境配置说明
│   │   └── PROJ-1.1.2: MLX后端激活
│   │       ├── TASK-1.1.2.1: 确认Ollama版本≥0.19（MLX预览支持）
│   │       ├── TASK-1.1.2.2: 在start-litellm.sh添加MLX环境变量
│   │       ├── TASK-1.1.2.3: 基准测试：记录当前tok/s（baseline）
│   │       └── TASK-1.1.2.4: 启用后验证tok/s提升，记录到benchmark.md
│   │
│   ├── CAP-1.2: 部署流程标准化
│   │   └── PROJ-1.2.1: Git发布流程替代ZIP补丁
│   │       ├── TASK-1.2.1.1: 定义分支策略（main/feature/fix）
│   │       ├── TASK-1.2.1.2: 创建Makefile（make test / make deploy / make backup）
│   │       ├── TASK-1.2.1.3: 编写release.sh（git tag → changelog更新）
│   │       └── TASK-1.2.1.4: 在HANDOFF.md更新发布SOP
│   │
│   └── CAP-1.3: 数据安全基础
│       └── PROJ-1.3.1: 数据备份机制
│           ├── TASK-1.3.1.1: 编写backup.sh（SQLite + ChromaDB定时备份）
│           ├── TASK-1.3.1.2: 配置备份到runtime/backups/（不入Git）
│           └── TASK-1.3.1.3: 更新.gitignore确保runtime/完整排除
│
├── EPIC-2: 核心代码重构
│   ├── CAP-2.1: orchestrator.py拆分
│   │   ├── PROJ-2.1.1: agent_factory.py
│   │   │   ├── TASK-2.1.1.1: 提取ExpertFactory类（create_agent逻辑）
│   │   │   ├── TASK-2.1.1.2: 提取Expert数据类定义
│   │   │   ├── TASK-2.1.1.3: 更新所有import引用
│   │   │   └── TASK-2.1.1.4: 运行全量测试（39 cases）确认无回归
│   │   ├── PROJ-2.1.2: knowledge_loader.py
│   │   │   ├── TASK-2.1.2.1: 提取KnowledgeLoader类（load_knowledge逻辑）
│   │   │   ├── TASK-2.1.2.2: 实现ChromaDB collection存在性检查（去重）
│   │   │   ├── TASK-2.1.2.3: 实现知识库版本hash标记
│   │   │   └── TASK-2.1.2.4: 运行全量测试确认无回归
│   │   └── PROJ-2.1.3: team_orchestrator.py
│   │       ├── TASK-2.1.3.1: 提取TeamOrchestrator类（build_review_team逻辑）
│   │       ├── TASK-2.1.3.2: 保留orchestrator.py作为兼容入口（薄包装层，<50行）
│   │       ├── TASK-2.1.3.3: 更新cli.py的import路径
│   │       └── TASK-2.1.3.4: 运行全量测试确认无回归
│   │
│   ├── CAP-2.2: 配置系统强化
│   │   └── PROJ-2.2.1: Pydantic配置校验
│   │       ├── TASK-2.2.1.1: 定义ExpertConfig Pydantic BaseModel（含id必填校验）
│   │       ├── TASK-2.2.1.2: 定义ReviewerConfig Pydantic BaseModel
│   │       ├── TASK-2.2.1.3: 替换_load_yaml_simple为Pydantic.parse_obj
│   │       ├── TASK-2.2.1.4: 更新所有expert.yaml确保id:字段在第一行
│   │       └── TASK-2.2.1.5: 运行全量测试确认无回归
│   │
│   └── CAP-2.3: 日志系统
│       └── PROJ-2.3.1: 结构化日志
│           ├── TASK-2.3.1.1: 在每个新模块顶部配置logging.getLogger(__name__)
│           ├── TASK-2.3.1.2: 创建runtime/logs/目录，配置RotatingFileHandler
│           ├── TASK-2.3.1.3: 将Rich终端输出与logging系统联动
│           └── TASK-2.3.1.4: 在HANDOFF.md记录日志位置和格式
│
├── EPIC-3: 能力激活（已有代码，打通断路）
│   ├── CAP-3.1: 流式输出激活
│   │   └── PROJ-3.1.1: stream=True集成
│   │       ├── TASK-3.1.1.1: 在Team.run()调用处添加stream=True
│   │       ├── TASK-3.1.1.2: 更新cli.py的输出处理逻辑（迭代chunk）
│   │       ├── TASK-3.1.1.3: Rich Live Display集成（实时进度展示）
│   │       └── TASK-3.1.1.4: 测试：确认流式输出不破坏最终结果格式
│   │
│   ├── CAP-3.2: 持久化记忆激活
│   │   └── PROJ-3.2.1: SqliteMemoryDb挂载
│   │       ├── TASK-3.2.1.1: 配置SqliteMemoryDb路径（runtime/memory.db）
│   │       ├── TASK-3.2.1.2: 在agent_factory.py中挂载memory参数
│   │       ├── TASK-3.2.1.3: 验证跨会话记忆读写正常
│   │       └── TASK-3.2.1.4: 在cli.py添加debt memory list命令（可选）
│   │
│   ├── CAP-3.3: 分层决策引擎接入
│   │   └── PROJ-3.3.1: LayeredDecisionEngine集成
│   │       ├── TASK-3.3.1.1: 梳理LayeredDecisionEngine现有接口
│   │       ├── TASK-3.3.1.2: 在team_orchestrator.py的post-processing阶段调用
│   │       ├── TASK-3.3.1.3: 编写铁闸规则单元测试（至少5条规则验证）
│   │       └── TASK-3.3.1.4: 集成测试：验证铁闸拦截高风险输出
│   │
│   └── CAP-3.4: SKILL.md决策执行
│       └── PROJ-3.4.1: 二选一决策
│           ├── TASK-3.4.1.1: 评估现有3个技能文件的实际使用频率
│           ├── TASK-3.4.1.2: 决策A（接入）：实现match_skills() → inject_skills_into_expert()
│           │   ├── TASK-3.4.1.2.1: 技能匹配逻辑（关键词/标签匹配）
│           │   └── TASK-3.4.1.2.2: Agent构建时注入技能上下文
│           └── TASK-3.4.1.3: 决策B（删除）：git rm _factory/skills/，更新文档
│
├── EPIC-4: 外部能力集成
│   ├── CAP-4.1: 数据出境审核门（合规P0）
│   │   └── PROJ-4.1.1: 技术级数据隐私门控
│   │       ├── TASK-4.1.1.1: 定义DataSensitivityLevel枚举（LOCAL_ONLY / REQUIRES_REVIEW / PUBLIC）
│   │       ├── TASK-4.1.1.2: 在DebtCase模型添加sensitivity字段（默认LOCAL_ONLY）
│   │       ├── TASK-4.1.1.3: 实现EgressGuard.check(data, target_api)拦截函数
│   │       ├── TASK-4.1.1.4: 在所有外部API调用前注入EgressGuard检查
│   │       ├── TASK-4.1.1.5: CLI实现强制确认提示（非可绕过）
│   │       └── TASK-4.1.1.6: 单元测试：验证LOCAL_ONLY数据被拦截
│   │
│   ├── CAP-4.2: 中国商业API接入
│   │   └── PROJ-4.2.1: DeepSeek V4 Pro集成
│   │       ├── TASK-4.2.1.1: 在litellm-config.yaml添加DeepSeek路由配置
│   │       ├── TASK-4.2.1.2: 在_infra/.env.example添加DEEPSEEK_API_KEY占位符
│   │       ├── TASK-4.2.1.3: 实现ModelRouter（任务类型→模型选择逻辑）
│   │       ├── TASK-4.2.1.4: 在EgressGuard通过后自动路由到DeepSeek
│   │       ├── TASK-4.2.1.5: 接入后跑50个真实请求，记录延迟/质量基准
│   │       └── TASK-4.2.1.6: 配置成本告警阈值（单次>$0.1触发警告）
│   │
│   └── CAP-4.3: HITL文档交换标准化
│       └── PROJ-4.3.1: 人工节点规范
│           ├── TASK-4.3.1.1: 定义decisions/<日期>-<ID>-human-review.md模板
│           ├── TASK-4.3.1.2: 在五阶段工作流中标注HITL节点位置
│           ├── TASK-4.3.1.3: 实现forge hitl <stage>命令（生成标准化输入文档）
│           └── TASK-4.3.1.4: 在HANDOFF.md记录HITL操作SOP
│
└── EPIC-5: 优化与长期健康
    ├── CAP-5.1: Agno抽象层（降低框架绑定风险）
    │   └── PROJ-5.1.1: Agent接口抽象
    │       ├── TASK-5.1.1.1: 定义BaseAgentInterface（run/stream/memory接口）
    │       ├── TASK-5.1.1.2: 实现AgnoAdapter（包装Agno具体实现）
    │       ├── TASK-5.1.1.3: 所有上层调用改用BaseAgentInterface
    │       └── TASK-5.1.1.4: 验证：替换Agno版本只需修改Adapter
    │
    ├── CAP-5.2: RAG质量基础评估
    │   └── PROJ-5.2.1: 简单检索质量评估
    │       ├── TASK-5.2.1.1: 创建5-10个手工标注的评估问题（golden set）
    │       ├── TASK-5.2.1.2: 实现eval_rag.py（检索结果vs预期答案）
    │       └── TASK-5.2.1.3: 每次知识库更新后运行，记录相关性得分
    │
    ├── CAP-5.3: 框架升级保护流程
    │   └── PROJ-5.3.1: Agno升级SOP
    │       ├── TASK-5.3.1.1: 创建upgrade/agno-<version>分支规范
    │       ├── TASK-5.3.1.2: 在Makefile添加make test-upgrade命令
    │       └── TASK-5.3.1.3: 在DECISIONS.md记录D-013：Agno升级保护政策
    │
    └── CAP-5.4: 性能基准体系
        └── PROJ-5.4.1: benchmark.md持续更新
            ├── TASK-5.4.1.1: 定义标准化benchmark场景（3个固定测试案件）
            ├── TASK-5.4.1.2: 实现run_benchmark.sh（自动计时+记录）
            └── TASK-5.4.1.3: 每个Wave结束后运行benchmark，记录对比数据

4. Dependency Map
4.1 关键路径分析

text

关键路径（必须按序，任何一项延误 = 整体延误）：

TASK-2.2.1.x（Pydantic配置）
    ↓
TASK-2.1.1.x（agent_factory.py提取）
    ↓
TASK-2.1.2.x（knowledge_loader.py提取，含去重修复）
    ↓
TASK-2.1.3.x（team_orchestrator.py提取）
    ↓
TASK-3.3.x（LayeredDecisionEngine接入）
    ↓
TASK-4.1.x（EgressGuard：依赖干净的调用链）
    ↓
TASK-4.2.x（DeepSeek API：依赖EgressGuard）

关键路径总长：约 12 个工作日
4.2 并行路径

text

并行轨道 A（独立于重构，可提前启动）：
├── TASK-1.1.2.x（MLX后端激活）
├── TASK-1.2.1.x（Git发布流程）
├── TASK-1.3.1.x（备份机制）
└── TASK-4.3.1.x（HITL文档规范，纯文档工作）

并行轨道 B（依赖重构完成，但内部并行）：
├── TASK-3.1.1.x（流式输出）
├── TASK-3.2.1.x（记忆激活）
└── TASK-5.3.1.x（升级SOP文档）

并行轨道 C（长期，不阻塞任何核心路径）：
├── TASK-5.1.1.x（Agent抽象层）
├── TASK-5.2.1.x（RAG评估）
└── TASK-5.4.1.x（性能基准）

4.3 阻塞项识别
阻塞项	被阻塞任务	解除条件	优先级
orchestrator.py拆分未完成	EgressGuard注入、DeepSeek路由、流式输出	EPIC-2完成	🔴 P0
Pydantic配置未就绪	orchestrator拆分（依赖稳定配置层）	CAP-2.2完成	🔴 P0
EgressGuard未上线	DeepSeek API正式接入	CAP-4.1完成	🔴 P0
SKILL.md决策未做出	PROJ-3.4.1无法执行	人工决策（立即）	🟠 P1
Ollama版本确认（≥0.19）	MLX后端激活	TASK-1.1.2.1验证	🟠 P1
4.4 依赖关系可视化

text

[EPIC-1 基础设施] ──────────────────────────────────┐
  MLX激活(独立)                                       │
  Git流程(独立)                                       ▼
  备份机制(独立)                           [EPIC-5 持续健康]

[EPIC-2 重构] ──── Pydantic → 拆分3文件 ────────────┐
                      ↑ 先决条件                     │
                      │                             ▼
[EPIC-3 能力激活] ── 依赖EPIC-2 ──── 流式/记忆/铁闸 ─┤
                                                    │
[EPIC-4 集成] ──── EgressGuard → DeepSeek ──────────┘
                   ↑ 依赖EPIC-2完成

5. Upgrade Waves
Wave 1：基础设施稳定（第1-3天）

主题： 在不触碰核心业务逻辑的前提下，消除环境脆弱性，建立安全网。

范围：
任务	预计时间	风险
Ollama版本确认 + MLX后端激活	2h	低（配置修改）
Git发布流程建立（分支策略+Makefile）	3h	极低
pyproject.toml editable install	2h	低
数据备份脚本（backup.sh）	1h	极低
运行baseline性能benchmark	1h	极低
更新HANDOFF.md（新流程）	1h	极低

Wave 1 退出条件：

    ✅ make test 命令运行39个测试全部通过
    ✅ MLX后端激活，tok/s比baseline提升（记录数据）
    ✅ runtime/ 目录每日备份脚本可运行
    ✅ 删除所有sys.path.insert，改用editable install

Wave 1 不触碰： orchestrator.py, cli.py, 任何Agent逻辑
Wave 2：核心代码重构（第4-8天）

主题： 拆解最高风险的技术债，消除认知负担炸弹。

范围：
任务	预计时间	风险
Pydantic ExpertConfig/ReviewerConfig定义	3h	低
替换_load_yaml_simple	2h	中（需验证所有YAML兼容）
更新所有expert.yaml，确保id:在首行	1h	低
提取agent_factory.py	4h	中
提取knowledge_loader.py（含ChromaDB去重）	4h	中
提取team_orchestrator.py	3h	中
orchestrator.py降级为薄兼容层	1h	低
结构化日志系统接入	2h	低
全量测试39 cases（每步后运行）	贯穿	低

拆分后文件结构：

text

_factory/patterns/peer-review/src/peer_review/
├── orchestrator.py          ← 兼容入口（<50行）
├── agent_factory.py         ← ExpertFactory（<250行）
├── knowledge_loader.py      ← KnowledgeLoader + 去重（<200行）
├── team_orchestrator.py     ← TeamOrchestrator + 流程（<280行）
├── config/
│   ├── expert_config.py     ← Pydantic ExpertConfig
│   └── reviewer_config.py   ← Pydantic ReviewerConfig
└── utils/
    └── logger.py            ← 统一日志配置

Wave 2 退出条件：

    ✅ orchestrator.py ≤ 50行（仅import转发）
    ✅ 3个新模块各 ≤ 300行
    ✅ 所有39个测试通过
    ✅ debt review 命令端到端正常运行
    ✅ ChromaDB去重验证：连续运行2次，第2次跳过索引构建（日志可见）
    ✅ 专家ID空值问题消失（Pydantic强制校验）

Wave 3：能力激活（第9-13天）

主题： 打通已有代码的断路，解锁设计好但未使用的能力。

范围：
任务	预计时间	风险
流式输出激活（stream=True + Rich Live）	3h	低
SqliteMemoryDb挂载	2h	低
SKILL.md二选一决策执行	1-4h	取决于决策
LayeredDecisionEngine接入主流程	4h	中
铁闸规则单元测试（5条）	2h	低
HITL文档交换模板标准化	2h	低
端到端集成测试（新增3个）	3h	低

SKILL.md决策指引：

text

评估标准（立即决策，今日）：
├── 过去2周内有多少次"希望技能系统在工作"？
│   ├── ≥3次 → 接入（实现match_skills/inject_skills）
│   └── 0次  → 删除（git rm + 更新文档）
└── 目的：消除"设计完未使用"的认知噪音

Wave 3 退出条件：

    ✅ 流式输出：debt review 运行时实时打印，无需等待全量完成
    ✅ 跨会话记忆：第2次运行同案件，Agent能引用上次结论
    ✅ 铁闸规则：至少1个高风险测试案件被正确拦截
    ✅ SKILL.md状态：已接入 OR 已删除（不允许保留"待定"状态）
    ✅ HITL模板文件存在：decisions/_TEMPLATE-human-review.md

Wave 4：外部能力集成（第14-18天）

主题： 扩展能力边界，接入外部API，建立合规基础。

范围：
任务	预计时间	风险
DataSensitivityLevel枚举定义	1h	低
EgressGuard.check()实现	3h	中
CLI强制确认提示（非可绕过）	2h	低
EgressGuard单元测试（拦截验证）	2h	低
DeepSeek V4 Pro litellm-config配置	1h	低
ModelRouter任务路由逻辑	3h	低
50个真实请求基准测试（质量+延迟）	2h	低
成本告警逻辑	1h	低
更新.env.example（DEEPSEEK_API_KEY）	0.5h	极低
forge hitl命令实现	3h	低

EgressGuard设计规范：

Python

# 核心设计（不超过50行）
class EgressGuard:
    SENSITIVE_FIELDS = ['debtor_name', 'debtor_id', 'amount', 'evidence']
    
    @staticmethod
    def check(data: dict, target_api: str) -> EgressDecision:
        sensitivity = data.get('_sensitivity', DataSensitivityLevel.LOCAL_ONLY)
        if sensitivity == DataSensitivityLevel.LOCAL_ONLY:
            raise EgressBlockedError(f"数据标记为本地专用，不可发送至 {target_api}")
        if sensitivity == DataSensitivityLevel.REQUIRES_REVIEW:
            return EgressDecision.REQUIRES_HUMAN_CONFIRMATION
        return EgressDecision.ALLOWED

# CLI强制确认（不可绕过）
def confirm_egress(data_summary: str, target: str) -> bool:
    print(f"⚠️  即将发送数据至外部API: {target}")
    print(f"数据摘要: {data_summary}")
    response = input("确认发送？输入 'YES' 继续，其他任意键取消: ")
    return response == 'YES'  # 严格匹配，无默认值

Wave 4 退出条件：

    ✅ EgressGuard：LOCAL_ONLY数据调用DeepSeek被自动拦截
    ✅ 敏感数据调用：CLI显示确认提示，输入非'YES'则中止
    ✅ DeepSeek V4 Pro：50次真实请求成功，延迟和质量记录在benchmark.md
    ✅ 成本：月度模拟测试费用 < $5
    ✅ HITL命令：forge hitl discovery 生成标准化Markdown文档

Wave 5：优化与收敛（第19-25天）

主题： 建立长期健康机制，降低未来维护成本。

范围：
任务	预计时间	风险
Agent接口抽象层（BaseAgentInterface）	6h	低
AgnoAdapter实现	4h	中
RAG简单评估集（5-10个golden set）	3h	低
eval_rag.py实现	2h	低
Agno升级保护SOP + Makefile命令	2h	低
性能基准标准化（3个固定测试案件）	2h	低
run_benchmark.sh自动化	2h	低
全量测试补充（新增10个集成测试目标）	4h	低
API文档：3个新模块函数签名注释	3h	低
故障排查手册更新	2h	低
DECISIONS.md更新（D-013到D-015）	1h	低
最终验收测试	4h	低

Wave 5 退出条件：

    ✅ Agent抽象层：替换AgnoAdapter不影响上层调用
    ✅ RAG评估：5个golden set问题，相关性得分 > 70%
    ✅ 测试总数：≥ 49 cases（原39 + 新增10个集成测试）
    ✅ 所有模块文件 < 300行
    ✅ benchmark.md包含Wave 1、3、5三个时间点的性能对比
    ✅ 故障排查手册覆盖10个最常见错误

6. Milestones
M0：升级启动门（Day 0，当前）
要素	内容
目标	升级前基线确认
验收标准	39个测试全部通过；debt review 端到端可运行；baseline benchmark已记录
交付物	baseline-benchmark.md；当前测试报告
风险	当前存在已知Bug可能导致baseline不稳定
通过动作	手动运行 pytest && debt review "测试案件"
M1：环境稳定（Day 3，Wave 1完成）
要素	内容
目标	消除环境脆弱性，建立安全网
验收标准	MLX tok/s提升可量化；make test 通过39 cases；backup.sh可运行；无sys.path.insert
交付物	Makefile；backup.sh；MLX benchmark记录；更新的HANDOFF.md
风险	Ollama版本不满足MLX要求（回退：保持Metal后端，跳过MLX）
回退方案	MLX激活失败 → 跳过，记录到backlog，继续Wave 2
M2：重构完成（Day 8，Wave 2完成）
要素	内容
目标	消除最高优先级技术债，建立可维护代码基础
验收标准	orchestrator.py ≤ 50行；3个新模块各 ≤ 300行；39 cases全通过；ChromaDB去重验证通过；专家ID空值问题消失
交付物	agent_factory.py；knowledge_loader.py；team_orchestrator.py；Pydantic配置模型；更新的测试套件
风险	Agno API在提取过程中意外行为（防御：每个子任务后立即运行测试）
回退方案	任一模块提取失败 → git revert到上个提交点，保持orchestrator.py原样，记录失败分析
M3：能力解锁（Day 13，Wave 3完成）
要素	内容
目标	打通所有已设计但断路的功能
验收标准	流式输出实时可见；跨会话记忆正常；铁闸规则拦截验证通过；SKILL.md状态明确（接入或删除）
交付物	更新的cli.py（流式）；memory.db（初始化）；铁闸规则测试报告；HITL模板文件
风险	SqliteMemoryDb与Agno版本兼容性问题（防御：激活前先读Agno changelog）
回退方案	记忆激活失败 → 保持禁用状态，其余功能照常上线
M4：合规门控上线（Day 16，Wave 4中期）
要素	内容
目标	数据出境合规门控上线（P0合规里程碑）
验收标准	LOCAL_ONLY数据被自动拦截；CLI确认提示强制显示；单元测试拦截验证通过
交付物	EgressGuard模块；DataSensitivityLevel枚举；合规测试报告
风险	误拦截（合法数据被错误标记为LOCAL_ONLY）
回退方案	误拦截发生 → 调整DataSensitivityLevel默认值，不回滚EgressGuard（合规不可降级）
M5：外部API就绪（Day 18，Wave 4完成）
要素	内容
目标	DeepSeek V4 Pro完整接入，模型路由体系建立
验收标准	50次真实请求成功；成本记录 < $5；ModelRouter正确路由；forge hitl命令可用
交付物	更新的litellm-config.yaml；ModelRouter模块；50次请求基准报告；forge hitl命令
风险	DeepSeek API服务不稳定；数据隐私确认被用户习惯性跳过
回退方案	API不稳定 → 降级到本地35B，记录到DECISIONS.md；用户绕过 → 技术层强制（无法跳过）
M6：生产就绪（Day 25，Wave 5完成）
要素	内容
目标	系统达到长期可维护、可演进的生产就绪状态
验收标准	Agent抽象层验证通过；测试总数≥49；RAG评估得分>70%；benchmark三时间点对比完整；所有文档更新
交付物	BaseAgentInterface + AgnoAdapter；eval_rag.py + golden set；标准化benchmark报告；故障排查手册；更新的DECISIONS.md（D-013~D-015）
风险	Agent抽象层引入新的间接性导致调试困难
回退方案	抽象层不阻塞功能，仅影响长期维护，可推迟至Wave 6
7. Agent Execution Workflow
7.1 AI Agent在本次升级中的角色定义

text

⚠️ 约束前置：
├── 境外闭源模型（Claude/ChatGPT）：仅用于HITL节点，人工触发，文档交换
├── 本地模型（qwen35b/deepseek-r1）：用于代码生成辅助、文档生成
├── DeepSeek V4 Pro /GLM 5.1 API：用于非敏感的方案生成、文档分析
└── 所有Agent输出必须经人工审核后才能合入代码

7.2 Research Agent

职责： 每个Task开始前的信息收集

触发时机： 每个新TASK开始时

执行流程：

text

输入：TASK描述 + 当前代码上下文
    ↓
[本地qwen35b] 分析：
    1. 该Task涉及哪些现有代码（文件+函数）？
    2. 已知的风险点是什么（来自Dossier）？
    3. 是否有既有决策约束（DECISIONS.md）？
    ↓
输出：research/<TASK-ID>-pre-analysis.md
    （最大1000 tokens，结构化输出）

输出模板：

Markdown

## Task Pre-Analysis: TASK-2.1.1.1

### 涉及代码
- orchestrator.py: L120-L180 (ExpertFactory类)
- cli.py: L45 (import orchestrator)

### 已知风险
- Agno Agent构造参数在v2.6.14中已废弃memory参数
- YAML解析在嵌套结构时有已知失效路径

### 约束检查
- D-009: Peer-Review架构不得擅自修改
- C-03: 拆分后单模块必须<300行

### 推荐执行顺序
1. 先写测试（明确期望行为）
2. 提取类定义
3. 运行测试确认

7.3 Planning Agent

职责： Task级别的实施计划细化

触发时机： Research完成后、代码开始前

执行流程：

text

输入：research/<TASK-ID>-pre-analysis.md + 代码片段
    ↓
[本地qwen35b 或 DeepSeek V4 Pro（非敏感）] 生成：
    1. 具体代码修改步骤（伪代码级别）
    2. 预计影响范围
    3. 测试验证方案
    ↓
输出：planning/<TASK-ID>-implementation-plan.md
人工审核：是否与DECISIONS.md冲突？→ 批准/修改
    ↓
进入Coding Agent

7.4 Coding Agent

职责： 代码生成与修改

触发时机： Planning批准后

执行约束：

text

强制规则：
├── 单次代码变更范围 ≤ 100行（分批次）
├── 每次变更后立即运行：make test
├── 任何Agno API调用必须查阅v2.6.14文档
└── 禁止：未经Planning批准的架构变更

执行模式：
[本地qwen35b（代码）] 生成代码
    ↓
[本地deepseek-r1（逻辑验证）] 检查：
    1. 是否有明显逻辑错误？
    2. 是否违反约束C-01~C-05？
    3. 是否超过复杂度上限（300行/50行）？
    ↓
人工：审查diff，手动apply到代码库
    ↓
make test（自动）→ 通过 → 提交

7.5 Review Agent

职责： 代码质量门禁审查

触发时机： 每个Project（PROJ-X.X.X）完成后

审查清单（自动化）：

Python

# review_agent_checklist.py
CHECKS = [
    ("文件行数 ≤ 300", lambda f: count_lines(f) <= 300),
    ("函数行数 ≤ 50", lambda f: max_function_lines(f) <= 50),
    ("无sys.path.insert", lambda f: "sys.path.insert" not in read(f)),
    ("无手写YAML解析", lambda f: "_load_yaml_simple" not in read(f)),
    ("有docstring", lambda f: has_docstrings(f)),
    ("测试文件存在", lambda f: test_file_exists(f)),
]
# 输出：review/<PROJ-ID>-code-review.md

人工Review（HITL节点，高风险Task）：

text

触发条件：
├── 涉及EgressGuard逻辑
├── 涉及铁闸规则修改
├── 涉及Agno Team编排核心路径
└── 任何 > 50行的函数

执行：生成标准化文档 → 提交给 Claude.ai/ChatGPT（网页） → 粘贴结果到 decisions/<日期>-code-review-human.md

7.6 Testing Agent

职责： 测试方案生成与覆盖率追踪

触发时机： 每个TASK完成后（Coding完成，Review通过）

执行流程：

text

[本地qwen35b] 分析：
    1. 新代码的happy path是什么？
    2. 边界条件有哪些？
    3. 对应的Dossier已知问题是否已覆盖？
    ↓
生成测试用例代码建议
    ↓
人工：审查并添加到pytest
    ↓
make test → 确认新测试通过
    ↓
更新tests/COVERAGE.md（当前cases数量）

测试类型分配：

text

单元测试（快速，每次提交前）：
├── Pydantic模型校验
├── EgressGuard拦截逻辑
├── ChromaDB去重逻辑
└── 铁闸规则

集成测试（Wave结束时）：
├── orchestrator → Agno Team端到端
├── RAG检索完整链路
└── DeepSeek API调用链路

E2E测试（里程碑时）：
└── `debt review` 完整命令（含流式输出验证）

7.7 Documentation Agent

职责： 升级过程中的文档自动生成

触发时机： 每个Wave结束时

执行流程：

text

输入：本Wave的所有git commits + 代码变更
    ↓
[本地qwen35b] 生成：
    1. CHANGELOG.md新版本条目
    2. 新模块的API文档摘要
    3. 已修复技术债清单更新
    4. 新增已知限制（如有）
    ↓
人工审核：确认准确性
    ↓
提交到docs/目录

7.8 Agent协作时序图

text

Task开始
   ↓
Research Agent → pre-analysis.md（15min，本地模型）
   ↓
[人工：确认分析准确]
   ↓
Planning Agent → implementation-plan.md（20min，本地/DeepSeek）
   ↓
[人工：批准计划 / 修改冲突]
   ↓
Coding Agent → 代码diff（变长，本地模型）
   ↓
[人工：审查diff，apply代码]
   ↓
make test（自动）
   ↓ 通过？
是 → Review Agent checklist（自动，5min）
        ↓
     [高风险Task] → HITL Review（网页Claude/ChatGPT）
        ↓
     Testing Agent → 测试补充建议（10min）
        ↓
     [人工：添加测试]
        ↓
     make test（自动）→ 提交
否 → Coding Agent重新修复（限3次）→ 人工介入

8. Knowledge Capture Workflow
8.1 知识沉淀设计原则

text

原则：每一个解决方案，必须同时产生可复用的知识资产
工具：现有的 docs/ + DECISIONS.md + HANDOFF.md 体系
新增：lessons/ 目录（对应Dossier中的_factory/lessons/）

8.2 Task级知识捕获（每个Task结束时）

触发： 每个TASK完成，耗时 < 5分钟

模板： lessons/task-<ID>-lesson.md

Markdown

## Task TASK-2.1.2.2 完成记录

**完成时间：** 2026-06-17
**实际耗时：** 3.5h（计划3h）

### 解决方案摘要（3句话）
ChromaDB collection存在性检查：使用client.list_collections()
获取已有collection名称列表，与目标expert_id比对，存在则跳过
SimpleDirectoryReader的调用。

### 踩坑记录
- ChromaDB 0.6.x的API是list_collections()，不是get_collections()
- collection名称区分大小写，expert.yaml的id字段需要规范化

### 可复用模式
```python
# 标准ChromaDB去重检查（可直接复用）
def collection_exists(client, collection_name: str) -> bool:
    return collection_name in [c.name for c in client.list_collections()]

影响决策

无新决策，但建议在HANDOFF.md添加"ChromaDB collection命名规范"章节

text


### 8.3 Project级知识捕获（每个PROJ完成时）

**触发：** 每个Project（如PROJ-2.1.2）完成

**模板：** `lessons/project-<ID>-retro.md`

```markdown
## Project PROJ-2.1.2: knowledge_loader.py 完成复盘

**完成里程碑：** M2（重构完成）
**实际耗时：** 4.5h（计划4h）
**测试覆盖：** 原5 cases → 现8 cases

### What Worked
- 先写测试再提取代码：每次都立即发现接口设计问题
- Pydantic已就绪：知识库版本hash标记几乎零成本添加

### What Didn't Work
- ChromaDB API文档与实际版本有出入：文档说get_collection，实际是list_collections
- 解决：在research阶段直接读ChromaDB源码，不信文档

### 可复用流程
1. 提取前：先写测试明确接口
2. 提取中：每50行提交一次（不要积累大变更）
3. 提取后：立即运行全量测试，不要"等一下再跑"

### 下次同类任务预估调整
知识库类模块提取：基准+1.5h（文档不准确的时间预算）

8.4 Wave级知识捕获（每个Wave结束时）

触发： 每个Wave结束，Documentation Agent辅助生成

位置： docs/DEV_LOG.md 追加 + _factory/lessons/wave-<N>-retro.md

内容框架：

Markdown

## Wave 2 复盘：核心代码重构（Day 4-8）

### 目标达成情况
- orchestrator.py拆分：✅ 完成
- Pydantic配置：✅ 完成（提前1天）
- ChromaDB去重：✅ 完成
- 测试通过：✅ 39/39

### 实际vs计划偏差
总计划：17h | 实际：19h（+12%）
超时原因：ChromaDB API文档不准确（+2h）

### 架构洞察（供未来项目参考）
1. 单文件拆分的最佳时机：当文件超过300行时立即拆分，不要等到500+
2. Pydantic作为配置层的价值：5行BaseModel替代40行手写解析，且免费获得错误信息
3. ChromaDB文档可信度：只信源码，不信文档

### 知识库条目索引
本Wave产生知识：
- TASK-2.1.1.1: agent_factory提取模式
- TASK-2.1.2.2: ChromaDB去重标准实现
- TASK-2.2.1.3: Pydantic YAML校验模式
（可检索：lessons/*.md）

### 给下一个Wave的建议
Wave 3重点：小心SqliteMemoryDb与Agno的版本兼容性，先查changelog

8.5 升级全局知识捕获（M6完成时）

输出： docs/UPGRADE_LEARNINGS.md（永久保留，供未来项目参考）

内容：

Markdown

## FORGE Factory v1.0.5 → v2.0.0 升级经验总结

### 最有价值的5个经验
1. [技术] orchestrator单文件的危害：在250行时就开始预防性拆分
2. [流程] 每个Task先写测试：发现了3个设计问题，否则是运行时错误
3. [工具] Pydantic替代手写解析器：投入2h，节省未来20h调试时间
4. [合规] EgressGuard必须是技术层，不能是流程层（流程会被绕过）
5. [性能] MLX激活是最高ROI的单一操作（30分钟，2x速度提升）

### 最大的失败教训
[待升级完成后填写]

### 未来独立开发者AI项目架构检查清单
[ ] 单文件 < 300行
[ ] 配置层使用Pydantic
[ ] 向量库有去重机制
[ ] 外部API有数据分级门控
[ ] 框架通过抽象层隔离
[ ] 测试覆盖 > 80%
[ ] 有流式输出（用户体验）
[ ] 有跨会话记忆
[ ] 有备份机制
[ ] 有HITL标准文档格式

8.6 知识检索机制

text

当前知识检索：
├── docs/DECISIONS.md → 决策查询
├── HANDOFF.md → 操作SOP
├── _factory/lessons/*.md → 具体问题解决方案
└── docs/UPGRADE_LEARNINGS.md → 跨项目经验

未来增强（Wave 5后）：
└── 将lessons/目录接入FORGE工厂的RAG知识库
    → 使AI Agent可直接检索历史经验
    → 实现"工厂自我学习"闭环

9. Risk Register
9.1 技术风险
风险ID	描述	概率	影响	综合评分	缓解方案
TR-01	Agno v2.6.14在拆分过程中暴露未知breaking behavior	中	高	🔴 高	每个子任务后立即运行39 cases；保持git commit粒度极小（<50行/commit）
TR-02	MLX后端在M1 Max（非M3/M4）上表现不如预期	中	低	🟡 低	Fallback到Metal后端；不影响功能，仅影响速度
TR-03	ChromaDB 0.6.x API与代码预期不一致	高	中	🟠 中	直接读源码而非文档；先在独立脚本验证API再集成
TR-04	Pydantic迁移导致现有YAML配置不兼容	中	高	🟠 中	先只校验必填字段（id）；逐步加严格度；先跑完整测试套件
TR-05	SqliteMemoryDb激活后与Agno的版本兼容性	中	中	🟡 低	激活前查Agno changelog；失败则保持禁用，功能不依赖记忆
TR-06	EgressGuard误拦截导致正常工作流中断	低	中	🟡 低	提供override机制（需显式输入'OVERRIDE'）；记录所有拦截到日志
TR-07	Agent抽象层引入间接性导致调试困难	低	低	🟢 低	抽象层保持薄（< 100行）；保留Agno原始错误透传
9.2 成本风险
风险ID	描述	概率	影响	综合评分	缓解方案
CR-01	DeepSeek API调用成本超预期（单次>$0.1）	低	低	🟢 低	硬编码成本告警；ModelRouter优先本地模型
CR-02	50次基准测试产生意外高额费用	极低	低	🟢 低	基准测试用短case（<500 tokens input）；计算前估算费用
CR-03	M1 Max升级到更高机型（性能不足）	极低	高	🟡 低	64GB已验证可跑70B Q4；当前35B MoE足够；无升级压力
9.3 时间风险
风险ID	描述	概率	影响	综合评分	缓解方案
TIM-01	orchestrator.py拆分超时（依赖关系比预期复杂）	中	高	🟠 中	拆分前先做完整依赖图分析；预留buffer +2天
TIM-02	SKILL.md决策拖延（优柔寡断）	高	中	🟠 中	强制：Wave 3第一天上午做出决策，写入DECISIONS.md
TIM-03	独立开发者精力分散（其他业务打断）	高	中	🟠 中	WIP限制：每天只做一个TASK；不在Wave结束前切换Wave
TIM-04	Wave 4集成测试发现设计缺陷，需返工Wave 2/3	低	高	🟡 低	Wave 3结束时增加集成测试；EgressGuard设计前Review
9.4 模型风险
风险ID	描述	概率	影响	综合评分	缓解方案
MR-01	多Agent顺从性：Peer Review输出高置信度错误建议	高	高	🔴 高	铁闸规则作为最后防线；M4里程碑强制上线；所有策略需人工最终确认
MR-02	DeepSeek API服务不稳定或不可用	中	低	🟡 低	默认路由本地35B；DeepSeek是增强选项，不是依赖
MR-03	qwen35b模型在本地更新后Prompt失效	低	中	🟡 低	Prompt版本管理（在expert.yaml注明兼容模型版本）
MR-04	Ollama版本更新导致MLX/Metal后端行为变化	低	中	🟡 低	锁定Ollama版本在uv.lock；升级需先验证
9.5 依赖风险
风险ID	描述	概率	影响	综合评分	缓解方案
DR-01	Agno 2.6.x再次breaking change	高	高	🔴 高	Wave 5完成抽象层隔离；Wave 2前锁定agno==2.6.14
DR-02	LlamaIndex 0.12.x API重大变更（类似0.9→1.0）	低	中	🟡 低	知识加载器通过knowledge_loader.py封装，替换只需修改一个文件
DR-03	ChromaDB版本升级导致持久化格式不兼容	低	中	🟡 低	ChromaDB版本锁定；升级前备份runtime/chroma_data/
DR-04	macOS系统升级破坏Ollama/MLX兼容性	低	高	🟡 低	系统更新前先验证；有至少48h的回滚窗口
10. Rollback Strategy
10.1 回退原则

text

原则1：每个TASK级提交都是可回退点（git commit粒度）
原则2：每个Wave前打tag（v1.0.5-wave1-start等）
原则3：数据层（SQLite/ChromaDB）独立备份，代码回退不影响数据
原则4：合规功能（EgressGuard）不降级——即使系统回退，门控也保持

10.2 Tag策略

Bash

# Wave开始前：
git tag -a v1.0.5-pre-wave1 -m "Wave 1 开始前的稳定基线"
git tag -a v1.0.5-pre-wave2 -m "Wave 2 开始前（Wave1完成）"
# ... 以此类推

# Wave结束后（M验收通过）：
git tag -a v1.1.0-wave1-complete -m "M1 环境稳定里程碑通过"
git tag -a v1.2.0-wave2-complete -m "M2 重构完成里程碑通过"
git tag -a v2.0.0-production -m "M6 生产就绪里程碑通过"

10.3 场景化回退方案

场景A：单个TASK失败（最常见）

text

症状：某Task修改后make test失败，且30分钟内无法修复
操作：
  1. git revert <commit-hash>（回退单个提交）
  2. 记录失败原因：lessons/task-<ID>-failure.md
  3. 分析：是设计问题还是实现问题？
     ├── 设计问题 → 重回Planning Agent阶段
     └── 实现问题 → 修复后重新执行
  4. 重新执行Task（不跳过测试）

场景B：Wave内多个Task级联失败

text

症状：Wave进行到中途，发现基础设计有问题，3+个Task需返工
操作：
  1. git reset --hard <wave-start-tag>（回退到Wave开始）
  2. 保留：lessons/（不回退，包含失败分析）
  3. 重新进行Planning阶段（Research Agent重分析）
  4. 必须修改：在Planning阶段增加失败场景的明确处理
  5. 重新执行Wave

场景C：orchestrator.py拆分失败（高风险场景）

text

症状：拆分后debt review命令报错，且无法快速定位
紧急操作：
  1. git checkout v1.0.5-pre-wave2 -- peer_review/orchestrator.py
     （只回退orchestrator.py，保留其他Wave 2的改进）
  2. 验证：make test全通过
  3. 系统恢复可用
恢复后分析：
  1. 在独立分支重新尝试拆分
  2. 每次拆分后立即运行：python -c "from peer_review.orchestrator import build_review_team"
  3. 使用更小粒度提交（每个函数提取一次提交）

场景D：EgressGuard误拦截导致工作流中断

text

症状：EgressGuard阻止了不应该被阻止的合法操作
操作（不可完全禁用EgressGuard）：
  1. 识别被误标记的数据字段
  2. 调整DataSensitivityLevel默认值或字段白名单
  3. 在日志中记录所有拦截事件（已有日志系统）
  4. 如极端紧急：提供管理员级override（需输入特殊确认码）
  不可接受的回退：完全禁用EgressGuard（合规不可降级）

场景E：Agno版本升级导致系统崩溃（未来维护场景）

text

症状：升级Agno版本后，多个Agent相关测试失败
操作：
  1. pip install agno==<上一个稳定版本>（uv lock回退）
  2. 运行make test确认恢复
  3. 在升级分支分析breaking change
  4. 有了抽象层后：只修改AgnoAdapter，不修改上层代码
  5. 修改完成，验证通过后，合并到main

10.4 数据层回退策略

text

SQLite（debt.db）：
├── 每日备份到：runtime/backups/debt-<日期>.db
├── 回退命令：cp runtime/backups/debt-<日期>.db runtime/debt.db
└── 最长数据损失：1天

ChromaDB（chroma_data/）：
├── 每次知识库更新前手动备份
├── 回退命令：cp -r runtime/backups/chroma_data-<日期> runtime/chroma_data
└── 重建成本：10-30秒/专家（可接受）

runtime/memory.db（跨会话记忆）：
├── 非关键数据，可接受丢失
└── 回退：直接删除，下次自动重建

10.5 回退决策树

text

系统出现问题
    ↓
问题影响范围？
├── 单个命令失败 → 查日志 → Task级回退
├── 功能性退化 → 运行make test确认范围 → Wave级回退
├── 系统完全不可用 → git reset --hard <最近稳定tag>
└── 数据损坏 → 先恢复数据库 → 再处理代码

回退后必须：
└── 在lessons/记录回退原因和分析 → 纳入知识库

11. Quality Gates
Gate 0：每次代码提交前
检查项	工具	通过标准	失败动作
语法检查	python -m py_compile	无错误	修复后重提交
单元测试	make test	全部通过	不允许提交
文件行数	wc -l	修改文件 ≤ 300行	拆分后重提交
无禁止模式	grep检查	无sys.path.insert；无_load_yaml_simple	修复后重提交

实现方式（Makefile）：

Makefile

pre-commit:
    python -m py_compile $(CHANGED_FILES)
    pytest tests/ -q
    python scripts/check_file_size.py
    grep -r "sys.path.insert" src/ && echo "FAIL" || echo "OK"
    grep -r "_load_yaml_simple" src/ && echo "FAIL" || echo "OK"

commit: pre-commit
    git add .
    git commit -m "$(MSG)"

Gate 1：Wave 1完成（M1）

进入条件：

    M0已通过（baseline确认）
    当前39 cases全部通过

退出条件（全部必须满足）：
验收项	验证方法	最低标准
MLX后端	运行benchmark脚本	tok/s有可测量提升（>10%），或记录"M1 Max暂不支持"
Editable install	python -c "from peer_review.orchestrator import *"	成功导入，无sys.path错误
测试通过	make test	39/39
备份可运行	bash backup.sh && ls runtime/backups/	备份文件存在
Git流程	git log	有明确分支和提交规范
文档更新	cat HANDOFF.md	包含新的部署SOP

退出动作： git tag v1.1.0-wave1-complete
Gate 2：Wave 2完成（M2）

进入条件：

    M1已通过
    重构分支创建（feature/wave2-refactor）

退出条件（全部必须满足）：
验收项	验证方法	最低标准
文件大小	wc -l src/peer_review/*.py	每个文件 ≤ 300行
文件数量	ls src/peer_review/	至少包含：agent_factory.py, knowledge_loader.py, team_orchestrator.py
配置校验	python -c "from peer_review.config.expert_config import ExpertConfig"	成功导入
专家ID	手动运行debt review（查日志）	无"构建专家 向量索引"（ID为空）日志
ChromaDB去重	连续运行2次debt review，比较日志	第2次日志显示"跳过已存在索引"
测试通过	make test	39/39（无回归）
E2E功能	debt review "测试案件"	返回完整评审报告

退出动作： git tag v1.2.0-wave2-complete + 合并到main
Gate 3：Wave 3完成（M3）

进入条件：

    M2已通过
    SKILL.md决策已写入DECISIONS.md

退出条件（全部必须满足）：
验收项	验证方法	最低标准
流式输出	运行debt review，观察终端	看到逐步打印，无需等待全量
跨会话记忆	运行2次同案件review	第2次Agent引用上次结论
铁闸规则	运行铁闸测试用例	5条测试用例全部正确拦截
SKILL.md状态	ls _factory/skills/ 或 cat DECISIONS.md	已接入主流程 OR 已删除
HITL模板	ls decisions/_TEMPLATE-human-review.md	文件存在，格式完整
测试通过	make test	≥ 39/39（新增集成测试）

退出动作： git tag v1.3.0-wave3-complete
Gate 4：Wave 4完成（M5）

进入条件：

    M3已通过
    EgressGuard单元测试已覆盖
    DeepSeek API Key已配置

退出条件（全部必须满足）：
验收项	验证方法	最低标准
合规门控	运行EgressGuard测试	LOCAL_ONLY数据100%被拦截
确认提示	手动测试（输入非'YES'）	工作流中止，不发送数据
DeepSeek连通	运行API连通测试	50次请求成功率 ≥ 95%
成本记录	查看DeepSeek控制台	50次测试费用有记录（预计 < $1）
模型路由	运行路由测试case	快速任务→本地7B，敏感任务→本地35B
HITL命令	forge hitl discovery	生成标准化Markdown文档
测试通过	make test	≥ 42/42

退出动作： git tag v1.4.0-wave4-complete
Gate 5：Wave 5完成（M6，生产就绪）

进入条件：

    M5已通过
    所有前序Wave的lessons文档完整

退出条件（全部必须满足）：
验收项	验证方法	最低标准
抽象层验证	替换AgnoAdapter为MockAdapter，运行测试	上层代码无需修改即通过
RAG评估	python eval_rag.py	5个golden set问题，相关性得分 ≥ 70%
测试总数	pytest --collect-only | wc -l	≥ 49个test cases
基准对比	cat docs/benchmark.md	包含Wave1/3/5三个时间点数据
文档完整	ls docs/	包含：benchmark.md, UPGRADE_LEARNINGS.md, 故障排查手册
API文档	查看3个新模块	每个公开函数有docstring
决策记录	cat docs/DECISIONS.md	包含D-013~D-015

退出动作： git tag v2.0.0-production + 更新CHANGELOG.md
12. KPI System
12.1 技术指标
KPI	基线（M0）	Wave 2后（M2）	Wave 5后（M6）	测量方法
最大单文件行数	500+行	≤ 300行	≤ 300行（所有模块）	wc -l
测试case数量	39	42+	49+	pytest --collect-only
测试通过率	100%	100%	100%	make test
ChromaDB首次启动时间	10-30s/专家	≤ 2s（去重后）	≤ 2s	time bash -c "debt review 'x'"
专家ID空值频率	偶现	0次/100运行	0次/100运行	日志grep
Agno遥测请求	0（已阻断）	0	0	网络抓包确认
12.2 效率指标
KPI	基线（M0）	Wave 3后（M3）	Wave 5后（M6）	测量方法
单次评审等待时间（用户感知）	15-25分钟（全量等待）	立即有输出（流式）	立即有输出	秒表计时
单次评审总耗时	15-25分钟	~12-18分钟（MLX+流式）	~10-15分钟	benchmark脚本
推理速度（tok/s）	baseline	baseline × 1.5-2x（MLX）	baseline × 2x	ollama benchmark
发布一个patch的时间	15min（ZIP制作+上传）	5min（git push）	5min	计时
新专家接入时间	~30min（手动调试YAML）	~10min（Pydantic报错清晰）	~10min	计时
12.3 自动化指标
KPI	基线	目标（M6）	测量方法
自动化测试覆盖率	~60%（估计）	≥ 80%	pytest --cov
数据出境自动拦截率	0%（无机制）	100%（LOCAL_ONLY数据）	EgressGuard测试
索引重建自动跳过率	0%（每次重建）	100%（存在则跳过）	日志统计
模型路由自动化	0%（手动选择）	80%（任务驱动自动路由）	路由日志
数据备份自动化	0%	100%（每日自动）	cron验证
12.4 成本指标
KPI	基线	目标（M6）	测量方法
本地推理成本	$0	$0（保持）	电费（忽略不计）
外部API月成本	$0（未接入）	< $10/月（普通任务）	API控制台账单
高质量任务月成本	$0	< $50/月（按需）	API控制台账单
单次评审API成本	N/A	< $0.05（DeepSeek Flash）	API控制台
成本超标告警触发率	N/A	0次/月（良好控制）	告警日志
12.5 知识复用指标
KPI	基线	目标（M6）	测量方法
Lessons文档数量	0	≥ 15（每Wave产生3+）	ls lessons/*.md | wc -l
RAG golden set通过率	N/A	≥ 70%	eval_rag.py
故障排查手册覆盖率	0条	≥ 10个常见错误场景	手册条目数
新项目接入时间（借助工厂）	未测量	< 2天启动新试点项目	下次项目计时
HITL文档交换效率	临时	≤ 30秒内可粘贴	实际操作计时
12.6 KPI仪表板（简化版，每Wave更新）

Markdown

## FORGE Factory 升级KPI仪表板

更新时间：[Wave结束日期]

| 维度 | M0 | M1 | M2 | M3 | M4 | M5 | M6目标 |
|------|----|----|----|----|----|----|--------|
| 最大文件行数 | 500+ | - | 300 | - | - | - | 300 |
| 测试cases | 39 | 39 | 42 | 45 | 47 | 49 | 49+ |
| tok/s提升 | 1x | 2x | 2x | 2x | 2x | 2x | 2x |
| 启动时间 | 30s | 30s | 2s | 2s | 2s | 2s | 2s |
| 月API成本 | $0 | $0 | $0 | $0 | $0 | <$10 | <$10 |
| 数据门控 | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| 流式输出 | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| 跨会话记忆 | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |

13. Prioritized Roadmap
13.1 Must Have（不做则升级失败）
优先级	任务	ROI	风险	复杂度	长期价值	执行Wave
P0-1	orchestrator.py拆分（3模块）	🔴极高	🔴高	🟠中	🔴极高	Wave 2
P0-2	Pydantic配置替换手写解析器	🔴极高	🟠中	🟢低	🔴极高	Wave 2（先）
P0-3	ChromaDB索引去重	🔴极高	🟢低	🟢低	🟠中	Wave 2
P0-4	EgressGuard数据出境门控	🟠中	🟢低	🟠中	🔴极高	Wave 4
P0-5	MLX后端激活	🔴极高	🟢低	🟢极低	🟠中	Wave 1（优先）
P0-6	Agno框架版本锁定+升级保护流程	🔴极高	🔴高	🟢低	🔴极高	Wave 1
P1-1	流式输出激活	🔴极高	🟢低	🟢极低	🟠中	Wave 3
P1-2	SqliteMemoryDb挂载	🟠中	🟢低	🟢极低	🟠中	Wave 3
P1-3	分层决策引擎接入主流程	🟠中	🟠中	🟠中	🔴极高	Wave 3
P1-4	pyproject.toml editable install	🟠中	🟢低	🟢低	🟠中	Wave 1
P1-5	结构化日志系统	🟠中	🟢低	🟢低	🟠中	Wave 2
13.2 Should Have（不做则升级质量受损）
优先级	任务	ROI	执行Wave
P1-6	DeepSeek V4 Pro API接入	高（能力扩展）	Wave 4
P1-7	Git标准化发布流程	中（效率）	Wave 1
P1-8	数据备份自动化	高（安全）	Wave 1
P1-9	HITL文档交换标准化	中（流程规范）	Wave 3
P2-1	Agent接口抽象层（Agno隔离）	极高（长期维护）	Wave 5
P2-2	RAG质量基础评估（golden set）	中（质量保障）	Wave 5
P2-3	SKILL.md接入或删除（二选一）	中（消除噪音）	Wave 3
13.3 Nice To Have（有余力则做）
任务	ROI	建议时机
本地Langfuse自托管（可观测性）	中	Wave 5之后，当Agent行为难以追踪时
DeepSeek V4 Pro接入（高质量任务）	中	当本地35B质量明显不足时
RAG混合检索（BM25+向量）	中	当检索召回率成为明显瓶颈时
70B本地模型（Llama3.3 Q4）	中	当35B质量不足，且接受更慢推理时
forge new <project>脚手架生成	高	第二个试点项目启动时
13.4 Avoid（明确不做，防止范围蔓延）
任务	避免原因
FastAPI服务化	无并发需求；增加运维复杂度；Wave 5之后再评估
Docker容器化	单机本地无需容器；时机不对
完整RAGAS评估管道	需要Ground Truth；独立开发者无法标注
Fine-Tuning/LoRA	工程复杂度超限；ROI不足
A2A/MCP协议	生态未成熟；2027年后再看
Web UI（React/Next.js）	前端技术栈增加；CLI当前够用
并行Multi-Agent执行	Agno非线程安全；需框架底层支持
OpenAI/Claude API自动调用	硬性约束（无法实现）
3个项目同时高强度并行	超出独立开发者认知负荷
LangSmith云端遥测	数据出境；独立开发者不需要企业级追踪
同模型多Agent评审>3轮	Token成本线性增加；顺从性风险超过质量收益
13.5 执行顺序可视化

text

Week 1（Day 1-5）：
Day 1: MLX激活 + Git流程 + 备份脚本                 [Wave 1]
Day 2: pyproject.toml + Makefile                    [Wave 1]
Day 3: baseline benchmark + HANDOFF更新 + M1验收    [Wave 1✓]
Day 4: SKILL.md决策 + Pydantic配置模型               [Wave 2开始]
Day 5: 替换YAML解析器 + 更新expert.yaml              [Wave 2]

Week 2（Day 6-10）：
Day 6: 提取agent_factory.py                         [Wave 2]
Day 7: 提取knowledge_loader.py（含去重）             [Wave 2]
Day 8: 提取team_orchestrator.py + 日志系统 + M2验收 [Wave 2✓]
Day 9: 流式输出 + 记忆激活                           [Wave 3开始]
Day 10: SKILL.md执行 + HITL模板                     [Wave 3]

Week 3（Day 11-15）：
Day 11: 分层决策引擎接入 + 铁闸测试                 [Wave 3]
Day 12: 集成测试补充 + M3验收                       [Wave 3✓]
Day 13: EgressGuard设计 + 数据分级                  [Wave 4开始]
Day 14: EgressGuard实现 + 单元测试 + M4验收（合规）  [Wave 4]
Day 15: DeepSeek litellm配置 + ModelRouter           [Wave 4]

Week 4（Day 16-20）：
Day 16: DeepSeek 50次基准测试 + 成本记录             [Wave 4]
Day 17: forge hitl命令 + M5验收                     [Wave 4✓]
Day 18: Agent抽象层设计 + BaseAgentInterface         [Wave 5开始]
Day 19: AgnoAdapter实现 + 验证                      [Wave 5]
Day 20: RAG golden set创建 + eval_rag.py            [Wave 5]

Week 5（Day 21-25）：
Day 21: 性能benchmark标准化 + run_benchmark.sh       [Wave 5]
Day 22: 测试补充（目标49+ cases）                   [Wave 5]
Day 23: API文档 + 故障排查手册                      [Wave 5]
Day 24: DECISIONS.md更新 + UPGRADE_LEARNINGS.md     [Wave 5]
Day 25: 最终验收测试 + M6验收 + v2.0.0 tag          [Wave 5✓]

14. Execution Review
14.1 计划的内在假设与风险

假设1：独立开发者每天可投入4-6小时

    风险：业务运营打断实际工时
    缓解：每个Wave有2天buffer；WIP原则（当天只做一个Task）

假设2：Agno 2.6.14 API在拆分过程中保持稳定

    风险：orchestrator.py提取过程中发现未知行为
    缓解：每个子任务后立即运行全量测试；提交粒度极小

假设3：MLX后端在M1 Max 64GB上可用

    风险：M1 Max（非M3/M4）MLX支持有限
    缓解：Wave 1第一天验证，失败则skip，不影响整体计划

假设4：EgressGuard设计足够灵活不误拦截

    风险：正常数据被误标记为LOCAL_ONLY
    缓解：默认值从宽，逐步加严；提供日志审计

14.2 此计划与"Big Bang Rewrite"的关键区别

text

Big Bang Rewrite（禁止）：
├── 停止所有新功能
├── 完整重写orchestrator.py
├── 一次性切换
└── 风险：重写期间系统不可用，重写后大量未知问题

本计划（增量演进）：
├── Wave 1：不触碰任何业务逻辑
├── Wave 2：拆分但保持orchestrator.py兼容入口（薄包装）
├── Wave 3：激活已有功能，不写新功能
├── Wave 4：集成外部能力，有完整门控
├── Wave 5：添加长期防护，不改功能
└── 每个Wave结束后：debt review命令必须可正常运行

14.3 最高价值的三件事（按ROI排序）

第一：MLX后端激活（Day 1，约30分钟，2x速度提升） 这是整个计划中投入产出比最高的单一操作。在Wave 1第一天，先做这件事。

第二：Pydantic替换手写YAML解析器（Wave 2，约5小时） 这一改变消除了最脆弱的技术债，且为后续所有改进（orchestrator拆分、专家ID修复）提供稳定基础。投入5小时，节省未来50小时调试。

第三：EgressGuard数据门控上线（Wave 4，约8小时） 这是合规要求，也是系统信任度的基础。一旦上线，所有外部API集成都有了可靠的安全边界。
14.4 最高风险的三件事（按影响排序）

第一：orchestrator.py拆分（Wave 2） 这是整个升级中唯一能导致系统完全不可用的操作。缓解：极小提交粒度；每步测试；完整回滚策略。

第二：Agno框架API不稳定性（贯穿全程） 升级Agno版本是定时炸弹。缓解：版本锁定至M5；Wave 5完成抽象层后才考虑升级。

第三：多Agent顺从性导致法律建议错误（当前+未来） 这不是升级问题，是系统设计问题。缓解：铁闸规则（Wave 3上线）；所有策略必须人工最终确认（不可完全自动化）。
14.5 执行纪律检查清单（每天开始时）

text

每日晨检（5分钟）：
[ ] 今天只做一个Task
[ ] Task开始前运行make test（确认基线）
[ ] 有Research Agent的pre-analysis
[ ] 有Planning Agent的implementation-plan（人工批准）
[ ] 知道今天的回退点在哪里

每日收尾（5分钟）：
[ ] 今天的工作已提交（不留uncommitted changes过夜）
[ ] make test全部通过
[ ] 今天的lesson已记录（lessons/task-<ID>-lesson.md）
[ ] debt review命令仍可正常运行（哪怕今天是重构日）

14.6 成功的最终定义

当以下所有条件同时成立，升级宣告成功：

text

技术成功：
✅ orchestrator.py ≤ 50行（兼容入口）
✅ 3个模块各 ≤ 300行
✅ 测试 ≥ 49 cases，全部通过
✅ ChromaDB去重正常
✅ 流式输出可用
✅ 跨会话记忆激活
✅ 铁闸规则正常工作
✅ EgressGuard拦截验证通过
✅ DeepSeek API连通
✅ Agent抽象层就绪

运营成功：
✅ 独立开发者可在2小时内理解任意单个模块
✅ 新专家接入时间 < 10分钟
✅ 月API成本 < $10（普通使用）
✅ 系统在完全离线状态下可正常运行

知识成功：
✅ 15+个lessons文档（供未来项目检索）
✅ 故障排查手册覆盖10+个场景
✅ UPGRADE_LEARNINGS.md完整记录本次升级经验
✅ DECISIONS.md包含D-001~D-015

合规成功：
✅ LOCAL_ONLY数据从未意外出境
✅ 每次外部API调用有日志记录
✅ HITL节点有标准化文档格式

计划签发： Architecture Transformation Director 有效期： 本计划在 M0 验收通过后正式生效 修订机制： 每个Wave结束时，根据实际执行情况更新下一Wave细节 总原则最终重申： 每一天结束时，debt review 命令必须可以运行。这是唯一不可动摇的底线。