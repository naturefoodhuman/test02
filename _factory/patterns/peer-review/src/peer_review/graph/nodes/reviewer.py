# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 02:20:00 CST
"""评审者节点（HUB-SPOKE 信息屏蔽）

职责：
- 每个评审者只读取 case_context，不读取 primary_analysis 或其他评审意见
- 独立给出评审意见
- 支持并行执行（LangGraph Send）
"""

from __future__ import annotations

from typing import Any

from langgraph.types import Send

from peer_review.graph.state import ReviewState
import peer_review.llm_client as llm_client
from peer_review.platform.routing_plan_engine import RoutingPlanEngine
from rich.console import Console

console = Console()


def make_reviewer_node(routing_engine: RoutingPlanEngine, node_name: str, role: str):
    """创建单个评审者节点函数

    Args:
        routing_engine: 路由引擎
        node_name: routing_plans.yaml 中的节点名（如 reviewer_1）
        role: 角色标签（如 风险评估、合规审查）
    """

    def reviewer_node(state: ReviewState) -> ReviewState:
        case_context = state.get("case_context", "")
        model_cfg = routing_engine.get_model_for_node(node_name)

        system_prompt = (
            f"你是一位独立的债务案件{role}专家。你只基于案件事实本身进行评审，"
            "不要受其他分析或结论影响。给出你的独立判断、风险点与建议。"
        )
        prompt = f"案件事实：\n{case_context}\n\n请从'{role}'角度给出独立评审意见。"
        privacy_context = None
        if state.get("data_fields") and state.get("privacy_endpoint"):
            privacy_context = {
                "data_fields": state.get("data_fields"),
                "endpoint": state.get("privacy_endpoint"),
                "approved": state.get("privacy_approved"),
            }
        resp = llm_client.chat(
            model_cfg,
            [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            privacy_context=privacy_context,
        )

        console.print(f"[dim]🤖 {node_name} ({role}) 使用模型: {model_cfg.display_name}[/dim]")
        return {
            "reviewer_opinions": [resp.content],
            "reviewer_roles": [role],
            "models_used": {node_name: model_cfg.model_id},
        }

    return reviewer_node


def dispatch_to_reviewers(state: ReviewState) -> list[Send]:
    """HUB-SPOKE 分发器：根据激活方案把评审任务并行/顺序发送给各评审者

    当前实现：发送给 reviewer_1 / reviewer_2 / reviewer_3（如果方案中存在）
    """
    sends: list[Send] = []
    # 从状态中获取路由引擎（由图构建时注入）
    routing_engine = state.get("_routing_engine")
    if routing_engine is None:
        return sends

    plan = routing_engine.get_active_plan()
    for node_name, node_cfg in plan.nodes.items():
        if not node_name.startswith("reviewer_"):
            continue
        sends.append(Send(node_name, {"case_context": state.get("case_context", "")}))

    return sends
