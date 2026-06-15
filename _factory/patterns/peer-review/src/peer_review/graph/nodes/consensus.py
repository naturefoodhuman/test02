# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 02:25:00 CST
"""汇总节点 + 分歧检测

职责：
- 整合主专家分析与各评审意见
- 计算评审间分歧度（基于关键词重叠的简化算法）
- 若分歧超过阈值，标记 requires_human
"""

from __future__ import annotations

from peer_review.graph.state import ReviewState
import peer_review.llm_client as llm_client
from peer_review.platform.routing_plan_engine import RoutingPlanEngine
from rich.console import Console

console = Console()


def _simple_divergence(opinions: list[str]) -> float:
    """简化的分歧度计算：基于关键词重叠

    真实实现应使用向量嵌入相似度；这里先用字符/关键词重叠做快速判断。
    """
    if len(opinions) < 2:
        return 0.0

    # 提取简单关键词集合（去除停用词）
    def keywords(text: str) -> set[str]:
        stopwords = {"的", "是", "了", "和", "在", "有", "我", "他", "她", "你", "它", "我们", "建议", "风险", "注意"}
        words = set()
        for w in text.split():
            w = w.strip("，。！？、；：\"\"''()[]{}【】")
            if len(w) >= 2 and w not in stopwords:
                words.add(w)
        return words

    keyword_sets = [keywords(op) for op in opinions]
    total_overlap = 0.0
    pairs = 0
    for i in range(len(keyword_sets)):
        for j in range(i + 1, len(keyword_sets)):
            union = keyword_sets[i] | keyword_sets[j]
            intersection = keyword_sets[i] & keyword_sets[j]
            if union:
                overlap = len(intersection) / len(union)
                total_overlap += overlap
                pairs += 1

    if pairs == 0:
        return 0.0
    avg_overlap = total_overlap / pairs
    # 分歧度 = 1 - 重叠度，阈值 0.4
    return round(1.0 - avg_overlap, 2)


def make_consensus_node(routing_engine: RoutingPlanEngine):
    """创建汇总节点函数"""

    def consensus_node(state: ReviewState) -> ReviewState:
        primary = state.get("primary_analysis", "")
        opinions = state.get("reviewer_opinions", [])
        roles = state.get("reviewer_roles", [])
        model_cfg = routing_engine.get_model_for_node("consensus")

        divergence = _simple_divergence(opinions)
        threshold = 0.4
        requires_human = divergence > threshold

        # 构建汇总提示
        review_text = ""
        for role, opinion in zip(roles, opinions):
            review_text += f"\n--- {role} ---\n{opinion}\n"

        system_prompt = (
            "你是一位高级债务案件策略总监。整合主专家分析与各评审独立意见，"
            "形成最终共识报告，并标注分歧点与需要人工复核的争议。"
        )
        prompt = (
            f"主专家分析：\n{primary}\n"
            f"各评审独立意见：\n{review_text}\n"
            f"分歧度（0-1）：{divergence}\n\n"
            "请给出最终汇总结论。"
        )
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

        console.print(f"[dim]🤖 consensus 使用模型: {model_cfg.display_name}[/dim]")
        return {
            "consensus": resp.content,
            "divergence_score": divergence,
            "requires_human": requires_human,
            "models_used": {"consensus": model_cfg.model_id},
        }

    return consensus_node
