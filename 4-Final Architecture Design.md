FORGE Factory — Final Architecture Design (v1.1.0 完整版)

文档类型： Chief Architect Final Output 版本： v1.1.0 日期： 2026-06-14 状态： 🔴 待实施 修订说明： 六项修订：放宽复杂度预算为原则导向、立即迁移 LangGraph、双文件模型管理体系、HUB-SPOKE 评审优先并提供多方案菜单、IDE 层明确为 Claude Code + LiteLLM、数据出境策略文件化
Executive Summary

FORGE Factory 的根本问题不是"缺功能"，而是"复杂度已超出单人可控边界，且核心价值尚未被完整激活"。

当前系统在两个方向同时失控：向上，Agno 框架绑定与 500 行单文件编排器构成定时炸弹；向下，SKILL.md 技能系统、分层决策引擎、跨会话记忆三个高价值模块已设计但全部断路。

本架构（v1.1.0）的核心判断是：

    不需要更多功能。需要立即迁移 LangGraph 消除根源风险；需要双文件模型管理体系让模型切换成为一行配置；需要把已有 60% 的代码激活；需要把数据出境策略权还给人。

目标架构的六个关键决策：

    Agno → LangGraph 立即迁移：不再通过抽象层推迟，直接解决根源，一次性付出迁移成本，终身受益于稳定 API 和原生 HUB-SPOKE 支持。
    双文件模型管理体系：A 文件（models.yaml）定义所有可用模型，B 文件（routing_plans.yaml）定义各节点调用方案，切换只改一个字段名。
    HUB-SPOKE 优先，多方案菜单：先展示每种方案的质量预期、耗时和成本，你来选择，系统来执行。
    数据出境策略文件化：不是代码硬编码"什么数据能出去"，而是你写 privacy_policy.yaml，DataPrivacyGate 执行你的策略。
    IDE 层：Claude Code for VS Code + LiteLLM：开发工具通过 LiteLLM 统一接入本地和外源模型，与 Agent 工作流共享同一个模型网关。
    复杂度以"流畅好用"为基准：去除死板数字限制，代之以设计原则和触发重构的信号。

单人三年可维护性判定：✅ 通过。
1. Architecture Foundations
1.1 必须保留内容
方法论层（永久保留，与代码无关）
资产	保留理由	价值属性
五阶段工作流（DISCOVERY→SPEC→BUILD→HARDEN→RETRO）	方法论护城河，10 年不会过时	永久资产
分层决策引擎（铁闸→AI参考→AI生成）的思想	法律合规底线，不可 AI 化	永久资产
HANDOFF.md + DECISIONS.md 文档体系	独立开发者的外化记忆，防止知识丢失	永久资产
专家知识库（领域 Markdown 文档）	差异化来源，时间越久价值越高	累积资产
技术层（保留并强化）
组件	保留理由	优化方向
Ollama 本地推理	数据隐私核心保障，零成本	启用 MLX 后端约 2x 加速
ChromaDB 本地向量库	无需独立服务，轻量	修复去重机制，增加版本控制
LlamaIndex 文档加载器	成熟稳定，替代成本高	保持版本锁定
SQLite 数据层	极稳定，无依赖，足够当前规模	新增 ModelRunRecord 表
CLI 入口（cli.py）	当前阶段最低摩擦，单人维护友好	增加流式输出、方案选择菜单
pytest 测试套件（39 cases）	框架升级的安全网	补充集成测试至 60+
YAML 专家配置（expert.yaml）的格式概念	配置驱动可扩展性	解析层迁移到 Pydantic
1.2 必须改变内容
问题	现状	目标状态	优先级
Agno 框架（立即迁移）	深度耦合，API 不稳定，6 个月内 3+ 次 breaking changes	迁移到 LangGraph 1.0（API 稳定承诺，原生 HUB-SPOKE）	P0 最高
orchestrator.py 500+ 行单文件	一个文件承担 5 种职责	拆分为职责清晰的多个文件	P0
手写 YAML 解析器	扁平结构限制，脆弱	Pydantic BaseModel 严格校验	P0
ChromaDB 无去重机制	每次启动重建索引	collection 存在性检查 + VERSION 文件	P0
PYTHONPATH 硬编码	环境切换必然失败	pyproject.toml editable install	P0
模型路由无配置化管理	散落在代码中，切换需改代码	双文件模型管理体系（A 文件 + B 文件）	P0
IDE 层未明确	模糊	Claude Code for VS Code + LiteLLM Gateway + 本地/外源模型	P0
防御性 try-except 覆盖	掩盖真实错误	启动时一次性检查，运行时明确报错	P1
流式输出未启用	等待 15-25 分钟无任何反馈	LangGraph stream_mode 实时打印	P1
多 Agent 顺从性风险	顺序模式，评审者互相可见	HUB-SPOKE 优先，多方案菜单供选择	P1
数据出境策略硬编码	代码写死"什么能出去"	策略文件化（privacy_policy.yaml），DataPrivacyGate 执行	P1
SKILL.md 未接入主流程	设计存在但完全无用	立即二选一：接入或删除	P1
分层决策引擎孤岛	代码存在但断路	接入 LangGraph 图节点主流程	P1
跨会话记忆未挂载	SqliteMemoryDb 代码存在但未启用	激活，并增加 ModelRunRecord 方案对比记录	P1
ZIP 补丁部署流程	每次发布手动操作	Git tag + Makefile 自动化	P2
1.3 必须删除内容
内容	删除理由
Agno 全部相关代码（迁移验证通过后）	根源风险消除，保持代码库干净
AgentRuntime 抽象层（不再需要）	LangGraph 1.0 直接使用，无需抽象
未来 6 个月的 Web UI 计划	过早投入，当前 CLI 完全够用
未来 6 个月的 FastAPI 服务化计划	无并发需求，增加不必要复杂度
完整 RAGAS 评估管道（当前阶段）	需要 Ground Truth，独立开发者无法实现
Docker 容器化（当前阶段）	单机本地不需要容器
Fine-Tuning 闭环（短期）	工程复杂度超出单人上限
LangSmith 云端遥测	数据出境，独立开发者不需要企业级追踪
超过 5 个顺序 Agent 且无信息隔离的评审链	顺从性风险高于质量收益
2. Target Architecture
2.1 总体分层

text

┌──────────────────────────────────────────────────────────────────────┐
│                          核心层 (Core Layer)                          │
│      五阶段工作流方法论 + 分层决策引擎 + 专家知识体系                    │
│      （与任何技术实现无关，永久稳定）                                    │
└──────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────┐
│                        平台层 (Platform Layer)                        │
│  ┌─────────────────┐  ┌────────────────┐  ┌──────────────────────┐   │
│  │  LangGraph 1.0  │  │  KnowledgeHub  │  │  DecisionEngine      │   │
│  │  (图编排引擎)    │  │  (知识统一接口) │  │  (铁闸+AI混合决策)   │   │
│  └─────────────────┘  └────────────────┘  └──────────────────────┘   │
│  ┌─────────────────┐  ┌────────────────┐  ┌──────────────────────┐   │
│  │  ModelRegistry  │  │  MemoryStore   │  │  DataPrivacyGate     │   │
│  │  (A文件驱动)    │  │  (记忆+对比DB) │  │  (策略文件驱动)      │   │
│  └─────────────────┘  └────────────────┘  └──────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  RoutingPlanEngine  (B 文件驱动的节点路由引擎)                   │   │
│  └────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────┐
│                         工具层 (Tool Layer)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐    │
│  │ ExpertDef│  │ SkillLib │  │ Pipeline │  │  ProjectTemplate   │    │
│  │ (专家配置) │  │ (技能库) │  │ (流水线) │  │  (项目脚手架)      │    │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────┐
│                      基础设施层 (Infra Layer)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐    │
│  │  Ollama  │  │ ChromaDB │  │  SQLite  │  │  External APIs     │    │
│  │ +MLX后端 │  │ (向量库) │  │ (业务DB) │  │(DeepSeek/GLM/Qwen) │    │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────────┘    │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  LiteLLM Gateway  (统一模型网关，A 文件驱动，localhost:4000)     │   │
│  └────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘

IDE 层：Claude Code for VS Code → LiteLLM Gateway (4000) → 本地/外源模型

2.2 模块级设计
核心层：五阶段工作流方法论（非代码，文档定义）

text

DISCOVERY  → 问题研究 + 可行性判断（人工主导 + AI 辅助）
SPEC       → 需求规格 + 架构决策（AI 主导 + 人工验证）
BUILD      → 核心功能开发（AI 工具辅助 + 人工把关）
HARDEN     → 测试、安全、性能优化（自动化主导）
RETRO      → 复盘、经验萃取、知识库更新（人工主导）

核心层：分层决策引擎（DecisionEngine）

Python

# 职责：严格三层，铁闸层由 Python 代码保证确定性，不可 AI 化
# 在 LangGraph 图中作为独立节点调用

class DecisionEngine:
    def decide(self, context: DecisionContext) -> Decision:
        # 层1：铁闸（硬编码规则，100% 确定性）
        gate_result = self._iron_gate_check(context)
        if gate_result.is_blocked:
            return Decision.blocked(reason=gate_result.reason)

        # 层2：AI 参考（本地模型风险评分，0-1）
        ai_score = self._ai_reference(context)

        # 层3：AI 生成（基于评分决定生成策略）
        return self._ai_generate(context, ai_score)

    def _iron_gate_check(self, context: DecisionContext) -> GateResult:
        # 硬编码规则列表，每条规则有对应单元测试
        # 不依赖任何 LLM，不依赖任何外部服务
        for rule in self.iron_gate_rules:
            if rule.matches(context):
                return GateResult.blocked(rule.reason)
        return GateResult.passed()

平台层：LangGraph 图编排引擎

Python

# 直接使用 LangGraph 1.0 API，无需适配层
from langgraph.graph import StateGraph, END
from langgraph.types import Send
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

# 图状态：所有 Agent 数据在此显式管理，无隐式状态
class ReviewState(TypedDict):
    case_context: str              # 案件上下文（原始输入）
    primary_analysis: str          # 主专家分析结论
    reviewer_opinions: list[str]   # 各评审独立意见（HUB-SPOKE 收集）
    reviewer_roles: list[str]      # 对应角色标签
    consensus: str                 # 最终汇总结论
    divergence_score: float        # 评审间分歧度（0-1）
    requires_human: bool           # 是否触发人工仲裁
    model_plan_id: str             # 本次使用的方案 ID（用于对比记录）
    models_used: dict[str, str]    # 各节点实际使用的模型
    iron_gate_triggered: bool      # 铁闸是否触发
    iron_gate_reason: str          # 铁闸触发原因

