# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 21:22:00

"""Deployment readiness report tests for APC-T054."""

from __future__ import annotations

from pathlib import Path

from server.app.ops.deployment_readiness import build_deployment_readiness_report


def test_deployment_readiness_report_passes() -> None:
    report = build_deployment_readiness_report(Path("."))

    assert report.ok is True
    assert report.checks["make_target:run-api"] == "ok"
    assert report.checks["make_target:launchd-validate"] == "ok"
    assert report.checks["launchd:com.parenting.server"] == "ok"
    assert report.checks["launchd:com.parenting.backup"] == "ok"
    assert report.checks["runbook_run_api"] == "ok"
    assert report.checks["runbook_runtime_logs"] == "ok"
