# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 01:55:00

"""Backlog patch plan tests."""

from __future__ import annotations

from pathlib import Path

from server.app.ops.backlog_patch_plan import build_backlog_patch_plan, write_backlog_patch_plan
from server.app.ops.closeout_recommendation import (
    APCCloseoutRecommendation,
    APCCloseoutRecommendationReport,
)


def test_backlog_patch_plan_builds_dry_run_change_for_ready_task(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "TASK_BACKLOG.md").write_text(
        """
### APC-T044 — Backup

- **状态**：BLOCKED（真实 pg_dump/NAS/restore drill 待验收）

### APC-T059 — Soak

- **状态**：BLOCKED（真实 7 晚 shadow 与 soak 待验收）
""".strip(),
        encoding="utf-8",
    )
    report = APCCloseoutRecommendationReport(
        status="ready_items_present",
        ready_count=1,
        blocked_count=1,
        recommendations=(
            APCCloseoutRecommendation(
                task_id="APC-T044",
                recommended_status="DONE",
                ready_to_close=True,
                reasons=(),
                dependencies=(),
                backlog_status_line="- **状态**：DONE",
            ),
            APCCloseoutRecommendation(
                task_id="APC-T059",
                recommended_status="BLOCKED",
                ready_to_close=False,
                reasons=("missing evidence",),
                dependencies=(),
                backlog_status_line="- **状态**：BLOCKED（missing evidence）",
            ),
        ),
    )

    plan = build_backlog_patch_plan(project_root=tmp_path, recommendation_report=report)

    assert plan.status == "changes_ready"
    assert plan.changes[0].task_id == "APC-T044"
    assert plan.changes[0].proposed_line == "- **状态**：DONE"
    assert plan.blocked_task_ids == ("APC-T059",)


def test_backlog_patch_plan_writes_json_and_markdown(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "TASK_BACKLOG.md").write_text(
        "### APC-T044 — Backup\n\n- **状态**：DONE\n",
        encoding="utf-8",
    )
    report = APCCloseoutRecommendationReport(
        status="no_ready_items",
        ready_count=0,
        blocked_count=0,
        recommendations=(),
    )
    plan = build_backlog_patch_plan(project_root=tmp_path, recommendation_report=report)
    json_path, md_path = write_backlog_patch_plan(plan, output_dir=tmp_path)

    assert json_path.exists()
    assert md_path.exists()
    assert "APC Backlog Patch Plan" in md_path.read_text(encoding="utf-8")
