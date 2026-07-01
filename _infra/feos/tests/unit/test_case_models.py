# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from _infra.feos.models import AuditRecord, CaseProblem, EscalationCase, TimelineEvent


def make_case() -> EscalationCase:
    return EscalationCase(
        id="case_2026_07_01_001",
        title="Schema validation failure",
        problem=CaseProblem(user_goal="fix tool call", actual_behavior="ValidationError"),
    )


def test_case_yaml_round_trip():
    case = make_case()
    loaded = EscalationCase.from_yaml_text(case.to_yaml_text())
    assert loaded.id == case.id
    assert loaded.status == "Draft"
    assert loaded.problem.user_goal == "fix tool call"


def test_case_missing_required_field_fails():
    with pytest.raises(ValidationError):
        EscalationCase(id="case_1", title="missing problem")


def test_timeline_json_line_serialization():
    event = TimelineEvent(id="evt_001", case_id="case_001", type="created", summary="case created")
    data = json.loads(event.to_json_line())
    assert data["case_id"] == "case_001"
    assert data["timestamp"].endswith("Z")


def test_audit_record_serialization():
    record = AuditRecord(id="audit_001", case_id="case_001", operation="clipboard_export", content_hash="sha256:abc")
    loaded = AuditRecord.from_yaml_text(record.to_yaml_text())
    assert loaded.operation == "clipboard_export"
    assert loaded.content_hash == "sha256:abc"
