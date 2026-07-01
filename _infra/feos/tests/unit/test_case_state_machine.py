# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import pytest

from _infra.feos.case_manager import CaseStateMachine, StateTransitionError
from _infra.feos.models.enums import CaseStatus


def test_main_path_transitions_allowed():
    sm = CaseStateMachine()
    path = sm.main_path()
    for current, target in zip(path, path[1:]):
        context = {"evidence_count": 1, "policy_allowed": True, "approved_plan": True}
        assert sm.can_transition(current, target, context=context)


def test_illegal_jump_rejected():
    with pytest.raises(StateTransitionError):
        CaseStateMachine().validate(CaseStatus.CREATED, CaseStatus.EXECUTING)


def test_archived_cannot_transition():
    with pytest.raises(StateTransitionError):
        CaseStateMachine().validate(CaseStatus.ARCHIVED, CaseStatus.CREATED)


def test_guard_failure_rejected():
    with pytest.raises(StateTransitionError, match="evidence_count"):
        CaseStateMachine().validate(CaseStatus.COLLECTING_EVIDENCE, CaseStatus.GRAPH_BUILDING, context={"evidence_count": 0})
