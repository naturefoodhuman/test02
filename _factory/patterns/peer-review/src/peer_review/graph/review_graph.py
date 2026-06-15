# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 02:30:00 CST
"""LangGraph HUB-SPOKE 评审图

构建 ReviewState 状态图，实现：
- primary_expert 主专家节点
- reviewer_dispatcher 条件边（HUB-SPOKE Send）
- reviewer 节点 × N（信息屏蔽，仅读 case_context）
- consensus_builder 汇总 + 分歧检测
- human_review_gate HITL 中断点
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.types import Send

from peer_review.graph.checkpointer import make_checkpointer
from peer_review.graph.nodes.consensus import make_consensus_node
from peer_review.graph.nodes.decision import make_decision_node
from peer_review.graph.nodes.memory import make_record_run_node
from peer_review.graph.nodes.primary_expert import make_primary_node
from peer_review.graph.nodes.reviewer import make_reviewer_node
from peer_review.graph.state import ReviewState
from peer_review.platform.knowledge_hub import KnowledgeHub
from peer_review.platform.routing_plan_engine import RoutingPlanEngine
from rich.console import Console

console = Console()


def build_review_graph(
    routing_engine: RoutingPlanEngine,
    knowledge_hub: KnowledgeHub,
) -> StateGraph:
    """构建 HUB-SPOKE 评审图

    Args:
        routing_engine: 路由方案引擎（B 文件驱动）
        knowledge_hub: 知识统一接口

    Returns:
        已编译的 StateGraph 实例
    """
    builder = StateGraph(ReviewState)

    plan = routing_engine.get_active_plan()

    # 注册主专家节点
    builder.add_node("primary_expert", make_primary_node(routing_engine, knowledge_hub))

    # 注册评审者节点
    reviewer_nodes = []
    for node_name, node_cfg in plan.nodes.items():
        if node_name.startswith("reviewer_"):
            builder.add_node(
                node_name,
                make_reviewer_node(routing_engine, node_name, node_cfg.role or node_name),
            )
            reviewer_nodes.append(node_name)

    # 注册汇总节点
    builder.add_node("consensus_builder", make_consensus_node(routing_engine))

    # 注册决策节点（分层决策引擎）
    builder.add_node("decision_engine", make_decision_node())

    # 注册记忆记录节点
    builder.add_node("record_run", make_record_run_node(routing_engine))

    # 注册人工审核门（HITL 中断点）
    builder.add_node("human_review_gate", lambda state: state)

    # HUB-SPOKE 分发：从主专家直接分发给所有评审者
    def dispatch_reviewers(state: ReviewState) -> list[Send]:
        case_context = state.get("case_context", "")
        return [Send(node, {"case_context": case_context}) for node in reviewer_nodes]

    # 主专家 -> 分发到各评审者
    builder.add_conditional_edges(
        "primary_expert",
        dispatch_reviewers,
        {node: node for node in reviewer_nodes},
    )

    # 各评审者 -> 汇总节点
    for node in reviewer_nodes:
        builder.add_edge(node, "consensus_builder")

    # 汇总节点 -> 决策节点
    builder.add_edge("consensus_builder", "decision_engine")

    # 决策节点 -> 人工审核 或 记录并结束
    def route_decision(state: ReviewState) -> str:
        if state.get("requires_human") or state.get("iron_gate_triggered"):
            return "human_review_gate"
        return "record_run"

    builder.add_conditional_edges("decision_engine", route_decision)

    # 人工审核 -> 记录并结束
    builder.add_edge("human_review_gate", "record_run")

    # 记录节点 -> 结束
    builder.add_edge("record_run", END)

    # 设置入口
    builder.set_entry_point("primary_expert")

    # 编译：添加 SqliteSaver 检查点，并在 human_review_gate 前中断
    checkpointer = make_checkpointer()
    return builder.compile(checkpointer=checkpointer, interrupt_before=["human_review_gate"])
