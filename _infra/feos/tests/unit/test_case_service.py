# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import pytest

from _infra.feos.case_manager import CaseService, CreateCaseInput, StateTransitionError
from _infra.feos.models.ids import FEOSIdGenerator
from _infra.feos.repositories import CaseRepository, TimelineRepository
from _infra.feos.storage import FEOSWorkspace


def make_service(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos")
    ws.ensure_initialized()
    return CaseService(CaseRepository(ws), TimelineRepository(ws), FEOSIdGenerator()), ws


def test_create_case_writes_case_and_timeline(tmp_path):
    service, ws = make_service(tmp_path)
    case = service.create_case(CreateCaseInput(title="test", user_goal="debug", actor="tester"))
    assert (ws.case_dir(case.id) / "case.yaml").exists()
    events = TimelineRepository(ws).list(case.id)
    assert events[0].type == "case_created"
    assert events[0].actor == "tester"


def test_transition_case_and_list(tmp_path):
    service, _ = make_service(tmp_path)
    case = service.create_case(CreateCaseInput(title="test", user_goal="debug"))
    updated = service.transition_case(case.id, "CollectingEvidence", actor="tester")
    assert updated.status == "CollectingEvidence"
    assert service.list_cases()[0].id == case.id


def test_illegal_transition_does_not_modify_case(tmp_path):
    service, _ = make_service(tmp_path)
    case = service.create_case(CreateCaseInput(title="test", user_goal="debug"))
    with pytest.raises(StateTransitionError):
        service.transition_case(case.id, "Executing")
    assert service.get_case(case.id).status == "Created"
