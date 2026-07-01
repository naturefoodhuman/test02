# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.evidence.collectors import AgentPlanCollector, PreviousAttemptCollector, UserInputCollector
from _infra.feos.ports.collectors import EvidenceCollectionRequest


def test_user_previous_agent_collectors():
    req = EvidenceCollectionRequest(case_id="case_001", user_input="goal", previous_attempts=["try 1"], agent_plan="plan")
    assert UserInputCollector().collect(req)[0].evidence_type == "user_input"
    assert PreviousAttemptCollector().collect(req)[0].evidence_type == "previous_attempt"
    assert AgentPlanCollector().collect(req)[0].origin == "agent_behavior"


def test_empty_inputs_are_skipped():
    req = EvidenceCollectionRequest(case_id="case_001")
    assert UserInputCollector().can_collect(req) is False
    assert PreviousAttemptCollector().can_collect(req) is False
    assert AgentPlanCollector().can_collect(req) is False
