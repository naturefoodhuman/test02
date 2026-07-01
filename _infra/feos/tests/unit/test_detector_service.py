# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.case_manager import CaseService
from _infra.feos.detector import DetectorService, DetectorSignals
from _infra.feos.detector.signals import AgentBehaviorSignals, ExecutionFailureSignals
from _infra.feos.models.ids import FEOSIdGenerator
from _infra.feos.repositories import CaseRepository, TimelineRepository
from _infra.feos.storage import FEOSWorkspace


def make_service(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos")
    ws.ensure_initialized()
    return CaseService(CaseRepository(ws), TimelineRepository(ws), FEOSIdGenerator())


def test_hard_trigger_auto_create_case(tmp_path):
    case_service = make_service(tmp_path)
    detector = DetectorService(case_service=case_service)
    decision = detector.evaluate(
        DetectorSignals(execution=ExecutionFailureSignals(repeated_failure_count=2), title="Loop", user_goal="fix repeated error"),
        auto_create=True,
    )
    assert decision.decision == "auto_create_case"
    assert decision.case is not None
    assert decision.case.trigger.escalation_score >= 0
    assert "same_error_repeated_2_times" in decision.hard_triggers


def test_suggest_threshold_and_continue():
    detector = DetectorService()
    suggest = detector.evaluate(DetectorSignals(agent=AgentBehaviorSignals(uncertainty=1.0)))
    assert suggest.decision in {"continue_local", "suggest_case"}
    high = detector.evaluate(DetectorSignals(execution=ExecutionFailureSignals(repeated_failure_count=2)))
    assert high.decision == "auto_create_case"
