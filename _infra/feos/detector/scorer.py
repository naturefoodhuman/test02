# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Escalation score computation."""

from __future__ import annotations

from pydantic import Field

from _infra.feos.models.base import FEOSModel

from .signals import DetectorSignals

DEFAULT_WEIGHTS = {
    "repeated_failure": 0.25,
    "uncertainty": 0.20,
    "error_stability": 0.15,
    "task_complexity": 0.15,
    "context_pollution": 0.10,
    "missing_knowledge": 0.10,
    "user_priority": 0.05,
}


class DetectorResult(FEOSModel):
    score: float = Field(..., ge=0.0, le=1.0)
    explanation: dict[str, float]
    reasons: list[str] = Field(default_factory=list)


class EscalationScorer:
    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or DEFAULT_WEIGHTS

    def score(self, signals: DetectorSignals) -> DetectorResult:
        repeated_failure = min(1.0, signals.execution.repeated_failure_count / 2.0)
        uncertainty = signals.agent.uncertainty
        error_stability = signals.execution.error_stability if signals.execution.same_error_repeated else min(signals.execution.error_stability, 0.5)
        task_complexity = signals.task.task_complexity
        context_pollution = max(signals.context.context_pollution, min(1.0, signals.context.unresolved_assumption_count / 5.0))
        missing_knowledge = signals.task.missing_knowledge
        user_priority = signals.task.user_priority
        raw = {
            "repeated_failure": repeated_failure,
            "uncertainty": uncertainty,
            "error_stability": error_stability,
            "task_complexity": task_complexity,
            "context_pollution": context_pollution,
            "missing_knowledge": missing_knowledge,
            "user_priority": user_priority,
        }
        explanation = {name: round(raw[name] * self.weights[name], 4) for name in self.weights}
        total = max(0.0, min(1.0, sum(explanation.values())))
        reasons = [f"{name}={value:.3f}" for name, value in explanation.items() if value > 0]
        return DetectorResult(score=round(total, 4), explanation=explanation, reasons=reasons)
