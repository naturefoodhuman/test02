# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 02:15:00 CST
"""主专家节点

职责：
- 读取案件上下文
- 调用知识库检索
- 生成本案初步分析
- 决策引擎铁闸检查
"""

from __future__ import annotations

from peer_review.graph.state import ReviewState
import peer_review.llm_client as llm_client
from peer_review.platform.decision_engine import DecisionContext, DecisionEngine
from peer_review.platform.knowledge_hub import KnowledgeHub
from peer_review.platform.routing_plan_engine import RoutingPlanEngine
from rich.console import Console

console = Console()


def make_primary_node(routing_engine: RoutingPlanEngine, knowledge_hub: KnowledgeHub):
    """创建主专家 LangGraph 节点函数"""

    def primary_node(state: ReviewState) -> ReviewState:
        case_context = state.get("case_context", "")
        model_cfg = routing_engine.get_model_for_node("primary_expert")

        # 知识检索（使用 debt-lawyer 专家知识库）
        retrieved = knowledge_hub.search("debt-lawyer", case_context, top_k=5)
        knowledge_context = "\n".join(retrieved) if retrieved else "（知识库当前未返回有效内容）"
        if retrieved:
            console.print(f"[dim]📚 知识检索命中 {len(retrieved)} 条（debt-lawyer）[/dim]")

        # 铁闸检查
        engine = DecisionEngine()
        decision = engine.decide(
            DecisionContext(case_text=case_context, proposed_strategy="")
        )

        if decision.decision.value == "blocked":
            return {
                "primary_analysis": "[主专家分析被铁闸阻断]\n" + decision.reason,
                "iron_gate_triggered": True,
                "iron_gate_reason": decision.reason,
                "models_used": {"primary_expert": model_cfg.model_id},
            }

        # 调用 LLM 生成主分析
        system_prompt = (
            "你是一位资深债务诉讼律师。基于案件事实与知识库片段，"
            "给出结构化的法律定性、风险评估与初步策略建议。"
        )
        prompt = f"案件事实：\n{case_context}\n\n相关知识库片段：\n{knowledge_context}\n\n请给出主专家分析。"
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

        console.print(f"[dim]🤖 primary_expert 使用模型: {model_cfg.display_name}[/dim]")
        return {
            "primary_analysis": resp.content,
            "iron_gate_triggered": False,
            "iron_gate_reason": "",
            "models_used": {"primary_expert": model_cfg.model_id},
        }

    return primary_node
