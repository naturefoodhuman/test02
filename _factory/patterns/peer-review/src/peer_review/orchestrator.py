# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-13 23:45:00 CST
"""
Peer-Review 多专家评审引擎 v1.0.5 (Agno + LlamaIndex + ChromaDB 重构版)
特性：全兼容导入层、禁用遥测、模型别名解析、CLI 适配
"""
import sys
import os
import json
import yaml
from pathlib import Path
from typing import Any, List
from dataclasses import dataclass, field

from rich.console import Console
console = Console()

# --- 核心修复 1: 禁用 Agno 遥测 (数据不出本机) ---
os.environ["AGNO_TELEMETRY"] = "false"

# --- 核心修复 2: 兼容导入层 (Defensive Imports) ---
SimpleDirectoryReader = None
try:
    from llama_index.core.readers import SimpleDirectoryReader
except ImportError:
    try:
        from llama_index.readers.file import SimpleDirectoryReader
    except ImportError:
        pass

try:
    from agno.agent import Agent
    from agno.team import Team
    from agno.models.ollama import Ollama
except ImportError as e:
    console.print(f"[bold red]❌ Agno 核心导入失败: {e}[/bold red]")
    sys.exit(1)

ChromaDb = None
try:
    from agno.vectordb.chromadb import ChromaDb
except ImportError:
    try:
        from agno.vectordb.chroma import ChromaDb
    except ImportError:
        pass

AgentKnowledge = None
try:
    from agno.knowledge.agent import AgentKnowledge
except ImportError:
    pass

# --- 模型别名映射 (解决 404 Not Found) ---
MODEL_ALIAS_MAP = {
    "local/primary": "qwen3.6:35b-a3b-q8_0",
    "local/r1": "deepseek-r1:32b",
    "cloud/glm-primary": "openai/glm-4-plus",
}

def resolve_model_id(raw_model_id: str) -> str:
    """将别名解析为真实的 Ollama/Model ID"""
    return MODEL_ALIAS_MAP.get(raw_model_id, raw_model_id)

# --- 数据类 ---
@dataclass
class ExpertConfig:
    id: str
    name: str
    role: str
    system_prompt: str = ""
    model_id: str = "qwen3.6:35b-a3b-q8_0"
    knowledge_dir: str = ""
    top_k: int = 5

# --- 知识加载器 ---
class KnowledgeLoader:
    _instances = {}

    @classmethod
    def load_knowledge(cls, config: ExpertConfig, persist_dir: str = "runtime/chroma_data") -> Any | None:
        if SimpleDirectoryReader is None or ChromaDb is None: return None
        if not config.id or config.id.startswith("_"): return None
        if config.id in cls._instances: return cls._instances[config.id]
        
        source_dir = Path(config.knowledge_dir)
        if not source_dir.exists() or not any(source_dir.iterdir()): return None

        console.print(f"📚 正在构建专家 [{config.id}] 向量索引...")
        try:
            docs = SimpleDirectoryReader(input_dir=str(source_dir)).load_data()
            db = ChromaDb(path=persist_dir, collection=config.id)
            if hasattr(db, 'load_documents'):
                db.load_documents(documents=docs, upsert=True)
            cls._instances[config.id] = db
            return db
        except Exception as e:
            console.print(f"[yellow]⚠️ [{config.id}] 索引跳过: {e}[/yellow]")
            return None

# --- 专家工厂 ---
class ExpertFactory:
    @staticmethod
    def create_agent(config: ExpertConfig, kb: Any) -> Agent:
        sys_prompt = config.system_prompt if config.system_prompt else f"你是 {config.name}。"
        agent_kb = None
        if kb and AgentKnowledge:
            try: agent_kb = AgentKnowledge(vector_db=kb, num_documents=config.top_k)
            except Exception: pass

        return Agent(
            name=config.name,
            model=Ollama(id=config.model_id),
            instructions=[sys_prompt, "基于知识库回答，客观专业。"],
            knowledge=agent_kb,
        )

# --- 编排器 ---
class PeerReviewOrchestrator:
    def __init__(self, primary: Agent, reviewers: list[Agent], model_override: str = None):
        self.primary = primary
        self.reviewers = reviewers
        active_id = resolve_model_id(model_override) if model_override else primary.model.id
        console.print(f"[dim]🤖 Team 模型: {active_id}[/dim]")

        self.team = Team(
            name="ReviewTeam", mode="sequential", 
            members=[primary] + reviewers, 
            model=Ollama(id=active_id), markdown=True
        )

    def run_review(self, query: str) -> str:
        console.print(f"[bold green]🔍 启动多专家评审...[/bold green]")
        try:
            resp = self.team.run(query)
            return resp.content if hasattr(resp, 'content') else str(resp)
        except Exception as e:
            return f"评审异常：{e}"

