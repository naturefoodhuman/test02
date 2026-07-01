# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import pytest

from _infra.feos.errors import FEOSStorageError
from _infra.feos.models import CaseProblem, EscalationCase, TimelineEvent
from _infra.feos.repositories import CaseRepository, TimelineRepository
from _infra.feos.storage import FEOSWorkspace, write_yaml


def test_case_repository_create_get_list(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos")
    ws.ensure_initialized()
    repo = CaseRepository(ws)
    case = EscalationCase(id="case_2026_07_01_001", title="test", problem=CaseProblem(user_goal="debug"))
    repo.save(case)
    assert repo.get(case.id).title == "test"
    assert [c.id for c in repo.list()] == [case.id]


def test_case_id_directory_mismatch_fails(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos")
    ws.ensure_initialized()
    bad_dir = ws.case_dir("case_2026_07_01_001")
    write_yaml(bad_dir / "case.yaml", EscalationCase(id="case_2026_07_01_999", title="bad", problem=CaseProblem(user_goal="x")).to_dict())
    with pytest.raises(FEOSStorageError):
        CaseRepository(ws).get("case_2026_07_01_001")


def test_corrupt_yaml_reports_error(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos")
    ws.ensure_initialized()
    path = ws.case_dir("case_2026_07_01_001") / "case.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("bad: [", encoding="utf-8")
    with pytest.raises(FEOSStorageError):
        CaseRepository(ws).get("case_2026_07_01_001")


def test_timeline_append_and_list(tmp_path):
    ws = FEOSWorkspace(tmp_path / "feos")
    ws.ensure_initialized()
    repo = TimelineRepository(ws)
    event = TimelineEvent(id="evt_001", case_id="case_001", type="created")
    repo.append(event)
    repo.append(TimelineEvent(id="evt_002", case_id="case_001", type="updated"))
    assert [e.id for e in repo.list("case_001")] == ["evt_001", "evt_002"]
