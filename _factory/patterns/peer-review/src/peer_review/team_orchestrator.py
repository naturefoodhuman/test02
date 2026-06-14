# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-14 16:50:00 CST
"""团队编排器模块

从 orchestrator.py 提取，单一职责：构建评审团队、运行编排流程。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Tuple

from rich.console import Console
console = Console()

# --- 防御性导入 ---
try:
    from agno.agent import Agent
    from agno.team import Team
    from agno.models.ollama import Ollama
except ImportError as e:
    console.print(f"[bold red]❌ Agno 核心导入失败: {e}[/bold red]")
    raise

# --- 兼容性：模型别名映射 ---
MODEL_ALIAS_MAP = {
    "local/primary": "qwen3.6:35b-a3b-q8_0",
    "local/r1": "deepseek-r1:32b",
    "cloud/glm-primary": "openai/glm-4-plus",
}

def resolve_model_id(raw_model_id: str) -> str:
    """将别名解析为真实的 Ollama/Model ID"""
    return MODEL_ALIAS_MAP.get(raw_model_id, raw_model_id)


# --- 编排器 ---
class PeerReviewOrchestrator:
    """Peer-Review 编排器：管理多专家评审流程"""

    def __init__(
        self,
        primary: Agent,
        reviewers: List[Agent],
        model_override: str = None
    ):
        self.primary = primary
        self.reviewers = reviewers
        active_id = resolve_model_id(model_override) if model_override else primary.model.id
        console.print(f"[dim]🤖 Team 模型: {active_id}[/dim]")

        self.team = Team(
            name="ReviewTeam",
            mode="sequential",
            members=[primary] + reviewers,
            model=Ollama(id=active_id),
            markdown=True
        )

    def run_review(self, query: str) -> str:
        """运行完整评审流程

        Args:
            query: 评审查询/案件上下文

        Returns:
            评审结果文本
        """
        console.print(f"[bold green]🔍 启动多专家评审...[/bold green]")
        try:
            resp = self.team.run(query)
            return resp.content if hasattr(resp, 'content') else str(resp)
        except Exception as e:
            return f"评审异常：{e}"


# --- 配置加载器：集成新配置体系 ---
try:
    from peer_review.config import (
        load_expert_configs,
        load_all_configs,
        get_project_root,
        ConfigurationError,
    )
    NEW_CONFIG_AVAILABLE = True
except ImportError:
    NEW_CONFIG_AVAILABLE = False


def _convert_pydantic_to_dataclass(pydantic_expert) -> "ExpertConfig":
    """将 Pydantic ExpertConfig 转换为兼容的 dataclass ExpertConfig"""
    from .agent_factory import ExpertConfig as FactoryExpertConfig
    return FactoryExpertConfig(
        id=pydantic_expert.id,
        name=pydantic_expert.name,
        role=pydantic_expert.role.value if hasattr(pydantic_expert.role, 'value') else str(pydantic_expert.role),
        system_prompt=pydantic_expert.system_prompt or "",
        model_id=resolve_model_id(pydantic_expert.model),
        knowledge_dir=str(Path(pydantic_expert.knowledge_sources[0]).parent) if pydantic_expert.knowledge_sources else "",
        top_k=5,
    )


def build_review_team(experts_dir: Path) -> Tuple[Agent, List[Agent]]:
    """构建评审团队：优先使用新配置体系，回退兼容模式

    Args:
        experts_dir: 专家目录路径

    Returns:
        (primary_agent, reviewers_list)

    Raises:
        ValueError: 未找到主专家或目录不存在
    """
    from .agent_factory import ExpertFactory, ExpertConfig as FactoryExpertConfig
    from .knowledge_loader import KnowledgeLoader

    primary, reviewers = None, []

    if NEW_CONFIG_AVAILABLE:
        # 新版：使用 Pydantic 配置加载器，含交叉验证
        try:
            project_root = get_project_root()
            cfg = load_all_configs(project_root)
            experts_dict = cfg.experts
            console.print(f"✅ 新配置体系加载成功：{len(experts_dict)} 位专家")
        except ConfigurationError as e:
            console.print(f"[yellow]⚠️ 新配置校验失败，回退兼容模式: {e}[/yellow]")
            experts_dict = None
        except Exception as e:
            console.print(f"[yellow]⚠️ 新配置加载异常，回退兼容模式: {e}[/yellow]")
            experts_dict = None

        if experts_dict:
            for expert_id, pydantic_expert in experts_dict.items():
                config = _convert_pydantic_to_dataclass(pydantic_expert)
                kb = KnowledgeLoader.load_knowledge(config)
                agent = ExpertFactory.create_agent(config, kb)
                console.print(f"🤖 加载专家: {config.name} ({config.role})")
                if config.role == "primary":
                    primary = agent
                else:
                    reviewers.append(agent)

            if not primary:
                raise ValueError("未找到主专家 (new config)")
            return primary, reviewers

    # 兼容模式：旧版手写解析器 (保留用于回退)
    console.print("[dim]使用兼容模式加载专家...[/dim]")
    if not experts_dir.exists():
        raise ValueError(f"目录不存在: {experts_dir}")

    for d in experts_dir.glob("*.expert"):
        # 跳过模板目录
        if d.name.startswith("_"):
            continue
        cfg = _load_expert_config_compat(d / "expert.yaml", d.name.replace(".expert", ""))
        if cfg is None:
            continue
        kb = KnowledgeLoader.load_knowledge(cfg)
        agent = ExpertFactory.create_agent(cfg, kb)
        console.print(f"🤖 加载专家: {cfg.name} ({cfg.role})")
        if cfg.role == "primary":
            primary = agent
        else:
            reviewers.append(agent)

    if not primary:
        raise ValueError("未找到主专家")
    return primary, reviewers


def _load_expert_config_compat(yaml_path: Path, fallback_id: str) -> "ExpertConfig | None":
    """兼容模式：旧版手写 YAML 解析器 (保留用于回退)"""
    try:
        import yaml
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

    from .agent_factory import ExpertConfig as FactoryExpertConfig
    return FactoryExpertConfig(
        id=expert_id,
        name=data.get("name", expert_id),
        role=role_str,
        system_prompt=sys_prompt,
        model_id=resolve_model_id(raw_model or "qwen3.6:35b-a3b-q8_0"),
        knowledge_dir=str(yaml_path.parent / "knowledge"),
    )