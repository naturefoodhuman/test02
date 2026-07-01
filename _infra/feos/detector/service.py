# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""DetectorService integrates score, hard triggers and optional case creation."""

from __future__ import annotations

from pydantic import Field

from _infra.feos.case_manager import CaseService, CreateCaseInput
from _infra.feos.models import EscalationCase
from _infra.feos.models.base import FEOSModel
from _infra.feos.models.case import CaseTrigger

from .hard_triggers import detect_hard_triggers
from .scorer import DetectorResult, EscalationScorer
from .signals import DetectorSignals


class DetectorDecision(FEOSModel):
    decision: str
    score: float
    score_result: DetectorResult
    hard_triggers: list[str] = Field(default_factory=list)
    case: EscalationCase | None = None


class DetectorService:
    def __init__(
        self,
        case_service: CaseService | None = None,
        scorer: EscalationScorer | None = None,
        auto_create_threshold: float = 0.70,
        suggest_threshold: float = 0.50,
    ):
        self.case_service = case_service
        self.scorer = scorer or EscalationScorer()
        self.auto_create_threshold = auto_create_threshold
        self.suggest_threshold = suggest_threshold

    def evaluate(self, signals: DetectorSignals, auto_create: bool = False) -> DetectorDecision:
        score_result = self.scorer.score(signals)
        hard_triggers = detect_hard_triggers(signals)
        if hard_triggers or score_result.score >= self.auto_create_threshold:
            decision = "auto_create_case"
        elif score_result.score >= self.suggest_threshold:
            decision = "suggest_case"
        else:
            decision = "continue_local"

        case = None
        if auto_create and decision == "auto_create_case" and self.case_service is not None:
            case = self.case_service.create_case(CreateCaseInput(title=signals.title, user_goal=signals.user_goal, actor="feos.detector"))
            case.trigger = CaseTrigger(
                type="hard_trigger" if hard_triggers else "score_threshold",
                attempts=signals.execution.repeated_failure_count,
                local_confidence=max(0.0, min(1.0, 1.0 - signals.agent.uncertainty)),
                escalation_score=score_result.score,
                reason=", ".join(hard_triggers or score_result.reasons),
            )
            self.case_service.case_repository.save(case)
        return DetectorDecision(
            decision=decision,
            score=score_result.score,
            score_result=score_result,
            hard_triggers=hard_triggers,
            case=case,
        )
