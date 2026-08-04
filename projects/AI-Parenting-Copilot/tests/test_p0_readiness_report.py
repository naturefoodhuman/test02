# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 21:45:00

"""P0 readiness aggregate report tests."""

from __future__ import annotations

from pathlib import Path

from server.app.ops.p0_readiness import build_p0_readiness_report


def test_p0_readiness_report_passes_automated_checks_and_lists_external_blockers() -> None:
    report = build_p0_readiness_report(Path("."))

    assert report.automated_status == "ready_for_external_validation"
    assert all(status == "ok" for status in report.automated_checks.values())
    assert any("APC-T022" in blocker for blocker in report.external_blockers)
    assert any("seven-night" in blocker for blocker in report.external_blockers)
    assert "make android-e2e-contract" in report.next_commands
    assert "make shadow-test" in report.next_commands
