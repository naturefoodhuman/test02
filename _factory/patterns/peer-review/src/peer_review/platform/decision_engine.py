# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 01:50:00 CST
"""DecisionEngine: 分层决策引擎

职责：
- 层1 铁闸：硬编码规则，100% 确定性，不可 AI 化
- 层2 AI 参考：本地模型风险评分
- 层3 AI 生成：基于评分决定生成策略

在 LangGraph 图中作为独立节点调用。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DecisionType(str, Enum):
    BLOCKED = "blocked"
    APPROVED = "approved"
    REQUIRES_REVIEW = "requires_review"


@dataclass
class DecisionContext:
    """决策上下文"""

    case_text: str = ""
    proposed_strategy: str = ""
    sensitive_fields: list[str] | None = None


@dataclass
class Decision:
    """决策结果"""

    decision: DecisionType
    reason: str = ""
    ai_score: float = 0.0


class DecisionEngine:
    """分层决策引擎"""

    IRON_GATE_RULES: list[dict[str, Any]] = [
        {
            "name": "禁止暴力催收",
            "pattern": ["上门堵人", "非法拘禁", "跟踪", "骚扰", "威胁", "恐吓"],
            "reason": "存在暴力催收或软暴力嫌疑，违反法律红线，必须人工复核",
        },
        {
            "name": "禁止泄露隐私",
            "pattern": ["公开债务人信息", "发朋友圈", "贴大字报", "群发通讯录"],
            "reason": "涉嫌侵犯隐私权/名誉权，必须人工复核",
        },
        {
            "name": "禁止伪造证据",
            "pattern": ["伪造借条", "伪造转账记录", "P图", "假合同"],
            "reason": "涉嫌伪造证据/虚假诉讼，必须人工复核",
        },
    ]

    def __init__(self, llm_client: Any | None = None):
        self.llm_client = llm_client

    def decide(self, context: DecisionContext) -> Decision:
        """三层决策入口"""
        # 层1：铁闸
        gate = self._iron_gate_check(context)
        if gate.decision == DecisionType.BLOCKED:
            return gate

        # 层2：AI 参考（本地模型风险评分）
        ai_score = self._ai_reference(context)

        # 层3：AI 生成决策
        return self._ai_generate(context, ai_score)

    def _iron_gate_check(self, context: DecisionContext) -> Decision:
        """铁闸层：硬编码规则，不依赖 LLM"""
        text = (context.case_text or "") + " " + (context.proposed_strategy or "")
        text_lower = text.lower()
        for rule in self.IRON_GATE_RULES:
            for keyword in rule["pattern"]:
                if keyword.lower() in text_lower:
                    return Decision(
                        decision=DecisionType.BLOCKED,
                        reason=f"铁闸规则触发：{rule['name']} - {rule['reason']}",
                    )
        return Decision(decision=DecisionType.APPROVED, reason="铁闸通过")

    def _ai_reference(self, context: DecisionContext) -> float:
        """AI 参考层：风险评分 0-1（当前为简单启发式，后续可接入本地模型）"""
        score = 0.0
        text = (context.case_text or "") + " " + (context.proposed_strategy or "")
        # 简单关键词风险评分
        risk_keywords = ["诉讼", "执行", "保全", "仲裁", "律师函"]
        for kw in risk_keywords:
            if kw in text:
                score += 0.1
        return min(score, 1.0)

    def _ai_generate(self, context: DecisionContext, ai_score: float) -> Decision:
        """AI 生成层：基于评分决定策略"""
        if ai_score > 0.7:
            return Decision(
                decision=DecisionType.REQUIRES_REVIEW,
                reason=f"AI 风险评分较高 ({ai_score:.2f})，建议人工复核",
                ai_score=ai_score,
            )
        return Decision(
            decision=DecisionType.APPROVED,
            reason=f"AI 风险评分正常 ({ai_score:.2f})",
            ai_score=ai_score,
        )