# --- 配置加载器 ---
def load_expert_config(yaml_path: Path, fallback_id: str) -> ExpertConfig | None:
    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if not data: return None
    except Exception: return None
        
    expert_id = data.get("id", fallback_id)
    if not expert_id or expert_id.startswith("_"): return None 

    raw_role = data.get("role", "reviewer")
    role_str = str(raw_role).strip() if not isinstance(raw_role, dict) else "primary"
    sys_prompt = raw_role.get("identity", "") if isinstance(raw_role, dict) else data.get("system_prompt", "")

    raw_model = data.get("model", None)
    if not raw_model:
        routing = data.get("routing", {})
        if isinstance(routing, dict): raw_model = routing.get("primary_reasoning", "qwen3.6:35b-a3b-q8_0")
    
    return ExpertConfig(
        id=expert_id, name=data.get("name", expert_id), role=role_str,
        system_prompt=sys_prompt, model_id=resolve_model_id(raw_model or "qwen3.6:35b-a3b-q8_0"),
        knowledge_dir=str(yaml_path.parent / "knowledge"),
    )


# --- LangGraph 兼容入口（新架构）---

from rich.live import Live
from rich.table import Table
from rich.panel import Panel


def _make_progress_table(node_status: dict[str, str]) -> Table:
    """构建 Rich Live 进度表"""
    table = Table(title="Peer-Review 评审进度", show_header=True, header_style="bold magenta")
    table.add_column("节点", style="cyan")
    table.add_column("状态", style="green")
    for node, status in node_status.items():
        table.add_row(node, status)
    return table


def run_langgraph_review(
    query: str,
    project_root: Path | None = None,
    config_only: bool = False,
    plan_id: str | None = None,
    data_fields: dict[str, Any] | None = None,
    privacy_endpoint: str | None = None,
    privacy_approved: bool | None = None,
    use_live: bool = True,
) -> dict:
    """LangGraph 评审入口（v1.1.0 新架构）

    Args:
        query: 案件上下文
        project_root: 项目根目录；为 None 时自动探测
        config_only: 为 True 时仅返回配置对象而不运行图（用于测试）
        plan_id: 临时覆盖 active_plan 的方案 ID（不修改配置文件）
        data_fields: 原始数据字段（用于 LLM 客户端节点级隐私校验）
        privacy_endpoint: 隐私策略目标端点（如 chinese_api）
        privacy_approved: CLI 是否已通过 DataPrivacyGate 人工确认
        use_live: 是否使用 Rich Live Display 展示进度

    Returns:
        若 config_only=True 返回 dict(routing_engine=..., knowledge_hub=...)
        否则返回最终状态 dict（含 thread_id 用于 HITL 恢复）
    """
    from peer_review.graph.review_graph import build_review_graph
    from peer_review.platform.knowledge_hub import KnowledgeHub
    from peer_review.platform.routing_plan_engine import RoutingPlanEngine

    if project_root is None:
        from peer_review.config import get_project_root
        project_root = get_project_root()

    routing_engine = RoutingPlanEngine(project_root)

    # 临时切换方案（不持久化到文件）
    if plan_id and plan_id in routing_engine.config.routing.plans:
        routing_engine.config.routing.active_plan = plan_id

    active_plan = routing_engine.config.routing.active_plan

    knowledge_hub = KnowledgeHub(
        knowledge_root=project_root / "_factory" / "experts",
        skills_root=project_root / "_factory" / "skills",
    )

    if config_only:
        return {"routing_engine": routing_engine, "knowledge_hub": knowledge_hub}

    graph = build_review_graph(routing_engine, knowledge_hub)

    import uuid
    thread_id = "review-" + str(uuid.uuid4())[:8]
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "case_context": query,
        "model_plan_id": active_plan,
        "data_fields": data_fields,
        "privacy_endpoint": privacy_endpoint,
        "privacy_approved": privacy_approved,
    }

    # 收集所有节点名用于 Live 进度表
    node_names = ["primary_expert"] + [
        n for n in graph.nodes if n.startswith("reviewer_")
    ] + ["consensus_builder", "human_review_gate"]
    node_status = {n: "⏳ 等待" for n in node_names}

    if use_live:
        with Live(_make_progress_table(node_status), console=console, refresh_per_second=4) as live:
            for event in graph.stream(
                initial_state,
                config=config,
                stream_mode="updates",
            ):
                for node_name, node_state in event.items():
                    if node_name == "primary_expert" and "primary_analysis" in node_state:
                        node_status[node_name] = "✅ 完成"
                    elif node_name.startswith("reviewer_"):
                        node_status[node_name] = "✅ 完成"
                    elif node_name == "consensus_builder":
                        divergence = node_state.get("divergence_score", 0)
                        node_status[node_name] = f"✅ 完成 (分歧度 {divergence})"
                    elif node_name == "human_review_gate":
                        node_status[node_name] = "🛑 人工审核中断点"
                live.update(_make_progress_table(node_status))
    else:
        for event in graph.stream(
            initial_state,
            config=config,
            stream_mode="updates",
        ):
            for node_name, node_state in event.items():
                if node_name == "primary_expert" and "primary_analysis" in node_state:
                    console.print(f"[dim]→ 主专家完成[/dim]")
                elif node_name.startswith("reviewer_"):
                    console.print(f"[dim]→ {node_name} 完成[/dim]")
                elif node_name == "consensus_builder":
                    console.print(f"[dim]→ 汇总完成 (分歧度: {node_state.get('divergence_score', 0)})[/dim]")
                elif node_name == "human_review_gate":
                    console.print("[yellow]→ 触发人工审核中断点[/yellow]")

    # 获取完整最终状态（包含所有节点写入）
    final_state = graph.get_state(config)
    if final_state is None or final_state.values is None:
        return {"thread_id": thread_id}
    result = dict(final_state.values)
    result["thread_id"] = thread_id
    return result


