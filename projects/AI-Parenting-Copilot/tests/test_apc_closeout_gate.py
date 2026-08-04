# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 23:45:00

"""APC closeout gate tests."""

from __future__ import annotations

import json
from pathlib import Path

from server.app.ops.apc_closeout import build_apc_closeout_gate_report
from server.app.ops.external_evidence import ExternalValidationEvidence, build_evidence_template
from server.app.rule_engine.review_signoff import build_signoff_template


def test_closeout_gate_lists_remaining_tasks_as_blocked_without_artifacts(tmp_path: Path) -> None:
    report = build_apc_closeout_gate_report(signoff_dir=tmp_path / "s", evidence_dir=tmp_path / "e")

    assert report.status == "blocked"
    assert {task.task_id for task in report.tasks} == {
        "APC-T022",
        "APC-T023",
        "APC-T030",
        "APC-T036",
        "APC-T038",
        "APC-T039",
        "APC-T040",
        "APC-T041",
        "APC-T044",
        "APC-T059",
    }
    assert all(task.status == "blocked" for task in report.tasks)


def test_closeout_gate_accepts_valid_external_evidence_for_backup_task(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    template = build_evidence_template("APC-T044")
    evidence = ExternalValidationEvidence(
        task_id="APC-T044",
        status="passed",
        operator="operator-1",
        completed_at="2026-08-04T23:45:00+08:00",
        evidence={key: f"artifact://{key}" for key in template.evidence},
    )
    (evidence_dir / "apc-t044.json").write_text(evidence.to_json(), encoding="utf-8")

    report = build_apc_closeout_gate_report(signoff_dir=tmp_path / "s", evidence_dir=evidence_dir)
    task = next(item for item in report.tasks if item.task_id == "APC-T044")

    assert task.status == "ready_to_close"
    assert task.reasons == ()


def test_closeout_gate_requires_production_rule_signoff_not_dev_shadow(tmp_path: Path) -> None:
    signoff_dir = tmp_path / "signoffs"
    signoff_dir.mkdir()
    template = build_signoff_template("vaccine", scope="dev_shadow")
    dev_shadow = template.__class__(
        **{
            **template.to_dict(),
            "status": "approved",
            "reviewer": "reviewer-1",
            "reviewed_at": "2026-08-04T23:45:00+08:00",
            "checklist": {key: True for key in template.checklist},
        }
    )
    (signoff_dir / "vaccine.json").write_text(
        json.dumps(dev_shadow.to_dict(), ensure_ascii=False),
        encoding="utf-8",
    )

    report = build_apc_closeout_gate_report(signoff_dir=signoff_dir, evidence_dir=tmp_path / "e")
    task = next(item for item in report.tasks if item.task_id == "APC-T022")

    assert task.status == "blocked"
    assert any("production rule signoff" in reason for reason in task.reasons)
