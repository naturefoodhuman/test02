# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 14:30:00

"""APC-T056/APC-T059 shadow/soak/release checklist tests."""
from __future__ import annotations

from pathlib import Path

from tests.shadow.camera_mmwave_shadow_harness import run_shadow_fixture


def test_shadow_harness_runs_mock_data_and_never_outputs_red() -> None:
    report = run_shadow_fixture(Path("tests/fixtures/radar_frames.jsonl"))
    data = report.to_dict()

    assert data["total_frames"] >= 1
    assert data["candidate_count"] >= 1
    assert all(candidate.alert_level != "red" for candidate in report.candidates)


def test_locustfile_and_release_checklist_exist() -> None:
    locustfile = Path("tests/soak/locustfile.py").read_text()
    checklist = Path("docs/RELEASE_CHECKLIST_P0.md").read_text()
    e2e_doc = Path("tests/e2e/test_mvp_feeding_roundtrip.md").read_text()

    assert "class ParentingUser" in locustfile
    assert "FCM" in checklist
    assert "Camera vendor cloud disabled" in checklist
    assert "pending_sync=true" in e2e_doc