def continue_langgraph_review(
    thread_id: str,
    project_root: Path | None = None,
    plan_id: str | None = None,
    use_live: bool = True,
) -> dict:
    """从 HITL 中断点恢复 LangGraph 评审

    Args:
        thread_id: 之前 run_langgraph_review 返回的线程 ID
        project_root: 项目根目录
        plan_id: 临时覆盖方案（通常不需要，保持与之前一致）
        use_live: 是否使用 Rich Live Display

    Returns:
        最终状态 dict
    """
    from peer_review.graph.review_graph import build_review_graph
    from peer_review.platform.knowledge_hub import KnowledgeHub
    from peer_review.platform.routing_plan_engine import RoutingPlanEngine

    if project_root is None:
        from peer_review.config import get_project_root
        project_root = get_project_root()

    routing_engine = RoutingPlanEngine(project_root)
    if plan_id and plan_id in routing_engine.config.routing.plans:
        routing_engine.config.routing.active_plan = plan_id

    knowledge_hub = KnowledgeHub(
        knowledge_root=project_root / "_factory" / "experts",
        skills_root=project_root / "_factory" / "skills",
    )
    graph = build_review_graph(routing_engine, knowledge_hub)

    config = {"configurable": {"thread_id": thread_id}}

    # 检查当前状态
    current_state = graph.get_state(config)
    if current_state is None or not current_state.values:
        raise ValueError(f"找不到线程 {thread_id} 的状态，无法恢复")

    # 收集节点状态用于 Live 显示
    node_names = ["primary_expert"] + [
        n for n in graph.nodes if n.startswith("reviewer_")
    ] + ["consensus_builder", "human_review_gate"]
    node_status = {n: "✅ 已完成" for n in node_names}
    node_status["human_review_gate"] = "🔄 恢复中"

    if use_live:
        with Live(_make_progress_table(node_status), console=console, refresh_per_second=4) as live:
            for event in graph.stream(None, config=config, stream_mode="updates"):
                for node_name in event:
                    if node_name == "human_review_gate":
                        node_status[node_name] = "✅ 人工审核通过"
                    elif node_name == "__end__":
                        node_status[node_name] = "✅ 结束"
                live.update(_make_progress_table(node_status))
    else:
        for event in graph.stream(None, config=config, stream_mode="updates"):
            for node_name in event:
                if node_name == "human_review_gate":
                    console.print("[green]→ 人工审核通过，继续执行[/green]")

    final_state = graph.get_state(config)
    if final_state is None or final_state.values is None:
        return {"thread_id": thread_id}
    result = dict(final_state.values)
    result["thread_id"] = thread_id
    return result


def build_review_team(experts_dir: Path) -> tuple[Agent, list[Agent]]:
    """Agno 旧版入口（保留兼容，待 LangGraph 验证后删除）"""
    primary, reviewers = None, []
    if not experts_dir.exists(): raise ValueError(f"目录不存在: {experts_dir}")

    for d in experts_dir.glob("*.expert"):
        cfg = load_expert_config(d / "expert.yaml", d.name.replace(".expert", ""))
        if cfg is None: continue
        kb = KnowledgeLoader.load_knowledge(cfg)
        agent = ExpertFactory.create_agent(cfg, kb)
        console.print(f"🤖 加载专家: {cfg.name} ({cfg.role})")
        if cfg.role == "primary": primary = agent
        else: reviewers.append(agent)
            
    if not primary: raise ValueError("未找到主专家")
    return primary, reviewers
