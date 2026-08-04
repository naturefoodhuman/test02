# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 23:58:00

"""APC closeout recommendation report tests."""

from __future__ import annotations

from pathlib import Path

from server.app.ops.apc_closeout import APCCloseoutGateReport, APCCloseoutTaskResult
from server.app.ops.closeout_recommendation import (
    build_closeout_recommendation_report,
    write_closeout_recommendation_report,
)


def test_closeout_recommendations_render_done_and_blocked_lines() -> None:
    gate = APCCloseoutGateReport(
        status="blocked",
        signoff_count=0,
        evidence_count=1,
        tasks=(
            APCCloseoutTaskResult(task_id="APC-T044", status="ready_to_close"),
            APCCloseoutTaskResult(
                task_id="APC-T059",
                status="blocked",
                reasons=("missing external evidence for APC-T059",),
                dependencies=("APC-T039",),
            ),
        ),
    )

    report = build_closeout_recommendation_report(closeout_report=gate)

    assert report.status == "ready_items_present"
    assert report.ready_count == 1
    assert report.blocked_count == 1
    ready = report.recommendations[0]
    blocked = report.recommendations[1]
    assert ready.backlog_status_line == "- **状态**：DONE"
    assert blocked.recommended_status == "BLOCKED"
    assert "missing external evidence" in blocked.backlog_status_line


def test_closeout_recommendations_write_json_and_markdown(tmp_path: Path) -> None:
    report = build_closeout_recommendation_report(
        closeout_report=APCCloseoutGateReport(
            status="blocked",
            signoff_count=0,
            evidence_count=0,
            tasks=(
                APCCloseoutTaskResult(
                    task_id="APC-T022",
                    status="blocked",
                    reasons=("missing production rule signoff for vaccine",),
                ),
            ),
        )
    )

    json_path, md_path = write_closeout_recommendation_report(report, output_dir=tmp_path)

    assert json_path.exists()
    assert md_path.exists()
    assert "APC Closeout Recommendations" in md_path.read_text(encoding="utf-8")
