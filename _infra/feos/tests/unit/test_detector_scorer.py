# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.detector import DEFAULT_WEIGHTS, DetectorSignals, EscalationScorer
from _infra.feos.detector.signals import AgentBehaviorSignals, ContextHealthSignals, ExecutionFailureSignals, TaskMetadataSignals


def test_weights_sum_to_one():
    assert round(sum(DEFAULT_WEIGHTS.values()), 6) == 1.0


def test_high_repeated_failure_scores_above_auto_threshold():
    signals = DetectorSignals(
        execution=ExecutionFailureSignals(repeated_failure_count=2, same_error_repeated=True, error_stability=1.0),
        agent=AgentBehaviorSignals(uncertainty=0.9),
        context=ContextHealthSignals(context_pollution=0.6),
        task=TaskMetadataSignals(task_complexity=0.8, missing_knowledge=0.8, user_priority=1.0),
    )
    result = EscalationScorer().score(signals)
    assert result.score > 0.70
    assert result.explanation["repeated_failure"] == 0.25
    assert result.reasons


def test_low_risk_scores_below_continue_threshold():
    result = EscalationScorer().score(DetectorSignals())
    assert result.score < 0.50