# 图构建（HUB-SPOKE 模式）
def build_review_graph(routing_engine: RoutingPlanEngine) -> StateGraph:
    builder = StateGraph(ReviewState)

    builder.add_node("primary_expert", make_primary_node(routing_engine))
    builder.add_node("reviewer", make_reviewer_node(routing_engine))
    builder.add_node("consensus_builder", make_consensus_node(routing_engine))
    builder.add_node("human_review_gate", human_review_interrupt)

    # HUB-SPOKE：主专家完成后并行分发给所有评审者
    builder.add_edge("primary_expert", "reviewer_dispatcher")
    builder.add_node("reviewer_dispatcher", dispatch_to_reviewers)

    # 条件路由：分歧低 → 直接汇总，分歧高 → 人工仲裁
    builder.add_conditional_edges(
        "consensus_builder",
        lambda state: "human_review_gate" if state["requires_human"] else END
    )

    # 检查点：每个节点完成后自动持久化
    conn = sqlite3.connect("runtime/checkpoints.sqlite", check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    return builder.compile(checkpointer=checkpointer, interrupt_before=["human_review_gate"])

平台层：RoutingPlanEngine（B 文件驱动）

Python

# 职责：加载 routing_plans.yaml，根据激活方案确定各节点模型
# 支持方案切换、GPU 内存预检、并行安全验证

class RoutingPlanEngine:
    def __init__(self, models_path: Path, plans_path: Path):
        self.models = ModelRegistry.from_yaml(models_path)     # A 文件
        self.plans = RoutingPlans.from_yaml(plans_path)        # B 文件
        self.validate_consistency()  # 启动时强制交叉验证

    def get_model_for_node(self, node_name: str) -> ModelConfig:
        active = self.plans.active_plan
        return self.models.get(active.nodes[node_name].model)

    def validate_consistency(self) -> None:
        """A 文件和 B 文件交叉验证：B 文件引用的所有模型名必须在 A 文件中存在"""
        available = set(self.models.models.keys())
        errors = []
        for plan_id, plan in self.plans.plans.items():
            for node_name, node_cfg in plan.nodes.items():
                if node_cfg.model not in available:
                    errors.append(
                        f"方案 '{plan_id}' 节点 '{node_name}' "
                        f"引用了未定义的模型 '{node_cfg.model}'"
                    )
        if errors:
            raise ConfigurationError("模型配置不一致：\n" + "\n".join(errors))

    def check_parallel_memory_safety(self, plan_id: str) -> MemorySafetyResult:
        """检查并行执行时是否超出可用内存（保守估计 + 15% 缓冲）"""
        plan = self.plans.plans[plan_id]
        parallel_nodes = [n for n in plan.nodes.values() if n.execution == "parallel"]
        local_parallel = [n for n in parallel_nodes
                          if self.models.get(n.model).type == "local"]
        total_mem = sum(self.models.get(n.model).memory_required_gb
                        for n in local_parallel)
        total_mem_with_buffer = total_mem * 1.15 + 8  # 系统保留 8GB
        available_mem = 64  # M1 Max 64GB

        if total_mem_with_buffer > available_mem:
            return MemorySafetyResult.UNSAFE(
                message=f"并行内存需求 {total_mem_with_buffer:.1f}GB 超出 {available_mem}GB，"
                        f"将自动降级为信息屏蔽顺序模式"
            )
        return MemorySafetyResult.SAFE(estimated_gb=total_mem_with_buffer)

    def list_plans_summary(self) -> list[PlanSummary]:
        """供 CLI 展示方案菜单：包含描述、评审模式、预估时间、预估成本、预估内存"""
        summaries = []
        for plan_id, plan in self.plans.plans.items():
            mem_check = self.check_parallel_memory_safety(plan_id)
            summaries.append(PlanSummary(
                plan_id=plan_id,
                description=plan.description,
                estimated_time=plan.estimated_total_time,
                estimated_cost=plan.estimated_cost,
                memory_safe=mem_check.is_safe,
                is_active=(plan_id == self.plans.active_plan)
            ))
        return summaries

平台层：DataPrivacyGate（策略文件驱动）

Python

# 职责：读取 privacy_policy.yaml，执行人类定义的数据出境策略
# 不自己决定策略，只执行策略

class DataPrivacyGate:
    def __init__(self, policy_path: Path):
        self.policy = PrivacyPolicy.from_yaml(policy_path)

    def check(self, data: SensitiveData, target_endpoint: str) -> GateDecision:
        decisions = []
        endpoint_cfg = self.policy.endpoints[target_endpoint]

        for field_name, value in data.fields.items():
            field_policy = self.policy.fields.get(field_name)
            if field_policy is None:
                # 未定义字段默认最保守策略
                decisions.append(GateDecision.REQUIRES_HUMAN(field=field_name))
                continue

            match field_policy.policy:
                case "local_only":
                    if target_endpoint != "local_model":
                        decisions.append(GateDecision.BLOCKED(field=field_name))
                case "mask_then_allow":
                    masked = self.masking_pipeline.apply(value, field_policy.mask_rule)
                    decisions.append(GateDecision.MASKED(field=field_name, masked_value=masked))
                case "human_approve":
                    decisions.append(GateDecision.REQUIRES_HUMAN(field=field_name))
                case "allow":
                    decisions.append(GateDecision.APPROVED(field=field_name))

        return self._aggregate(decisions)

    def request_human_approval(self, fields: list[str], preview: dict) -> bool:
        """
        人工审核门：必须显式输入 "yes"，不接受 y/Y/回车
        审核决策记录到审计日志
        """
        print("\n⚠️  [数据出境审核]")
        print("以下字段将发送到外部端点：")
        for field in fields:
            print(f"  • {field}：{preview.get(field, '(已脱敏)')}")
        print()
        response = input("确认发送？请输入 yes 确认，其他任意键取消：").strip().lower()
        approved = (response == "yes")
        self._log_approval(fields, approved)  # 审计日志，不可跳过
        return approved

平台层：KnowledgeHub（知识统一接口）

Python

# 职责：统一管理 ChromaDB + LlamaIndex
# 核心：存在性检查 + VERSION 版本控制，修复去重 Bug

class KnowledgeHub:
    def load_expert_knowledge(self, expert_id: str) -> KnowledgeBase:
        if self._is_index_current(expert_id):
            return self._load_existing(expert_id)
        return self._build_and_persist(expert_id)

    def _is_index_current(self, expert_id: str) -> bool:
        """双重检查：collection 是否存在 + 版本是否与磁盘一致"""
        collection = self.chroma.get_collection(expert_id)
        if collection is None:
            return False
        version_file = self.knowledge_path / expert_id / "VERSION"
        if not version_file.exists():
            return False
        current_version = version_file.read_text().strip()
        indexed_version = collection.metadata.get("version", "unknown")
        return current_version == indexed_version

    def _build_and_persist(self, expert_id: str) -> KnowledgeBase:
        # 构建索引时写入版本号到 collection metadata
        docs = SimpleDirectoryReader(self.knowledge_path / expert_id).load_data()
        collection = self.chroma.create_collection(
            expert_id,
            metadata={
                "version": self._get_current_version(expert_id),
                "built_at": datetime.now().isoformat()
            }
        )
        # ... 向量化并存入 collection
        return KnowledgeBase(collection=collection)

    def inject_skill(self, skill_id: str, agent_context: dict) -> None:
        """将 SKILL.md 技能文件内容注入 Agent 上下文"""
        skill_path = self.skills_path / f"{skill_id}.skill.md"
        if skill_path.exists():
            agent_context["injected_skills"] = skill_path.read_text()

    def search(self, query: str, expert_id: str, top_k: int = 5) -> list[Document]:
        collection = self._load_existing(expert_id)
        return collection.query(query_texts=[query], n_results=top_k)

平台层：MemoryStore（含模型方案对比记录）

Python

# 职责：跨会话记忆 + 模型方案运行记录（供 forge compare-plans 使用）

class MemoryStore:
    def record_run(self, record: ModelRunRecord) -> None:
        """每次评审结束后自动记录，用于方案对比分析"""
        ...

    def get_plan_comparison(self, days: int = 30) -> list[PlanComparisonRow]:
        """查询最近 N 天内各方案的质量、耗时、成本对比"""
        ...

class ModelRunRecord(BaseModel):
    run_id: str
    case_hash: str               # 相同案件的哈希，用于跨方案对比
    plan_id: str                 # 使用的方案 ID
    models_used: dict[str, str]  # 各节点实际使用的模型
    total_time_seconds: int
    total_cost_usd: float
    divergence_score: float      # 评审间分歧度
    human_quality_score: Optional[int]  # 用户事后评分（1-5），可选
    adopted_by_user: Optional[bool]     # 用户是否采纳了建议
    created_at: str

2.3 文件结构（重构后）

text

_factory/patterns/peer-review/src/peer_review/
├── graph/
│   ├── review_graph.py        # LangGraph StateGraph 定义，HUB-SPOKE 结构
│   ├── nodes/
│   │   ├── primary_expert.py  # 主专家节点
│   │   ├── reviewer.py        # 评审者节点（信息屏蔽）
│   │   └── consensus.py       # 汇总节点 + 分歧检测
│   └── checkpointer.py        # SqliteSaver 初始化
├── platform/
│   ├── knowledge_hub.py       # KnowledgeHub：ChromaDB + LlamaIndex
│   ├── decision_engine.py     # DecisionEngine：铁闸 + AI 参考 + AI 生成
│   ├── model_registry.py      # ModelRegistry：A 文件解析
│   ├── routing_plan_engine.py # RoutingPlanEngine：B 文件驱动
│   ├── memory_store.py        # MemoryStore：跨会话记忆 + 方案对比
│   └── data_privacy_gate.py   # DataPrivacyGate：策略文件驱动
└── config/
    ├── schemas.py             # Pydantic Schema：Expert、Model、Plan、Policy
    └── loader.py              # 统一配置加载入口

文件职责隔离规则：

    review_graph.py 不直接调用 Ollama，通过 RoutingPlanEngine 获取模型配置
    knowledge_hub.py 不知道 LangGraph 存在
    decision_engine.py 不依赖任何 Agent 框架
    data_privacy_gate.py 不知道具体业务逻辑，只执行策略文件

2.4 数据流设计

text

用户输入（CLI）
    │
    ▼
[DataPrivacyGate.check()] ─── 读取 privacy_policy.yaml ─── 触发人工确认（策略定义）
    │ 通过
    ▼
[RoutingPlanEngine.list_plans_summary()] ── 展示方案菜单 ── 用户选择
    │ 选定方案
    ▼
[RoutingPlanEngine.check_parallel_memory_safety()] ── GPU 内存预检
    │ 安全/降级
    ▼
[LangGraph StateGraph.stream(input, config)]
    │
    ├─── primary_expert 节点
    │         ├── KnowledgeHub.search()  →  ChromaDB 检索
    │         ├── DecisionEngine.decide() → 铁闸检查
    │         └── LLM 推理（流式输出）
    │
    ├─── reviewer_dispatcher 节点（HUB-SPOKE 分发）
    │         └── Send() 并行/信息屏蔽顺序发送给各评审者
    │
    ├─── reviewer 节点 × N（各自独立，只看案件上下文）
    │         └── LLM 推理（流式输出）
    │
    ├─── consensus_builder 节点
    │         ├── 计算分歧度（向量相似度）
    │         └── 分歧 > 阈值 → requires_human = True
    │
    └─── [条件] human_review_gate（HITL 断点）或 END
    │
    ▼
[MemoryStore.record_run()] ── 记录方案 ID + 结果 + 分歧度
    │
    ▼
[OutputFormatter] ── Rich 终端流式输出 + Markdown 文件保存
    │
    ▼
[可选] 用户一键质量评分（1-5）

2.5 控制流设计（HUB-SPOKE）

text

LangGraph 原生 HUB-SPOKE 实现：

方案：high-quality（3 个 API 并行评审）
─────────────────────────────────────────────
primary_expert
    │
    ▼
reviewer_dispatcher
    │ Send() ×3（并行）
    ├──► reviewer_1（deepseek-pro，独立，不见其他评审）
    ├──► reviewer_2（deepseek-flash，独立）
    └──► reviewer_3（qwen-plus，独立）
              │（所有并行分支完成后汇聚）
              ▼
         consensus_builder
              │
    [divergence_score > 0.4?]
    ├── Yes → human_review_gate (HITL 中断点)
    └── No  → END

方案：all-local（信息屏蔽顺序模式）
─────────────────────────────────────────────
primary_expert（生成初步分析）
    │（只传 case_context 给评审者，不传 primary_analysis）
    ▼
reviewer_1（local-deepseek-r1，只看 case_context）
    │（结论写入 reviewer_opinions[0]，不传给 reviewer_2）
    ▼
reviewer_2（local-qwen35b，只看 case_context）
    │
    ▼
reviewer_3（local-coder，只看 case_context）
    │
    ▼
consensus_builder（整合所有独立意见 + primary_analysis）

关键：信息屏蔽由 LangGraph State 控制
reviewer 节点只从 State 中读取 case_context，
不读取 primary_analysis 和 reviewer_opinions

3. Project Factory Architecture
3.1 工厂能力定义

工厂的核心价值主张：任何新项目不从零开始，从已验证的模板 + 知识 + 经验开始。

text

项目孵化工厂能力矩阵：

                    debt-collection    project-B    project-C
                    ─────────────      ─────────    ─────────
工厂核心（共享）      ████████████       ████████     ████████
领域专家配置（复用）   ████░░░░░░░░       ██░░░░░░     ██░░░░░░
领域知识库（独有）     ████░░░░░░░░       ████░░░░     ████░░░░
业务数据层（独有）     ████████████       ████████     ████████
模型路由方案（独有）   ████████████       ████████     ████████
数据出境策略（独有）   ████████████       ████████     ████████

3.2 项目模板体系
标准项目骨架

text

projects/
└── _TEMPLATE/
    ├── CHARTER.md                  # 项目章程（目标/范围/约束）
    ├── pyproject.toml              # 依赖声明
    ├── config/
    │   ├── models.yaml             # ★ A 文件：本项目所有可用模型
    │   ├── routing_plans.yaml      # ★ B 文件：各节点模型调用方案
    │   └── privacy_policy.yaml     # ★ 数据出境策略文件
    ├── src/<project-name>/
    │   ├── cli.py                  # CLI 入口（含方案选择菜单）
    │   ├── models.py               # 业务数据模型（Pydantic + 敏感度标注）
    │   ├── domain/                 # 领域逻辑（项目专有）
    │   └── integrations.py         # 工厂能力接入点
    ├── experts/                    # 本项目专家定义（YAML + knowledge/）
    ├── tests/
    │   ├── test_domain.py
    │   └── test_integration.py
    └── docs/
        ├── DECISIONS.md
        └── RETRO/

forge CLI 命令体系

Bash

# 项目管理
forge new <project-name> --domain <domain>
    → 从 _TEMPLATE 复制骨架
    → 生成初始三配置文件（models/routing_plans/privacy_policy）
    → 初始化 Git 分支

forge stage <project> <phase>
    → 切换工作流阶段，触发阶段门控检查清单

forge retro <project>
    → 触发 RETRO 流程，自动收集数据
    → 引导经验提取，写入工厂知识库

forge status
    → 显示所有活跃项目的当前阶段状态

# 模型管理
forge switch-plan [--project <name>]
    → 交互式显示方案菜单，选择后修改 active_plan 字段

forge compare-plans [--project <name>] [--days 30]
    → 从 MemoryStore 读取历史数据，输出方案对比表

# 数据策略
forge privacy-audit [--project <name>]
    → 展示 privacy_policy.yaml 当前策略摘要
    → 显示各字段 30 天内触发频次，提示策略优化建议

# 知识管理
forge knowledge-update <expert-id>
    → 检测 knowledge/ 目录文件变化
    → 显示验证提醒，提供预置验证问题集

3.3 知识沉淀体系

text

_factory/knowledge/
├── universal/                      # 工厂通用知识（所有项目共享）
│   ├── patterns/
│   │   ├── hub-spoke-review.md     # HUB-SPOKE 评审模式说明
│   │   ├── layered-decision.md     # 分层决策模式说明
│   │   └── rag-pipeline.md         # RAG 管道最佳实践
│   ├── anti-patterns/
│   │   ├── langgraph-pitfalls.md   # LangGraph 已知陷阱
│   │   ├── sycophancy-risk.md      # 顺从性风险案例
│   │   └── *.md                    # 持续积累
│   └── lessons/
│       ├── 2026-06-debt-R1.md      # 项目复盘提取
│       └── *.md
│
├── experts/                        # 专家知识库（按专家 ID 索引）
│   ├── debt-lawyer/
│   │   ├── laws/
│   │   ├── cases/
│   │   └── VERSION                 # 知识库版本号（去重关键）
│   ├── compliance-auditor/         # 可跨项目复用
│   ├── risk-assessor/              # 可跨项目复用
│   └── execution-strategist/       # 可跨项目复用
│
└── skills/                         # 技能知识库
    ├── _SKILL_INDEX.md             # 技能索引
    ├── prescription-risk.skill.md
    ├── asset-search.skill.md
    ├── compliance-layered.skill.md
    └── *.skill.md                  # 持续积累

3.4 复用体系

text

复用流程（项目 B 如何受益于项目 A 的经验）：

项目 A RETRO 产出
    ├── forge retro 执行
    │       ├── 可复用模式 → _factory/patterns/
    │       ├── 失败模式 → _factory/anti-patterns/
    │       ├── 领域知识更新 → experts/
    │       └── 新技能 → skills/
    └── 自动同步到工厂知识库

项目 B 启动
    ├── forge new project-b（自动继承 L1 + L3 知识）
    ├── DISCOVERY：RAG 检索历史经验，主动提示"项目 A 踩过这个坑"
    ├── SPEC：引用已有专家（compliance-auditor 跨项目复用）
    └── 三配置文件自动生成初始版本

3.5 经验反馈体系
RETRO 标准化流程（轻量版，< 20 分钟）

text

Step 1：自动收集数据（AI 执行，2 分钟）
    → 本轮 API 调用次数/成本汇总
    → 各方案平均质量评分（来自 MemoryStore）
    → DecisionEngine 铁闸触发记录
    → 测试通过率变化

Step 2：人工复盘（核心，15 分钟）
    → 回答 5 个标准化问题（AI 预填数字部分，人工填判断部分）
    → 标记"下次不要再犯"的错误
    → 标记"值得复用"的模式

Step 3：知识入库（AI 辅助 + 人工审核，3 分钟）
    → AI 辅助提取经验文本
    → 人工审核后写入工厂知识库
    → 更新 expert knowledge/ + VERSION 文件

模型方案效果记录（新增）

text

RETRO 阶段额外收集（来自 MemoryStore 自动提取）：
├── 本轮使用的方案列表（plan_id）
├── 各方案的平均质量评分（用户事后标注）
├── 各方案的平均耗时和成本
├── 相同输入下不同方案的分歧度对比
└── 推荐：下一轮应优先使用的方案

3.6 标准化体系（阶段门控）

text

进入 BUILD 阶段的门控：
✅ CHARTER.md 已填写且经人工审核
✅ config/models.yaml 至少定义 1 个本地模型
✅ config/routing_plans.yaml 至少有 1 个 all-local 方案
✅ config/privacy_policy.yaml 已定义出境策略且经人工确认
✅ expert.yaml 通过 Pydantic Schema 验证（RoutingPlanEngine 启动验证）
✅ tests/test_domain.py 存在且有基础测试用例

进入 HARDEN 阶段的门控：
✅ 核心功能 CLI 命令全部可运行
✅ 测试有实质覆盖（能捕获真实 Bug 的用例）
✅ ChromaDB 索引已构建且版本检查通过

进入 RETRO 阶段的门控：
✅ 核心用户场景 E2E 可运行
✅ 所有已知 P0 Bug 已修复
✅ 文档已更新（HANDOFF.md 反映最新状态）

4. AI Workflow Architecture
4.1 工作流总图

text

五阶段 × AI 参与度矩阵：

阶段        人工占比   AI占比   境外模型       本地/中国API     输出物
──────────────────────────────────────────────────────────────────────
DISCOVERY    60%       40%      可用（网页）    辅助研究         市场/技术调研报告
SPEC         40%       60%      可用（网页）    需求分析         CHARTER.md + ADR
BUILD        20%       80%      可参与          代码生成         可运行代码 + 测试
HARDEN       10%       90%      可参与          测试/安全        Bug 修复 + 性能报告
RETRO        70%       30%      可用（网页）    数据整理         经验文档 + 知识库更新

4.2 DISCOVERY 阶段工作流

text

触发：forge stage <project> discovery

自动化部分（AI 执行）：
1. RoutingPlanEngine 加载当前激活方案
2. local-fast 模型：分析 CHARTER 草稿，生成 10 个关键研究问题
3. KnowledgeHub RAG：检索工厂知识库中相关历史项目经验
4. 主力模型：基于历史经验生成结构化调研报告（标准化 Markdown）

人工执行部分：
5. [可选] 将报告粘贴到 Claude.ai / ChatGPT 获取补充视角
6. 人工填写市场信息、竞品数据（AI 无法自动获取）
7. 人工审核结论，确认 CHARTER 初稿

输出：
→ docs/research/<date>-discovery.md
→ 如 privacy_policy.yaml 未配置：引导填写向导

4.3 SPEC 阶段工作流

text

触发：forge stage <project> spec

自动化部分：
1. 基于 DISCOVERY 产出，AI 生成初版 CHARTER.md
2. DecisionEngine 检查需求的合规风险（铁闸层）
3. 专家 Agent HUB-SPOKE 评审（2-3 个专家独立评审，评审技术方案）
4. 生成架构决策备选方案

人工执行部分：
5. [必须] 人工审核 DecisionEngine 的合规检查结论
6. [必须] 确认 CHARTER.md 内容
7. [可选] 粘贴到 Claude/ChatGPT 获取架构决策"第二意见"

输出：
→ 已签批的 CHARTER.md
→ docs/DECISIONS.md 初始版（含本阶段 ADR）
→ 三配置文件初始版（models.yaml / routing_plans.yaml / privacy_policy.yaml）

4.4 BUILD 阶段工作流

text

触发：forge stage <project> build

自动化部分（高 AI 占比）：
1. RoutingPlanEngine 根据 B 文件自动选择各节点模型
2. 代码生成：local-coder（Qwen2.5-Coder 32B）主力
3. 代码推理/审查：local-deepseek-r1 辅助
4. 测试生成：基于函数签名自动生成测试用例骨架
5. 合规检查：DecisionEngine 检查生成代码的安全边界
6. DataPrivacyGate：检查代码中的数据处理逻辑

人工执行部分：
7. [必须] 审查 DecisionEngine 标记的高风险代码段
8. [必须] 运行 pytest 并确认测试通过
9. [必须] 验证核心业务逻辑的正确性

禁止：
× 跳过人工代码审查直接部署
× 让 AI 决定铁闸规则内容

4.5 HARDEN 阶段工作流

text

触发：forge stage <project> harden

自动化部分：
1. pytest 自动运行，生成覆盖率报告
2. DataPrivacyGate 扫描代码，识别潜在数据出境点
3. 性能基准测试（本地推理速度、RAG 检索延迟）
4. ChromaDB 索引完整性验证（版本一致性检查）
5. 路由配置一致性验证（RoutingPlanEngine.validate_consistency()）

人工执行部分：
6. 审查隐私扫描报告，确认无未声明的数据出境路径
7. 决定哪些 Bug 是 P0（必须修复才能进入 RETRO）
8. 运行方案菜单中所有方案至少一次，验证均可正常工作

4.6 RETRO 阶段工作流

text

触发：forge retro <project>

自动化部分（AI 预填）：
1. 从 MemoryStore 提取：本轮 API 成本、各方案质量评分、耗时对比
2. 从 DecisionEngine 日志提取：铁闸触发记录摘要
3. 从 pytest 历史提取：测试通过率变化
4. 生成复盘报告草稿（数字部分已填好）
5. [可选] 生成标准化文档供粘贴到 Claude.ai 获取"还有哪些遗漏教训"

人工执行部分（核心，< 20 分钟）：
6. 填写 5 个标准化复盘问题（判断部分）
7. 标记"下次不要再犯"的错误
8. 标记"值得复用"的模式
9. 审核 AI 辅助提取的经验文本

知识入库（自动 + 人工审核）：
10. 经人工审核的经验写入 _factory/knowledge/
11. 更新专家 knowledge/ + VERSION 文件
12. 记录本次 RETRO 时间到项目状态文档

4.7 Research 工作流（DISCOVERY 子流程）

Python

def research_workflow(topic: str, project: str) -> ResearchReport:
    # Step 1: 本地 RAG 检索历史经验（KnowledgeHub）
    historical = knowledge_hub.search(topic, expert_id="factory-universal")

    # Step 2: 快速模型生成研究框架（local-fast）
    framework = llm_call(
        model=routing_engine.get_model_for_node("fast_classify"),
        prompt=f"为研究主题"{topic}"生成 10 个关键问题"
    )

    # Step 3: 主力模型深度分析（按 B 文件路由）
    analysis = llm_call(
        model=routing_engine.get_model_for_node("primary_expert"),
        prompt=f"历史经验：{historical}\n研究框架：{framework}\n深度分析主题：{topic}"
    )

    # Step 4: 生成标准化文档（供人工粘贴到境外模型，< 30000 tokens）
    return ResearchReport(
        analysis=analysis,
        hitl_prompt=generate_hitl_prompt(topic, analysis),
        save_path=f"projects/{project}/docs/research/{date}-{topic}.md"
    )

5. Model Routing Architecture
5.1 核心设计理念

模型管理体系的核心是双文件驱动 + LiteLLM 统一网关：

    A 文件（models.yaml）：定义所有可用模型的接入信息，一次配置，全局可用。
    B 文件（routing_plans.yaml）：定义每个工作节点的模型调用方案，切换方案只改 active_plan 一个字段。
    LiteLLM Gateway：统一路由层，所有调用（Claude Code、CLI、Agent）共用同一个网关，代码中永远不出现 base_url 或 API key。

5.2 A 文件：模型注册表（models.yaml）

YAML

# config/models.yaml
# 所有可用模型的接入信息
# API Key 引用环境变量，不明文写在此文件中

models:
  # ── 本地模型（Ollama + MLX 后端）──────────────────────────────
  local-qwen35b:
    display_name: "Qwen3.5 35B MoE（本地主力）"
    provider: ollama
    model_id: qwen3.5:35b-a3b-q8_0
    base_url: http://localhost:11434
    type: local
    estimated_speed: "~50 tok/s (MLX)"
    memory_required_gb: 22
    capabilities: [general, reasoning, chinese]

  local-deepseek-r1:
    display_name: "DeepSeek-R1 32B（本地推理）"
    provider: ollama
    model_id: deepseek-r1:32b
    base_url: http://localhost:11434
    type: local
    estimated_speed: "~40 tok/s"
    memory_required_gb: 20
    capabilities: [deep_reasoning, strategy]

  local-coder:
    display_name: "Qwen2.5-Coder 32B（本地代码）"
    provider: ollama
    model_id: qwen2.5-coder:32b
    base_url: http://localhost:11434
    type: local
    estimated_speed: "~40 tok/s"
    memory_required_gb: 20
    capabilities: [code_generation, code_review]

  local-70b:
    display_name: "Llama3.3 70B Q4（本地顶配）"
    provider: ollama
    model_id: llama3.3:70b-q4_K_M
    base_url: http://localhost:11434
    type: local
    estimated_speed: "~20 tok/s"
    memory_required_gb: 48
    capabilities: [general, high_quality]
    note: "需手动触发加载，启动慢约 60 秒"

  local-fast:
    display_name: "Qwen2.5 7B（本地快速）"
    provider: ollama
    model_id: qwen2.5:7b
    base_url: http://localhost:11434
    type: local
    estimated_speed: "~120 tok/s"
    memory_required_gb: 6
    capabilities: [classify, summarize, route]

  embedding:
    display_name: "bge-m3（向量嵌入）"
    provider: ollama
    model_id: bge-m3
    base_url: http://localhost:11434
    type: embedding

  # ── 中国商业 API ─────────────────────────────────────────────
  deepseek-flash:
    display_name: "DeepSeek V4 Flash（API 快速）"
    provider: deepseek
    model_id: deepseek-chat
    base_url: https://api.deepseek.com/v1
    api_key: ${DEEPSEEK_API_KEY}
    type: api
    estimated_cost: "$0.002/1k tokens"
    capabilities: [general, reasoning, fast]
    data_policy: requires_privacy_check

  deepseek-pro:
    display_name: "DeepSeek V4 Pro（API 高质量）"
    provider: deepseek
    model_id: deepseek-reasoner
    base_url: https://api.deepseek.com/v1
    api_key: ${DEEPSEEK_API_KEY}
    type: api
    estimated_cost: "$0.015/1k tokens"
    capabilities: [deep_reasoning, high_quality]
    data_policy: requires_privacy_check

  qwen-plus:
    display_name: "Qwen 3.6 Plus（API 超长上下文）"
    provider: alibaba
    model_id: qwen-plus
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key: ${QWEN_API_KEY}
    type: api
    estimated_cost: "$0.005/1k tokens"
    capabilities: [long_context, chinese]
    data_policy: requires_privacy_check

  glm-5:
    display_name: "GLM-5.1（API 中文专项）"
    provider: zhipu
    model_id: glm-4-plus
    base_url: https://open.bigmodel.cn/api/paas/v4
    api_key: ${GLM_API_KEY}
    type: api
    estimated_cost: "$0.007/1k tokens"
    capabilities: [chinese, legal]
    data_policy: requires_privacy_check

5.3 B 文件：路由方案表（routing_plans.yaml）

YAML

# config/routing_plans.yaml
# 各节点模型调用方案
# 切换方案只改 active_plan 这一个字段

active_plan: default              # ← 切换方案只改这里

plans:
  # ── 默认方案：本地为主，外源 API 增强评审质量 ─────────────────
  default:
    description: "本地模型为主，DeepSeek Flash 增强评审质量"
    estimated_total_time: "约 12-18 分钟"
    estimated_cost: "$0.01-0.03/次"
    nodes:
      primary_expert:
        model: local-qwen35b
        note: "主分析，本地主力"
      reviewer_1:
        model: deepseek-flash
        role: "风险评估"
        execution: sequential
        note: "外源 API 独立评审，不受本地模型偏见影响"
      reviewer_2:
        model: local-deepseek-r1
        role: "合规审查"
        execution: sequential
        note: "本地推理模型，深度分析"
      reviewer_3:
        model: local-qwen35b
        role: "执行策略"
        execution: sequential
        note: "本地主力，独立视角"
      consensus:
        model: deepseek-flash
        note: "外源模型汇总，客观性更好"
      fast_classify:
        model: local-fast

  # ── 高质量方案：多外源 API 并行，最高评审质量，顺从性最低 ──────
  high-quality:
    description: "多外源 API 独立并行评审，最高质量，顺从性最低"
    estimated_total_time: "约 8-12 分钟（API 并行执行）"
    estimated_cost: "$0.05-0.15/次"
    notes: "3 个独立 API 模型评审，偏见多样性最高"
    nodes:
      primary_expert:
        model: local-qwen35b
      reviewer_1:
        model: deepseek-pro
        role: "深度推理评审"
        execution: parallel     # ← LangGraph Send() 并行
      reviewer_2:
        model: deepseek-flash
        role: "快速风险评审"
        execution: parallel
      reviewer_3:
        model: qwen-plus
        role: "中文法律专项"
        execution: parallel
      consensus:
        model: deepseek-pro
        note: "高质量模型做最终决断"
      fast_classify:
        model: local-fast

  # ── 全本地方案：零成本，数据完全不出本地 ──────────────────────
  all-local:
    description: "全部本地模型，零 API 成本，数据完全不出本地"
    estimated_total_time: "约 18-25 分钟"
    estimated_cost: "$0"
    notes: "信息屏蔽顺序模式，评审者只看案件上下文"
    nodes:
      primary_expert:
        model: local-qwen35b
      reviewer_1:
        model: local-deepseek-r1
        role: "风险评估"
        execution: sequential_isolated  # ← 信息屏蔽顺序
      reviewer_2:
        model: local-qwen35b
        role: "合规审查"
        execution: sequential_isolated
      reviewer_3:
        model: local-coder
        role: "技术可行性"
        execution: sequential_isolated
      consensus:
        model: local-deepseek-r1
      fast_classify:
        model: local-fast

  # ── 快速方案：单评审，最快速度，适合低风险场景 ─────────────────
  fast:
    description: "单评审+汇总，最快完成，适合低风险初步判断"
    estimated_total_time: "约 5-8 分钟"
    estimated_cost: "$0.005/次"
    nodes:
      primary_expert:
        model: local-qwen35b
      reviewer_1:
        model: deepseek-flash
        role: "综合评审"
        execution: sequential
        note: "单一评审，速度快但多角度覆盖不足"
      consensus:
        model: local-qwen35b
      fast_classify:
        model: local-fast

  # ── 手动方案：快速自定义模板 ─────────────────────────────────
  # 使用方法：复制此方案，修改 model 字段名，设 enabled: true
  # 然后修改 active_plan 为此方案 ID 即可生效
  manual-override:
    description: "手动配置方案（修改此方案的模型名即可）"
    estimated_total_time: "根据配置模型而定"
    estimated_cost: "根据配置模型而定"
    enabled: false              # ← 改为 true 才能被选中
    nodes:
      primary_expert:
        model: local-qwen35b   # ← 在此修改模型名
      reviewer_1:
        model: local-qwen35b   # ← 在此修改
        role: "初步评审"
        execution: sequential_isolated
      reviewer_2:
        model: local-deepseek-r1  # ← 在此修改
        role: "批判性审查"
        execution: sequential_isolated
      reviewer_3:
        model: deepseek-flash  # ← 在此修改（外源汇总）
        role: "综合决断"
        execution: sequential_isolated
      consensus:
        model: deepseek-flash  # ← 在此修改
      fast_classify:
        model: local-fast

5.4 多评审方案菜单（CLI 交互）

text

$ debt review --case-id 001

┌────────────────────────────────────────────────────────────────────┐
│                    FORGE 评审方案选择                               │
├──┬──────────────────┬────────────────┬──────────┬─────────────────┤
│  │ 方案             │ 评审模式        │ 时间      │ 成本            │
├──┼──────────────────┼────────────────┼──────────┼─────────────────┤
│1 │ default ★        │ 混合（1API+2本地）│ ~15min   │ ~$0.02         │
│  │ 当前激活         │ 信息屏蔽顺序    │          │                 │
├──┼──────────────────┼────────────────┼──────────┼─────────────────┤
│2 │ high-quality     │ 3 API 并行      │ ~10min   │ ~$0.10          │
│  │                  │ 顺从性最低      │ 预估内存43GB │              │
├──┼──────────────────┼────────────────┼──────────┼─────────────────┤
│3 │ all-local        │ 本地信息屏蔽    │ ~22min   │ $0              │
│  │                  │ 数据不出境      │ 预估内存50GB │              │
├──┼──────────────────┼────────────────┼──────────┼─────────────────┤
│4 │ fast             │ 单评审          │ ~6min    │ ~$0.01          │
│  │                  │ 低风险适用      │          │                 │
├──┼──────────────────┼────────────────┼──────────┼─────────────────┤
│5 │ manual-override  │ 自定义          │ 见B文件   │ 见B文件         │
│  │ (需先编辑B文件)  │                │          │                 │
└──┴──────────────────┴────────────────┴──────────┴─────────────────┘

直接回车使用激活方案 (default)，输入数字切换：
> _

5.5 本地模型职责矩阵
模型 ID	规格	核心职责	路由条件
local-qwen35b	~20GB MoE	执行核心 — Agent 主力，通用推理，中文处理	中等复杂度任务，默认选择
local-deepseek-r1	~20GB	推理核心 — 复杂策略分析，长链推理	策略生成，复杂法律分析
local-coder	~20GB	代码核心 — 专注代码生成与审查	BUILD 阶段代码任务
local-70b	~48GB	质量顶配 — 最高质量，加载慢	按需手动触发（A 文件有 note 提示）
local-fast	~6GB	快速分类 — 路由判断，简单摘要	所有 fast_classify 节点
embedding	~3GB	向量嵌入 — 所有 RAG 检索	所有 ChromaDB 操作
5.6 中国商业 API 职责矩阵
模型 ID	核心职责	适用场景	月度预算目标
deepseek-flash	日常增强 — 高质量快速响应	DISCOVERY 调研、SPEC 需求分析、默认方案评审	< $10/月
deepseek-pro	高质量增强 — 接近 Claude Sonnet 水平	重要报告生成、high-quality 方案汇总	< $20/月
qwen-plus	超长上下文 — 1M Token	整个知识库分析、大型代码库审查	按需
glm-5	中文专项 — 中文法律文档	中文法规理解、法律本地化内容	< $5/月

所有中国 API 调用前：必须通过 DataPrivacyGate 策略检查，无法跳过。
5.7 人工调用 ChatGPT 职责（明确定义的 HITL 节点）

text

HITL-GPT-01: DISCOVERY 阶段竞品研究补充
    触发：AI 调研报告生成后，人工主动发起
    操作：将报告粘贴到 ChatGPT，获取"还有哪些遗漏的竞品/风险"
    时间：< 15 分钟
    输出：保存到 docs/research/gpt-supplement-<date>.md

HITL-GPT-02: BUILD 阶段边界案例识别
    触发：核心功能完成后
    操作：将脱敏功能描述 + 测试用例粘贴，获取"未覆盖的边界案例"
    时间：< 10 分钟
    输出：追加到 tests/edge-cases.md

HITL-GPT-03: HARDEN 阶段安全盲区检查
    触发：代码完成前
    操作：将脱敏代码框架粘贴，获取安全检查意见
    时间：< 20 分钟
    输出：保存到 docs/security-review-<date>.md

5.8 人工调用 Claude 职责（明确定义的 HITL 节点）

text

HITL-CLAUDE-01: 月度架构复审（每月一次）
    触发：每月第一个工作日
    操作：将当月 DECISIONS.md 变更 + 新增技术债粘贴
    目标：架构健康度诊断和改进建议
    时间：< 30 分钟
    输出：更新 docs/ARCHITECTURE_REVIEW.md

HITL-CLAUDE-02: RETRO 阶段经验萃取（每个里程碑后）
    触发：forge retro 流程末尾，可选执行
    操作：将复盘草稿粘贴，获取"还有哪些系统性教训"
    时间：< 20 分钟
    输出：补充到 RETRO 文档，更新工厂知识库

HITL-CLAUDE-03: 重大架构决策前（按需）
    触发：需要做 D 级（架构层）决策时
    操作：将决策背景 + 备选方案粘贴，获取权衡分析
    时间：< 30 分钟
    输出：保存为 docs/decisions/D-XXX-claude-review.md

5.9 职责隔离规则

text

R-01: 数据出境遵守 privacy_policy.yaml 策略（不是代码硬编码）
R-02: 高频小任务（分类/路由）→ local-fast，不消耗大模型
R-03: 中国 API 调用前必须通过 DataPrivacyGate
R-04: ChatGPT → 不用于 Claude 职责，反之亦然
R-05: Claude/ChatGPT → 永远不参与自动化流程，只参与文档交换
R-06: local-70b → 按需手动触发，不设为默认方案
R-07: 方案切换 → 只改 routing_plans.yaml 中 active_plan 字段
R-08: 新增模型 → 先在 models.yaml 定义，再在方案中引用

6. Knowledge Architecture
6.1 项目 A 如何让项目 B 立即受益？

三个机制的组合：

text

机制 1：共享专家池（立即可用）
    debt-collection 的 compliance-auditor 专家
    → 包含法律合规知识库（已构建 ChromaDB 索引）
    → project-B 的 routing_plans.yaml 直接引用该专家 ID
    → 无需重新注入知识，VERSION 检查确保索引有效

机制 2：教训知识库（RETRO 驱动）
    debt-collection RETRO 后
    → 经验文档进入 _factory/knowledge/lessons/
    → project-B DISCOVERY 时，KnowledgeHub 自动检索
    → 主动提示："project debt-collection 踩过类似坑：..."

机制 3：技能复用（SKILL.md 接入 KnowledgeHub 后）
    debt-collection 产生的 compliance-layered.skill.md
    → 进入 _factory/skills/
    → project-B 的 expert.yaml 声明 requires_skills
    → KnowledgeHub.inject_skill() 自动加载

6.2 知识体系完整架构

text

_factory/knowledge/
├── universal/                          # 工厂通用知识（所有项目共享）
│   ├── patterns/
│   │   ├── hub-spoke-review.md
│   │   ├── layered-decision.md
│   │   ├── rag-pipeline.md
│   │   └── dual-file-model-mgmt.md    # 双文件模型管理最佳实践
│   ├── anti-patterns/
│   │   ├── langgraph-pitfalls.md
│   │   ├── sycophancy-risk.md
│   │   ├── schemaless-config.md
│   │   └── *.md
│   └── lessons/
│       └── *.md                        # RETRO 后持续积累
│
├── experts/                            # 专家知识库
│   ├── debt-lawyer/
│   │   ├── laws/
│   │   ├── cases/
│   │   └── VERSION                     # v1.2 → ChromaDB 检查版本一致性
│   ├── compliance-auditor/             # 跨项目复用
│   ├── risk-assessor/                  # 跨项目复用
│   └── execution-strategist/           # 跨项目复用
│
└── skills/
    ├── _SKILL_INDEX.md                 # 技能索引（forge 可查询）
    ├── prescription-risk.skill.md
    ├── asset-search.skill.md
    ├── compliance-layered.skill.md
    └── *.skill.md

6.3 数据出境策略文件（privacy_policy.yaml）

设计理念：策略由你来定，DataPrivacyGate 只是执行者。

YAML

# config/privacy_policy.yaml
# 数据出境策略：项目负责人定义，DataPrivacyGate 执行
# ─────────────────────────────────────────────────────
# 设计原则：
# 1. 政策类型只有 4 种：local_only / human_approve / mask_then_allow / allow
# 2. 未定义字段默认 human_approve（最保守）
# 3. 每季度执行 forge privacy-audit 检查策略是否仍然适用
# 4. 此文件只能人工修改，AI 无权修改

version: "1.0"
project: "debt-collection"
last_reviewed: "2026-06-14"
reviewed_by: "项目负责人"

# ── 数据字段分级定义 ─────────────────────────────────────────────
fields:
  debtor_name:
    label: "债务人姓名"
    policy: local_only
    note: "真实姓名不出本地；如需分析时可在 prompt 中替换为代称"

  id_number:
    label: "身份证号"
    policy: human_approve        # 不是 local_only！特殊场景允许出境，但需人工确认
    mask_rule: "keep_first_6_last_4"
    note: "脱敏版（前6后4）经人工确认后可出境；如接入特定法律分析 API 可能需要原始值"

  phone_number:
    label: "联系电话"
    policy: human_approve
    mask_rule: "keep_first_3_last_4"
    note: "同身份证号处理原则"

  amount:
    label: "债务金额（精确）"
    policy: mask_then_allow
    mask_rule: "round_to_nearest_10000"
    note: "精确金额不出境，四舍五入到万元后自动允许出境"

  case_evidence:
    label: "案件证据材料"
    policy: local_only
    note: "证据内容仅本地处理，含证据的摘要经脱敏后可 human_approve"

  legal_strategy:
    label: "法律策略建议"
    policy: mask_then_allow
    mask_rule: "remove_personal_identifiers"
    note: "去除个人标识符后的策略框架可出境"

  compliance_analysis:
    label: "合规分析结果"
    policy: allow
    note: "通用合规结论，无个人信息，直接可出境"

  general_legal_knowledge:
    label: "通用法律知识问答"
    policy: allow
    note: "完全通用内容，无任何个人信息"

  debtor_region:
    label: "债务人所在省份"
    policy: allow
    note: "省级地域信息，无法识别个人"

# ── 目标端点策略 ─────────────────────────────────────────────────
endpoints:
  chinese_api:
    display_name: "中国商业 API（DeepSeek/Qwen/GLM）"
    allowed_policies: [allow, mask_then_allow]
    requires_human_for: [human_approve]
    data_residency: "中国境内服务器"

  overseas_web_manual:
    display_name: "境外网页手动（ChatGPT/Claude，人工粘贴）"
    allowed_policies: [allow, mask_then_allow, human_approve]
    requires_human_for: [human_approve]
    note: "人工操作，用户自行判断粘贴内容"

  local_model:
    display_name: "本地 Ollama 模型"
    allowed_policies: [allow, mask_then_allow, human_approve, local_only]
    note: "数据不离本机，任何数据均可"

# ── 人工审核触发规则 ─────────────────────────────────────────────
human_approval_triggers:
  - condition: "policy == human_approve AND target != local_model"
    message: "字段 {field_label} 将发送到 {endpoint_name}，请确认"
    action: "显示数据预览，要求显式输入 yes"

  - condition: "首次使用新的 API 端点"
    message: "首次调用 {endpoint_name}，请确认数据政策"
    action: "显示策略摘要，记录同意时间戳到审计日志"

  - condition: "批量出境 > 100 条记录"
    message: "批量出境 {count} 条记录"
    action: "显示字段摘要，要求显式确认"

# ── 脱敏管道配置 ─────────────────────────────────────────────────
masking_pipeline:
  steps:
    - remove_personal_identifiers   # 去除姓名、证件号、联系方式
    - round_amounts                 # 金额模糊化到万元
    - keep_first_6_last_4           # 身份证脱敏（如策略允许出境）
    - keep_first_3_last_4           # 电话脱敏
  verify_before_send: true          # 脱敏后二次验证，确认无原始数据残留

6.4 知识版本控制

text

VERSION 文件机制：
_factory/experts/<expert-id>/VERSION  内容示例：v1.3-20260614

ChromaDB collection metadata：
{
  "version": "v1.3-20260614",
  "built_at": "2026-06-14T10:30:00"
}

KnowledgeHub._is_index_current() 比对两者：
  一致 → 跳过重建，直接加载（冷启动快）
  不一致 → 重建索引，更新 metadata

知识库更新流程：
1. 人工修改 knowledge/ 目录下的文档
2. 人工更新 VERSION 文件（如 v1.3 → v1.4）
3. 下次运行时 KnowledgeHub 自动检测版本变化，重建索引
4. forge knowledge-update <expert-id> 命令提示验证

6.5 跨项目知识流动

text

知识流向图：

项目执行
    │ RETRO 触发（forge retro <project>）
    ├──► 可复用模式 ──────────────────► _factory/patterns/
    ├──► 失败模式 ────────────────────► _factory/anti-patterns/
    ├──► 领域知识更新 ─────────────────► experts/<id>/knowledge/ + VERSION++
    └──► 新技能文件 ──────────────────► _factory/skills/

新项目启动（forge new project-b）
    ├── 自动继承 _factory/knowledge/universal/ 的全部知识
    ├── DISCOVERY：RAG 主动检索并提示相关历史教训
    ├── SPEC：可直接引用已有专家（compliance-auditor 等）
    └── BUILD：可引用已有技能（compliance-layered 等）

6.6 知识质量保证

text

质量红线：
× 禁止 AI 直接写入知识库（所有写入必须经人工审核）
× 禁止未更新 VERSION 文件的知识库热更新
× 禁止 AI 修改 privacy_policy.yaml
× 每次修改 privacy_policy.yaml 必须在 DECISIONS.md 中记录理由

质量监控（forge privacy-audit 触发）：
→ 30 天内从未触发 DataPrivacyGate 的字段：提示"此字段是否仍需要此策略？"
→ 30 天内触发 > 50 次确认门的字段：提示"此字段是否可以放宽为 mask_then_allow？"

7. Toolchain Architecture
7.1 工具链设计原则

text

核心原则：以"流畅好用"为目标，不追求最少工具数
- 每个工具解决一个明确问题
- 每个工具独立可替换
- 独立开发者在合理时间内可掌握每个工具
- 所有工具共享同一个模型网关（LiteLLM），配置一次全局可用

7.2 IDE 层
工具	用途	配置说明
VS Code	主要代码编辑器	标准配置
Claude Code for VS Code	AI 辅助代码编辑、重构、审查	通过 LiteLLM 网关路由到本地/外源模型
LiteLLM Gateway	统一模型接入层，A 文件驱动，localhost:4000	Claude Code、CLI、Agent 共用

Claude Code + LiteLLM 集成配置：

YAML

# _infra/litellm-config.yaml
# 此文件是 A 文件（models.yaml）的 LiteLLM 执行层
# models.yaml 是人可读的配置，此文件是 LiteLLM 格式

model_list:
  - model_name: "local/qwen35b"
    litellm_params:
      model: "ollama/qwen3.5:35b-a3b-q8_0"
      api_base: "http://localhost:11434"

  - model_name: "local/deepseek-r1"
    litellm_params:
      model: "ollama/deepseek-r1:32b"
      api_base: "http://localhost:11434"

  - model_name: "local/coder"
    litellm_params:
      model: "ollama/qwen2.5-coder:32b"
      api_base: "http://localhost:11434"

  - model_name: "local/fast"
    litellm_params:
      model: "ollama/qwen2.5:7b"
      api_base: "http://localhost:11434"

  - model_name: "api/deepseek-flash"
    litellm_params:
      model: "deepseek/deepseek-chat"
      api_key: "os.environ/DEEPSEEK_API_KEY"

  - model_name: "api/deepseek-pro"
    litellm_params:
      model: "deepseek/deepseek-reasoner"
      api_key: "os.environ/DEEPSEEK_API_KEY"

  - model_name: "api/qwen-plus"
    litellm_params:
      model: "openai/qwen-plus"
      api_base: "https://dashscope.aliyuncs.com/compatible-mode/v1"
      api_key: "os.environ/QWEN_API_KEY"

  - model_name: "api/glm-5"
    litellm_params:
      model: "openai/glm-4-plus"
      api_base: "https://open.bigmodel.cn/api/paas/v4"
      api_key: "os.environ/GLM_API_KEY"

Claude Code 日常使用规范：

text

开发工厂框架代码（无业务数据）：
    → Claude Code 可使用 api/deepseek-pro（高质量）

开发/修改含业务数据的文件：
    → Claude Code 切换到 local/qwen35b（数据不离本机）

处理 privacy_policy.yaml：
    → 不使用 AI 辅助，纯人工编辑

启动流程：
    1. make start-gateway     → 启动 LiteLLM（localhost:4000）
    2. VS Code 打开项目
    3. Claude Code 配置：API Base = http://localhost:4000
    4. 按需在 Claude Code 中选择模型

7.3 Agent/AI 框架层
工具	用途	版本	风险
LangGraph	Agent 图编排，HUB-SPOKE 实现，检查点持久化	≥ 1.0.10（修复 SQLi 漏洞）	🟢 低（API 稳定承诺）
langgraph-checkpoint-sqlite	LangGraph 状态持久化	≥ 3.0.1（修复安全漏洞）	🟢 低
LlamaIndex	文档加载 + RAG 管道	≥ 0.12.x（锁定）	🟡 中

安全说明：
1
应使用 langgraph-checkpoint-sqlite 3.0.1+ 和 langgraph 1.0.10+，以避免 SQLite checkpointer 中已修补的安全漏洞。
7.4 CLI 层
工具	用途	状态
debt CLI（cli.py）	debt-collection 项目入口，含方案选择菜单	✅ 已有，需迁移到 LangGraph
forge CLI	工厂管理命令（new/stage/retro/status/switch-plan/compare-plans/privacy-audit）	🚧 部分已有，待补全
uv	Python 包管理 + 虚拟环境	✅ 已有
7.5 向量库层
工具	用途	说明
ChromaDB	本地向量存储	修复去重后生产可用，VERSION 机制保障一致性
bge-m3（Ollama）	Embedding 模型	替换只需改 models.yaml 中 embedding 模型 ID
7.6 数据库层
工具	用途	说明
SQLite（业务库）	台账/情报/时效数据	极稳定，runtime/debt.db
SQLite（LangGraph SqliteSaver）	图执行状态检查点	原生内置，runtime/checkpoints.sqlite
SQLite（MemoryStore）	跨会话记忆 + ModelRunRecord	runtime/memory.db
ChromaDB	向量索引持久化	runtime/chroma_data/
7.7 文档系统层
文档	用途	格式
HANDOFF.md	项目交接（新 Agent 必读，含排障表）	Markdown
DECISIONS.md	ADR 决策日志（D-001 起）	Markdown + 标准模板
DEV_LOG.md	逐轮开发日志	Markdown
CHARTER.md	项目章程（每项目一份）	Markdown + 标准模板
RETRO/*.md	复盘记录（每里程碑一份）	Markdown + 标准模板
config/models.yaml	A 文件：模型注册表	YAML
config/routing_plans.yaml	B 文件：节点路由方案	YAML
config/privacy_policy.yaml	数据出境策略	YAML

文档工具规则： 所有文档 Markdown + Git，不依赖任何云端文档服务（Notion/Confluence 等）。
7.8 版本管理层
工具	用途	规范
Git	代码版本控制，替代 ZIP 补丁部署	main（稳定）+ dev（开发）+ hotfix/*（紧急）
Git tag	版本发布标记	v<major>.<minor>.<patch>-<project>
.gitignore	排除敏感文件	runtime/ 目录不入 Git
uv.lock	依赖版本锁定	确保环境完全可重现
7.9 自动化系统层

Makefile

# Makefile 完整命令集

# 日常开发
start-gateway:    # 启动 LiteLLM 网关
    @cd _infra && ./start-litellm.sh

start-ollama:     # 启动 Ollama（MLX 后端）
    @OLLAMA_USE_MLX=1 ollama serve

test:             # 运行全量测试
    @uv run pytest tests/ -v

test-unit:        # 只跑单元测试（快速）
    @uv run pytest tests/unit/ -v

# 项目管理
backup:           # 备份 runtime/ 目录 + git push
    @git push origin main
    @tar -czf backups/runtime-$(shell date +%Y%m%d-%H%M).tar.gz runtime/
    @echo "✅ 备份完成"

pre-upgrade-check: # macOS/依赖升级前检查
    @uv run pytest tests/ -v && echo "✅ 升级前测试通过，可以升级"

# 模型管理
switch-plan:      # 交互式切换路由方案
    @uv run forge switch-plan

compare-plans:    # 查看方案对比报告
    @uv run forge compare-plans --days 30

# 数据策略
privacy-audit:    # 审查当前数据出境策略
    @uv run forge privacy-audit

# 代码质量
lint:             # 代码检查
    @uv run ruff check src/

format:           # 代码格式化
    @uv run ruff format src/

自动化原则：

text

✅ 自动化：
- 每日 runtime/ 备份（cron: 0 2 * * * make backup）
- 提交前运行测试（pre-commit hook: make test-unit）
- 提交前检查代码风格（ruff check）

❌ 不引入：
- GitHub Actions / CI/CD（当前阶段过度设计）
- Docker / Compose（单机不需要）
- Terraform / Ansible（无服务器运维需求）

7.10 工具链完整依赖清单

toml

# pyproject.toml 核心依赖（以解决问题为准，不设硬性数量限制）

[project.dependencies]
# AI 框架
langgraph = ">=1.0.10"               # ← 最低版本（修复安全漏洞）
langgraph-checkpoint-sqlite = ">=3.0.1"  # ← 最低版本（修复安全漏洞）
llama-index-core = ">=0.12"
llama-index-vector-stores-chroma = ">=0.12"

# 模型与向量
chromadb = ">=0.6"
ollama = ">=0.4"
litellm = ">=1.40"                   # LiteLLM 客户端（调用网关）

# 数据与配置
pydantic = ">=2.10"
pyyaml = ">=6.0"
python-dotenv = ">=1.0"
sqlite-utils = ">=3.36"

# 界面与工具
rich = ">=13.9"
click = ">=8.0"
httpx = ">=0.27"

# 数值计算
numpy = ">=1.26"                     # 分歧度计算（向量相似度）

# 测试
pytest = ">=9.0"
pytest-asyncio = ">=0.23"           # LangGraph 异步测试

# 代码质量
ruff = ">=0.4"                       # Lint + Format（替代 flake8+black）

8. Complexity Budget
8.1 核心原则：以"流畅好用"为基准

复杂度预算的目标不是限制代码行数，而是确保系统对独立开发者来说始终是流畅好用的。

text

✅ 好的复杂度（必须存在，创造价值）：
   - 功能完整性所必需
   - 安全和合规所必需（DataPrivacyGate、铁闸规则）
   - 长期可维护性所必需（清晰的模块职责分离）
   - 用户体验流畅所必需（方案菜单、流式输出、GPU 预检）
   - 解决业务问题所必需的任何代码

❌ 坏的复杂度（必须消除，不创造价值）：
   - 一个文件承担多个不相关的职责
   - 手写已有成熟库解决的问题
   - 过度防御性代码掩盖真实错误
   - 提前为不确定需求设计的过度抽象
   - 为了"看起来专业"而加的无谓架构层
   - 定义了但从不被使用的功能和配置

8.2 触发重构的信号（代替死板数字上限）

代码层面： 不以行数为硬限制，以下信号出现时发起重构讨论：
信号	说明	处理方向
修改一个功能需要在同一文件搜索很久才找到	文件可能承担太多职责	按职责拆分，不按行数
新增一个功能需要同时改 3 处以上不相关地方	耦合过重	引入适当抽象
看一个函数需要追踪 5 层调用才能理解它做什么	嵌套过深	提取命名清晰的子函数
修改 expert.yaml 导致不相关测试失败	配置解析脆弱	加强 Pydantic Schema 校验
阅读某段代码 10 分钟仍不理解意图	逻辑不清晰	重写或加注释，不是"保留"
某个文件每次迭代都必须改	职责分配不对	重新分配职责

系统层面： 以下情况出现时评估是否需要架构调整：
信号	说明	评估方向
冷启动时间主观感受 > 30 秒	初始化逻辑堆积	懒加载、缓存、去重检查
内存不足导致 Ollama 无法加载目标模型	多模型并发超限	优化模型加载策略，利用 RoutingPlanEngine GPU 预检
某个外部 API 失效导致整个工作流卡住	单点依赖	添加降级路径到 all-local 方案
测试套件运行超过 3 分钟（单元测试）	测试混入了不必要的 IO	分离单元测试和集成测试
同时维护 3 个以上高强度项目	认知负荷接近极限	主动降低某个到维护模式

工具层面： 新增依赖的判断标准（不是"不能超过 N 个"）：

text

新增依赖前自问：
1. 这个依赖解决的问题，用现有工具手写需要多少时间？值得吗？
2. 这个依赖的维护状态如何（最近是否有更新，社区是否活跃）？
3. 这个依赖有无重大版本破坏性变更的历史？
4. 如果这个依赖未来停止维护，迁移成本多大？
5. 这个依赖会给独立开发者带来多大学习成本？

如果答案让你觉得"划算"，加。
如果不确定，在代码注释中说明为什么加，方便未来评估是否删除。
不需要 ADR 审批，不需要"数量配额"。

8.3 必须存在的复杂度（允许清单）

text

以下复杂度必须存在，不得以"简化"为由移除：

✅ LangGraph StateGraph 图结构定义
   → 工作流的清晰表达，替代了 500 行单文件编排器

✅ DataPrivacyGate 的策略解析和执行逻辑
   → 合规不可省略，但复杂度由策略文件承担，代码本身不复杂

✅ RoutingPlanEngine 的双文件解析和一致性校验
   → 模型管理的核心价值，换来"一行配置切换方案"

✅ DecisionEngine 的铁闸规则
   → 法律合规底线，不可 AI 化，不可省略

✅ KnowledgeHub 的版本检查机制
   → 避免脏索引积累，保障知识质量

✅ HUB-SPOKE 的信息屏蔽机制（LangGraph State 控制）
   → 解决顺从性问题的关键，不是过度设计

✅ MemoryStore 的 ModelRunRecord 记录
   → 模型方案选优的数据基础，工厂价值的重要体现

8.4 绝对禁止（无例外）

text

🚫 永远不做，不因为"够用"而例外：

FORBIDDEN-01: 手写已有成熟库解决的问题
    典型：手写 YAML 解析器（Pydantic 解决）

FORBIDDEN-02: 铁闸合规规则交由 AI 判断
    法律合规底线不可概率化，Python 代码保证确定性

FORBIDDEN-03: 敏感数据未经 privacy_policy.yaml 策略检查就调用外部 API
    DataPrivacyGate 必须执行，不可绕过

FORBIDDEN-04: 闭源模型（Claude/ChatGPT）API 自动调用
    技术不可行（仅支持网页手动），不要尝试绕过

FORBIDDEN-05: 防御性 try-except 覆盖核心业务逻辑
    掩盖错误，使调试时间数倍增加
    替代：启动时一次性检查所有依赖，运行时让错误明确暴露

FORBIDDEN-06: 框架版本升级与功能开发在同一分支
    混淆 Bug 来源，极难调试

FORBIDDEN-07: AI 修改 privacy_policy.yaml
    数据出境策略是人类决策

FORBIDDEN-08: 无版本检查地运行时重建向量索引
    冷启动性能随知识库增长线性恶化

FORBIDDEN-09: routing_plans.yaml 中引用 models.yaml 未定义的模型名
    由 RoutingPlanEngine.validate_consistency() 在启动时强制检测

FORBIDDEN-10: 在未通过全量测试前合并 LangGraph 迁移到主分支

8.5 复杂度债务信号监控

text

🔴 立即处理（优先于任何新功能）：
- 某个 Bug 无法复现（防御性代码掩盖了根因）
- DataPrivacyGate 策略被意外绕过
- RoutingPlanEngine.validate_consistency() 启动时报错
- LangGraph 检查点损坏（无法从断点恢复）

🟠 计划内处理（下次迭代开始时）：
- 某个文件已成为"不敢改"的遗产代码
- routing_plans.yaml 中超过 8 个方案且多数从不使用
- privacy_policy.yaml 中有字段 90 天内从未触发

🟡 追踪但不紧急：
- 某个依赖版本落后超过 6 个月
- 某个 SKILL.md 定义 6 个月未被使用
- DEV_LOG.md 中相同类型 Bug 出现 3 次以上

9. Migration Roadmap
Phase A：立即启动——两条并行线（第 1-2 周）

目标： 消除所有 P0 问题。分两条并行线推进，避免 LangGraph 迁移阻塞其他工作。
线 1：LangGraph 迁移（独立分支 langgraph-migration）
任务	说明	验收标准
安装 LangGraph ≥ 1.0.10 + checkpoint-sqlite ≥ 3.0.1	安全版本	uv add "langgraph>=1.0.10" 成功
定义 ReviewState（TypedDict）	显式状态，替代 Agno 的隐式状态	Pydantic 验证通过
迁移主专家节点 → LangGraph 节点函数	最小迁移单元	单节点测试通过
迁移评审节点 → HUB-SPOKE（信息屏蔽）	reviewer 节点只读 case_context	分歧检测测试通过
迁移汇总节点 + 分歧检测	ConsensusBuilder	高/低分歧场景测试通过
接入 SqliteSaver 检查点	runtime/checkpoints.sqlite	中断恢复测试通过
集成 HITL 断点	interrupt_before=["human_review_gate"]	HITL 触发和继续测试通过
全量测试通过	39 原有 cases + 20 新 LangGraph 测试	全部通过后合并
删除 Agno 全部代码	代码库干净	无 Agno 引用残留

风险控制： 迁移期间主分支 Agno 实现正常运行，两者并存直到验证通过。
线 2：双文件体系 + DataPrivacyGate（主分支，独立于迁移）
任务	文件	验收标准
建立 config/models.yaml（A 文件）	见 Section 5.2	所有模型条目通过 Pydantic 校验
建立 config/routing_plans.yaml（B 文件）	见 Section 5.3	RoutingPlanEngine.validate_consistency() 通过
实现 RoutingPlanEngine（含方案菜单 + GPU 预检）	platform/routing_plan_engine.py	forge switch-plan 可用
建立 config/privacy_policy.yaml	见 Section 6.3	人工确认后提交
实现 DataPrivacyGate（策略文件驱动）	platform/data_privacy_gate.py	敏感字段出境被阻断测试通过
迁移 YAML 解析到 Pydantic Schema	config/schemas.py	所有 expert.yaml 通过验证
修复 ChromaDB 去重 + VERSION 机制	platform/knowledge_hub.py	多次运行不重复构建索引
修复 PYTHONPATH → pyproject.toml editable	pyproject.toml	新环境 uv pip install -e . 即可
更新 LiteLLM 配置接入所有模型	_infra/litellm-config.yaml	Claude Code 可通过网关调用本地模型
启用 Ollama MLX 后端	Ollama 配置，30 秒完成	推理速度 benchmark 可测量提升

Phase A 完整退出标准：

    ✅ LangGraph 迁移：全量测试（≥ 59 cases）全部通过，debt review 在 LangGraph 上正常运行
    ✅ 方案菜单：debt review 启动时展示可选方案
    ✅ DataPrivacyGate：high 字段出境被硬性阻断，human_approve 字段触发确认提示
    ✅ RoutingPlanEngine：validate_consistency() 在配置错误时明确报错
    ✅ ChromaDB：多次运行不重复构建索引（VERSION 机制生效）
    ✅ Claude Code + LiteLLM：可在 VS Code 中通过网关调用本地模型
    ✅ Agno 代码完全删除

Phase B：激活沉睡功能（第 3-4 周）

目标： 把已有但断路的功能全部激活，验证 API 增强路径。
任务	说明	价值
HUB-SPOKE 并行完整实现（high-quality 方案）	LangGraph Send() 实现真正并行	顺从性最低的评审方案可用
MemoryStore + ModelRunRecord	评审结束后自动记录方案 ID + 结果	方案对比数据开始积累
forge compare-plans 命令	从 MemoryStore 读取，输出对比表	数据驱动模型选优
接入分层决策引擎到 LangGraph 节点	DecisionEngine 作为图节点调用	铁闸保护激活
SKILL.md 接入 KnowledgeHub	inject_skill() 实现	技能复用激活
SqliteMemoryDb 跨会话记忆激活	挂载到 LangGraph 状态持久化	跨会话上下文积累
DeepSeek V4 Flash API 接入 + 50 次真实测试	验证质量和延迟	验证 API 增强路径
流式输出启用	LangGraph stream_mode="updates"	实时打印，不等待完成
评审结束一键质量评分	[1-很有用 / 2-一般 / 3-没用 / 回车跳过]	质量对比数据有主观标注
标准化 HITL 文档交换格式	固化 Claude/ChatGPT 交互输入输出格式	规范化人工节点

Phase B 退出标准：

    ✅ high-quality 方案（3 API 并行）运行时间 < 12 分钟
    ✅ all-local 方案信息屏蔽有效（reviewer 节点确实只读 case_context）
    ✅ 分歧检测：高分歧场景正确触发 HITL 中断点
    ✅ ModelRunRecord 正确记录，forge compare-plans 显示对比数据
    ✅ DeepSeek V4 Flash 50 次测试：延迟 < 30s/次，成本记录准确

Phase C：工厂能力建设（第 5-8 周）

目标： 将单项目能力升级为工厂能力，启动 Project B 验证复用价值。
任务	说明	验收标准
forge new 命令完整实现	从 _TEMPLATE 生成骨架，含三配置文件初始版本	新项目从零到 CLI 可运行 < 30 分钟
forge stage 命令 + 阶段门控	切换阶段时触发门控检查清单	未满足条件时阻止切换并显示清单
forge retro 命令	自动收集数据，引导 5 个问题，写入工厂知识库	总流程 < 20 分钟
forge status 命令	显示所有项目当前阶段状态	多项目可视化
Makefile 完整工具集	make test/start-gateway/backup/compare-plans 等	常用操作单命令完成
Project B 启动	在新项目中复用 compliance-auditor 专家	复用专家比例 ≥ 40%
知识库工厂 ADR 模板	标准化决策记录格式	新 ADR 使用模板创建
pre-commit hook 配置	测试 + ruff check	提交前自动检查

Phase C 退出标准：

    ✅ forge new 创建项目 < 5 分钟（含三配置文件初始化）
    ✅ Project B DISCOVERY 阶段主动获取到 debt-collection 的相关历史经验
    ✅ Project B 复用了 ≥ 2 个来自 debt-collection 的专家（compliance-auditor 等）
    ✅ forge compare-plans 可显示跨项目方案对比（如 debt vs project-b 的方案质量对比）
    ✅ debt-collection 完成第一次完整 RETRO，经验进入工厂知识库

Phase D：持续演进（第 9 周起，长期）

工作模式：由真实问题触发，不提前投资不确定需求。
触发条件	对应行动
forge compare-plans 数据显示某方案持续质量最高	将其设为 default 方案
某 API 提供商出现稳定性问题	routing_plans.yaml 中替换，不改代码
用户发现某字段策略需调整	修改 privacy_policy.yaml，不改代码
新模型发布且质量更好	models.yaml 新增，routing_plans 新建方案
RAG 召回率成为明显瓶颈（人工抽查确认）	引入 BM25 + 向量混合检索
Agent 行为难以追踪（调试频繁失败）	引入本地 Langfuse 自托管
月度 API 成本 > $50	重新评估 ModelRouter，增加本地覆盖
每日 API 调用 > 500 次	启动基础 RAG 质量评估（届时有足够数据）
需要 Web 界面（明确有外部用户）	评估 FastAPI + 简单前端（届时才值得投入）
10. Success Metrics
10.1 项目成功率
指标	当前基线	6 个月目标	1 年目标	测量方式
工厂孵化项目数（累计）	1	3	5	forge status 统计
项目进入 HARDEN 阶段率	100%（1/1）	80%	85%	阶段日志
项目 RETRO 完成率	0%（无流程）	100%	100%	retro 文档数量
P0 Bug 平均修复时间	未测量	< 1 天	< 4 小时	DEV_LOG 记录
10.2 开发效率
指标	当前基线	6 个月目标	1 年目标	测量方式
新项目从零到 CLI 可运行	推测 > 1 天	< 4 小时	< 2 小时	实际计时
单次 Agent 评审总时间（default 方案）	15-25 分钟	< 10 分钟	< 8 分钟	CLI 时间戳
单次 Agent 评审总时间（high-quality 方案）	未实现	< 12 分钟	< 10 分钟	CLI 时间戳
工作流冷启动时间	30-60 秒	< 20 秒	< 15 秒	实际计时
测试套件运行时间（单元）	未测量	< 60 秒	< 60 秒	pytest 输出
单次 RETRO 流程时间	无流程	< 20 分钟	< 15 分钟	实际计时
10.3 模型成本
指标	当前基线	月度目标	触发审查阈值
本地推理成本	$0	$0（永久保持）	永不触发
中国 API 月度成本	$0（未接入）	< $20/月	> $50/月
单次 API 调用成本（default 方案）	N/A	< $0.03/次	> $0.10/次
境外 API 成本	$0	$0（永久保持）	任何 API 费用出现
方案切换操作时间	未实现	< 1 分钟	> 5 分钟（说明双文件体系失效）
10.4 知识复用率
指标	当前基线	6 个月目标	测量方式
新项目引用已有专家比例	0%（只有 1 个项目）	≥ 40%	专家 YAML 分析
技能库命中率（新项目用到已有技能）	0%	≥ 30%	SKILL 使用统计
RETRO 经验进入工厂知识库比例	0%	100%	文件数量统计
新项目避免已知 anti-patterns	未测量	≥ 80%	RETRO 对比分析
10.5 自动化率
指标	当前基线	6 个月目标	测量方式
工作流中完全自动化节点占比	~60%	≥ 75%	流程图分析
DataPrivacyGate 自动检测准确率	0%（未实现）	≥ 95%	测试用例覆盖
模型方案切换时间（从决定到生效）	需改代码	< 1 分钟（改一个字段名）	实际计时
数据策略更新时间（从决定到生效）	需改代码	< 5 分钟（改 privacy_policy.yaml）	实际计时
ChromaDB 去重自动化	0%（每次重建）	100%	运行日志
每次发布手动操作步骤数	~8 步（ZIP 补丁）	≤ 3 步（git push + tag）	操作记录
10.6 单人可维护性（最重要指标）

评估方式：体验导向，不是数字达标。

text

✅ 合格信号：
- 三个月没碰代码，读 HANDOFF.md 后 30 分钟内恢复工作状态
- 想换一个评审模型：只改 routing_plans.yaml 中一个字段名，< 1 分钟
- 想调整数据出境策略：只改 privacy_policy.yaml，不改代码，< 5 分钟
- 新增一个外源模型：models.yaml 加一条目，routing_plans 加引用，< 10 分钟
- LangGraph 报 Bug：可在 GitHub Issues 搜到答案（大社区优势）
- 系统出故障：HANDOFF.md 排障表覆盖，30 分钟内恢复
- 让新 AI Agent 接手：读完 HANDOFF.md 后能独立运行所有功能

❌ 不合格信号（需要立即重构）：
- 想换一个模型，需要改 3 处以上代码
- 想调整数据策略，需要修改 Python 代码
- 系统出故障，不知道从哪里开始排查
- 框架升级后系统崩溃，且不知道是哪个变化导致的
- 某个模块"不敢改"，每次碰到就绕过

11. Architecture Decision Records

ADR-001：立即迁移 LangGraph（不通过抽象层推迟）

决策： 在 Phase A 直接迁移到 LangGraph 1.0，不使用 AgentRuntime 抽象层推迟。

原因：

    Agno 在 6 个月内经历 3+ 次 breaking changes（Dossier 已记录），"推迟"只是推迟痛苦
    LangGraph 1.0 已有 API 稳定性承诺，是选择它的最重要信号
    LangGraph 原生支持 HUB-SPOKE 并行（Send()）、检查点持久化（SqliteSaver）、HITL 断点——这三个恰好是最需要的功能
    月搜索量 27,100+，社区大意味着遇到问题有解决方案
    一次彻底迁移（1-2 周）的总成本低于长期修复 Agno breaking changes 的累积成本

备选方案：

    AgentRuntime 抽象层推迟迁移 ← 放弃：只是推迟 3-6 个月，不解决根源
    迁移 CrewAI 1.14 ← 放弃：并行支持弱于 LangGraph Send()，图结构表达力弱
    迁移 PydanticAI ← 放弃：编排能力相对基础，HUB-SPOKE 需额外实现

迁移路径： 独立分支并行推进，保留 Agno 实现直到验证通过，验证后完全删除 Agno。

ADR-002：双文件模型管理体系

决策： A 文件（models.yaml）定义可用模型，B 文件（routing_plans.yaml）定义节点方案，通过 RoutingPlanEngine 统一执行。

原因：

    模型选择需要频繁调整（不同任务、不同质量要求、不同成本预算）
    当前"代码中散落的模型配置"每次调整都需要改代码并重启
    双文件分离关注点：A 文件稳定（接入信息），B 文件频繁变化（调用方案）
    支持方案历史记录和 A/B 对比，是工厂知识沉淀的重要组成

备选方案：

    单文件统一配置 ← 放弃：接入信息和路由方案混在一起，职责不清
    完全代码配置 ← 放弃：切换需改代码，不符合"快捷简便"目标

ADR-003：privacy_policy.yaml 策略文件化

决策： 数据出境策略通过 YAML 文件定义，DataPrivacyGate 执行，人类决策策略内容。

原因：

    硬编码"HIGH 敏感只能本地"过于死板（身份证号在特定场景可以出境）
    策略随业务变化（新字段、新合规要求、新信任的 API 提供商）
    策略文件化使变更有追踪（DECISIONS.md 记录），比代码变更更易审计
    策略由人来定意味着人对数据处理负责，不是让代码代劳

核心设计： 4 种策略类型（local_only / human_approve / mask_then_allow / allow），未定义字段默认 human_approve（最保守）。

ADR-004：HUB-SPOKE 优先，提供多方案菜单

决策： 多方案菜单将 high-quality（多 API 并行）作为高质量首选，all-local 作为数据安全首选，用户自主选择。

原因：

    研究证据：LLM Agent 1-2 轮即可达成虚假共识（ACL 2025），顺序模式顺从性风险高
    法律建议场景中，高置信错误比慢速正确更危险
    LangGraph Send() 原生支持并行，HUB-SPOKE 不再有额外实现成本
    并行 API 评审者与本地评审者组合，在 GPU 不溢出前提下实现真正并行

GPU 安全设计： RoutingPlanEngine 在执行并行方案前，通过 models.yaml 中的 memory_required_gb 预估总内存需求（保守值 + 15% 缓冲），超出时自动降级为信息屏蔽顺序模式并提示用户。

ADR-005：IDE 层选用 Claude Code for VS Code + LiteLLM

决策： 以 Claude Code for VS Code 为主要开发辅助工具，通过 LiteLLM Gateway 连接本地和外源模型。

原因：

    Claude Code 在代码理解和生成上质量优秀，且支持配置自定义 API 端点
    通过 LiteLLM 网关，开发框架代码时可用外源高质量模型；处理敏感数据文件时可选择切换到本地模型
    统一使用 LiteLLM 网关意味着 Claude Code、CLI、Agent 三者共享同一个模型接入配置（A 文件）

ADR-006：LangGraph 后不再需要 AgentRuntime 抽象层

决策： v1.0.0 中设计的 AgentRuntime 抽象层在本版本中取消。

原因：

    抽象层的设计目的是"隔离 Agno 的不稳定性"
    迁移到 LangGraph 1.0 后，根源问题消除，抽象层失去存在理由
    LangGraph 的 StateGraph API 已经是足够稳定的接口，直接使用更简洁
    保持"不为了抽象而抽象"的原则

12. Red Team Findings

RF-001（升级版）：LangGraph 迁移本身就是最大的短期风险

攻击角度： 迁移本身是风险最高的操作。LangGraph 的编程模型（图结构 + 状态机）与 Agno 的团队协作模型（team.run()）根本不同。迁移期间系统完全不可用，且迁移引入的 Bug 可能混入业务 Bug 难以区分。

具体威胁：

    LangGraph 的状态管理是显式的（State TypedDict），Agno 是隐式的——迁移需要重新设计所有数据流
    LangGraph 的并行执行（Send()）需要处理并发安全，这是原来 Agno 顺序模式没有的复杂度
    LangGraph 的检查点系统改变了错误恢复的逻辑

风险评级： 🔴 高（但是短期、可控的，不是长期风险）

RF-002：双文件体系的同步一致性问题

攻击角度： A 文件定义了 local-qwen35b，B 文件引用了 local-qwen35b。当用户在 A 文件修改了模型 ID（把 qwen35b 换成了 qwen3.5:35b-a3b-q4），但忘记 B 文件中有 10 个方案都引用了旧名字，系统会静默失败或报出让人困惑的错误。

风险评级： 🟠 中高

RF-003：privacy_policy.yaml 策略灵活化带来的"策略蔓延"风险

攻击角度： 策略越灵活，策略文件越复杂，最终没人能清楚记住"哪些数据在哪些条件下可以出境"。当策略有 20+ 个字段定义和 5+ 个目标端点时，DataPrivacyGate 的审计可信度反而下降——因为连策略维护者都不清楚完整规则集。

风险评级： 🟡 中低

RF-004：GPU 并行安全检查的准确性问题

攻击角度： RoutingPlanEngine 通过读取 models.yaml 中的 memory_required_gb 来判断是否可以并行。但这个数字是手写估计值，不是实时的 Ollama 内存使用量。在实际运行中，KV cache 随对话长度增长，实际内存可能超过估计值，导致 OOM 错误。

风险评级： 🟠 中高
RF-005：知识库质量无法保证，RAG 可能产生"专业外表的错误建议"（模型风险，极高）

攻击角度： 当前知识库由人工维护，但内容质量未经 RAG 层面验证。LLM 使用 RAG 检索的错误文档时，会生成"听起来很专业但实际错误"的法律建议，比空输出更危险（因为用户更容易相信它）。

具体威胁：

    专家知识库更新不及时（法规修改未同步）
    分块策略默认，上下文切割在不恰当的位置
    没有 RAG 质量评估，无法发现"知识库质量已退化"

风险评级： 🔴 高（法律场景中的错误建议有实际损失风险）

RF-006：方案对比数据的有效性依赖用户主动评分

攻击角度： ModelRunRecord 记录了方案ID、耗时、成本，但质量评分（human_quality_score）是可选字段，依赖用户事后填写。如果用户从不填写质量评分，forge compare-plans 只能比较速度和成本，无法比较质量——这是"模型方案选优"的核心目标，却恰好无法实现。

风险评级： 🟡 中低

13. Blue Team Responses
对 RF-001（LangGraph 迁移风险）

回应： 承认这是 Phase A 最大风险，通过严格的迁移策略控制。

text

迁移策略（最小化风险）：

1. 并行运行（不是替换）：
   在独立分支同时维护 Agno 实现和 LangGraph 实现
   两者运行相同的 test cases，对比输出质量
   只有当 LangGraph 实现通过全量测试才合并

2. 渐进迁移（不是一次重写）：
   Step 1：迁移单个 reviewer Agent（最小单元）
   Step 2：迁移完整 review team（主流程）
   Step 3：集成 HUB-SPOKE 并行
   Step 4：集成检查点持久化
   每个 Step 独立验证通过才进入下一个

3. 回滚保障：
   Agno 实现保留在 git branch `agno-backup` 直到 LangGraph 稳定 2 周
   任何时候可以一键回滚

4. 测试先行：
   迁移前先补充测试用例（包括：输入输出格式、分歧检测、HITL 触发）
   测试用例与实现无关（不测试 Agno API，测试业务行为）

对 RF-002（双文件同步一致性）

回应： 在 RoutingPlanEngine 启动时增加交叉验证。

Python

class RoutingPlanEngine:
    def validate_consistency(self) -> ValidationResult:
        """
        启动时验证 A 文件和 B 文件的一致性：
        检查 B 文件中所有方案引用的模型名，是否都在 A 文件中定义
        """
        available_models = set(self.models_config.models.keys())
        errors = []
        
        for plan_id, plan in self.routing_config.plans.items():
            for node_name, node_config in plan.nodes.items():
                if node_config.model not in available_models:
                    errors.append(
                        f"方案 '{plan_id}' 节点 '{node_name}' "
                        f"引用了未定义的模型 '{node_config.model}'"
                    )
        
        if errors:
            raise ConfigurationError(
                "模型配置不一致，请检查：\n" + "\n".join(errors)
            )
        return ValidationResult.OK

# 启动时自动调用，明确报错而非静默失败

对 RF-003（策略蔓延风险）

回应： 引入策略简洁性原则和定期策略复查。

text

策略设计原则（写入 privacy_policy.yaml 顶部注释）：

1. 字段数量建议 ≤ 20 个（超出说明数据模型可能需要重构）
2. 政策类型只有 4 种：local_only / human_approve / mask_then_allow / allow
   不引入更多类型（简单的规则集更容易理解和审计）
3. 每季度做一次"策略复查"（10 分钟）：
   检查哪些字段的策略已经不适用，删除或更新
4. 新增字段时默认 policy: human_approve（最保守策略）
   不需要思考"这个字段敏感吗"，默认保守，后续可放宽

定期策略复查触发：
$ forge privacy-audit
→ 输出：每个字段的策略 + 最近 30 天内被 DataPrivacyGate 触发的次数
→ 如果某字段 30 天内从未触发（意味着从未出境），提示"考虑是否需要保持此策略"
→ 如果某字段 30 天内触发 > 50 次（频繁触发确认），提示"考虑是否可以放宽策略"

对 RF-004（GPU 内存估计不准确）

回应： 多层保护。

text

层1：保守估计 + 安全缓冲
models.yaml 中的 memory_required_gb 填写保守值（高于实际需要）
RoutingPlanEngine 计算时再加 15% 安全缓冲

层2：实时查询（可选）
$ ollama ps  # 查看当前已加载模型和内存占用
RoutingPlanEngine 可选择在执行前调用 ollama ps API 获取实时内存状态
（比纯估计更准确，但增加一次 API 调用）

层3：优雅降级
如果检测到内存压力（Ollama 返回 OOM 错误），
LangGraph 检查点确保状态已持久化，
系统提示："本地内存不足，自动降级为信息屏蔽顺序模式"
不崩溃，不丢失数据，给用户明确的信息

层4：用户可见的内存提示
方案菜单中，每个方案显示"预估内存使用：XX GB"
用户在选择前就能看到，而不是运行时才发现

对 RF-005（知识库质量）
回应： 这是最高优先级的真实风险，特别是法律场景。

短期缓解（Phase B）：

    每次知识库更新必须有 VERSION 文件更新
    更新时强制显示警告："知识库已更新，建议运行 3 个已知测试用例验证质量"
    在 CLI 输出中明确标注："以下内容基于知识库版本 v1.2，请人工验证重要决策"

中期方案（Phase D 触发条件）：

    当知识库 > 5 个专家时，引入简单的质量监控：随机抽取 5 个问题，比较本周与上周的答案，显示变化（不是自动评分，是提醒人工注意）
    不引入完整 RAGAS（需要 Ground Truth），而是用"领域专家人工抽查"替代（每月 1 次，15 分钟）

永久措施：

    铁闸规则永远不依赖 RAG 知识库（硬编码）
    高风险法律建议必须标注"需人工验证"

对 RF-006（质量评分依赖用户主动填写）

回应： 降低填写摩擦，并提供间接质量指标。

text

降低摩擦：
每次评审结束，CLI 自动提示：
"评审完成。请问这次建议有用吗？[1-很有用 / 2-一般 / 3-没用 / 回车跳过]"
一个按键完成评分，10 秒内可完成

间接质量指标（不依赖主动评分）：
- adopted_by_user：用户在"是否采纳建议"提示中的选择（已有此字段）
- follow_up_corrections：用户在同案件下次评审时是否否定了上次结论
- divergence_score：评审间分歧度（分歧高的方案质量通常不如分歧低的）

方案对比报告的降级策略：
- 有用户评分时：显示平均质量评分
- 无用户评分时：显示采纳率 + 分歧度（间接指标）
- 同时提示："填写质量评分可以让方案对比更准确"

14. Refined Architecture

基于红蓝对抗，最终精炼后的架构修正：
修正 1：LangGraph 迁移分步策略（对应 RF-001）

迁移分 4 个独立验证步骤，每步都有独立的验收标准，不合并到主分支直到全部通过。详见 Phase A。
修正 2：双文件启动时一致性校验（对应 RF-002）

Python

# RoutingPlanEngine.__init__() 中调用
self.validate_consistency()  # 不通过则明确报错，不让系统带着错误配置运行

修正 3：privacy_policy.yaml 内置简洁性原则（对应 RF-003）

策略文件顶部注释说明设计原则；4 种策略类型不扩展；forge privacy-audit 定期提示。
修正 4：GPU 内存三层保护（对应 RF-004）

保守估计 + 可选实时查询 + LangGraph 检查点优雅降级。方案菜单显示预估内存。
修正 5：质量评分一键化（对应 RF-007）

评审结束后一键评分提示，提供间接质量指标作为补充。
修正 6：迁移完成后删除 Agno 全部代码

迁移验证通过后，从代码库中完全删除 Agno 相关代码，不保留"万一需要回滚"的旧代码（Git history 已保留）。保持代码库干净。
最终架构精炼图（v1.1.0）


五阶段工作流（方法论核心，不随代码变化）
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│              平台层（稳定接口）                            │
│  LangGraph 1.0    KnowledgeHub    ModelRegistry         │
│  DecisionEngine   DataPrivacyGate MemoryStore           │
│  RoutingPlanEngine（B文件驱动）                           │
│         ↑ 所有平台层组件都是独立可测试的单元               │
└────────────────────────┬────────────────────────────────┘
                         │
                    直接使用 LangGraph API
                    不再需要抽象层
┌────────────────────────▼────────────────────────────────┐
│              配置层（人工控制，代码执行）                  │
│  models.yaml (A文件) → LiteLLM Gateway → 所有模型端点    │
│  routing_plans.yaml (B文件) → 节点模型分配               │
│  privacy_policy.yaml → DataPrivacyGate 执行策略          │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              数据层（最稳定层）                            │
│  SQLite 业务DB+模型对比记录   ChromaDB 向量DB             │
│  LangGraph SqliteSaver检查点  _factory/知识库            │
└─────────────────────────────────────────────────────────┘

IDE 层：Claude Code for VS Code → LiteLLM Gateway（4000端口）
        → local/* 或 api/* 按需切换

15. Self Review
Round 1：最大漏洞

漏洞： LangGraph 迁移是 Phase A 唯一的关键路径。如果迁移时间超出预估（从 1-2 周变成 3-4 周），整个 Phase A 的其他所有目标都会被阻塞——双文件体系、privacy_policy、LiteLLM 集成——因为它们都依赖 LangGraph 的图节点设计。

这个漏洞是否可修复？ 部分可修复。

修复方向：

    双文件体系（A/B 文件 + models.yaml）可以在 Agno 上先实现，不依赖 LangGraph
    privacy_policy.yaml + DataPrivacyGate 完全独立，可以并行开发
    只有 HUB-SPOKE 的 Send() 并行和检查点依赖 LangGraph

调整策略：Phase A 改为"并行推进两条线"：

    线 1：LangGraph 迁移（在独立分支，允许超时）
    线 2：双文件体系 + DataPrivacyGate（在主分支，立即产生价值）

Round 2：最大假设

假设： "用户会在 routing_plans.yaml 中为不同场景维护多个方案，并通过 forge compare-plans 数据驱动地选优。"

这个假设的隐藏依赖：

    用户有足够的意愿维护多个方案（而非一旦有"够用"的方案就不再优化）
    用户会在评审结束后填写质量评分（否则对比数据缺乏核心指标）
    相同案件会被评审多次（只有重复评审才有对比数据）

如果假设失效：

    双文件体系仍然有价值：即使不做方案对比，切换模型只改一个字段名本身就是巨大的易用性提升
    方案对比功能降级为"有了更好，没有也没损失"的附加功能
    不影响核心架构价值

结论： 这是可接受的假设，因为假设失效的成本很低（只是少了一个附加功能），而假设成立的收益很高（数据驱动的模型选优）。
Round 3：未来失效点

最可能在 2-3 年后失效的架构决策：

失效点 1： LiteLLM 作为网关的地位

如果 2028 年 Ollama 原生支持 OpenAI 兼容的多模型路由，LiteLLM 的核心价值（统一不同提供商的接口）可能消失。届时 A 文件可以直接驱动 Ollama，LiteLLM 层可以移除而不影响 B 文件和业务代码。

失效点 2： privacy_policy.yaml 的字段级策略在模型能力极大提升后可能过于保守

当本地 7B 模型的质量足够好时，现在需要"human_approve 才能出境"的分析任务可能完全可以本地完成。策略文件会积累大量历史性的"保守策略"字段，需要定期清理。

失效点 3： 双文件体系在项目数量 > 10 时的管理复杂度

每个项目都有自己的 models.yaml 和 routing_plans.yaml，当有 10+ 个项目时，模型接入信息会在多个项目中重复。届时需要"工厂级 models.yaml"（全局共享）+ "项目级 routing_plans.yaml"（项目专有）的两层设计。

预防策略：

    双文件体系的 models.yaml 格式已经支持这种拆分（只需把 A 文件提升到工厂层）
    privacy_policy.yaml 的年度复查机制（已设计）可以发现过时的保守策略
    LiteLLM 的移除成本极低（只改 A 文件的 provider 字段指向方式）

单人三年可维护性最终判定：✅ 通过

关键改善点：

    LangGraph 1.0 的 API 稳定承诺 → 减少了最大的单点风险
    双文件体系 → 模型切换不需要改代码，维护成本大幅降低
    privacy_policy.yaml → 数据策略调整不需要改代码，合规维护更简单
    LangGraph 大社区 → 遇到问题有现成的 GitHub Issues 和文档

如果三年后只有一个人维护：

    切换评审模型：修改 routing_plans.yaml 中的一个字段名，< 1 分钟
    调整数据策略：修改 privacy_policy.yaml 中的 policy 字段，< 5 分钟
    新增外源模型：在 models.yaml 增加一个条目，在 routing_plans 中引用，< 10 分钟
    LangGraph 框架问题：查 LangGraph GitHub Issues（27,100 月搜索量的社区支持）
    系统故障：HANDOFF.md 排障表，30 分钟内恢复
    知识传递：三个配置文件 + HANDOFF.md + DECISIONS.md = 完整的系统知识外化

这个架构能持续三年单人运行。

