# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 10:00:00 CST
"""决策节点实现

职责：
- 将汇总后的结论提交给 DecisionEngine 进行最终判定
- 判定结果（铁闸触发、AI评分）写入 ReviewState
- 确定是否需要人工仲裁 (requires_human)
"""

from __future__ import annotations

from peer_review.graph.state import ReviewState
from peer_review.platform.decision_engine import DecisionEngine, DecisionContext
from rich.console import Console

console = Console()


def make_decision_node():
    """创建决策节点函数"""

    def decision_node(state: ReviewState) -> ReviewState:
        # 1. 构建决策上下文
        # 我们将汇总结论作为建议策略，主专家分析作为背景
        context = DecisionContext(
            case_text=state.get("case_context", ""),
            proposed_strategy=state.get("consensus", ""),
            sensitive_fields=state.get("data_fields", {}).keys() if state.get("data_fields") else None,
        )

        # 2. 执行三层决策
        engine = DecisionEngine()
        decision = engine.decide(context)

        # 3. 更新状态
        # 如果 DecisionType.BLOCKED，则标记铁闸触发
        from peer_review.platform.decision_engine import DecisionType
        
        iron_gate_triggered = (decision.decision == DecisionType.BLOCKED)
        
        # 决定是否需要人工审核：
        # 1. 铁闸触发 (BLOCKED) -> 必须人工
        # 2. 汇总节点已经标记 requires_human (分歧度高) -> 必须人工
        # 3. AI 判定为 REQUIRES_REVIEW -> 必须人工
        requires_human = (
            iron_gate_triggered or 
            state.get("requires_human", False) or 
            decision.decision == DecisionType.REQUIRES_REVIEW
        )

        console.print(f"[bold blue]⚖️  决策引擎判定: {decision.decision} - {decision.reason}[/bold blue]")
        if iron_gate_triggered:
            console.print("[bold red]🛑 铁闸触发！已强制路由至人工审核门[/bold red]")

        return {
            "iron_gate_triggered": iron_gate_triggered,
            "iron_gate_reason": decision.reason,
            "requires_human": requires_human,
        }

    return decision_node
