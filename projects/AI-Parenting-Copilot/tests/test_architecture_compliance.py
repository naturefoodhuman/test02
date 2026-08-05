# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 02:20:00

"""Architecture compliance audit tests."""

from __future__ import annotations

from pathlib import Path

from server.app.ops.architecture_compliance import (
    build_architecture_compliance_report,
    write_architecture_compliance_report,
)


def test_architecture_compliance_report_passes_with_external_blockers() -> None:
    report = build_architecture_compliance_report(Path("."))

    assert report.status == "pass_with_external_blockers"
    checks = {check.check_id: check for check in report.checks}
    assert checks["ARCH-001"].status == "pass"
    assert checks["ARCH-003"].status == "pass"
    assert checks["ARCH-005"].status == "pass"
    assert checks["ARCH-007"].status == "pass"
    assert len(report.external_blockers) >= 10


def test_architecture_compliance_report_writes_json_and_markdown(tmp_path: Path) -> None:
    report = build_architecture_compliance_report(Path("."))
    json_path, md_path = write_architecture_compliance_report(report, output_dir=tmp_path)

    assert json_path.exists()
    assert md_path.exists()
    assert "Architecture Compliance Audit" in md_path.read_text(encoding="utf-8")
