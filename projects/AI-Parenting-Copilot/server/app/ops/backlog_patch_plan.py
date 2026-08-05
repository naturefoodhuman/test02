# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 01:55:00

"""Backlog patch plan generator for APC closeout recommendations.

This module creates a safe dry-run patch plan from closeout recommendations. It does
not edit TASK_BACKLOG.md; it shows exactly which task status lines would change once
external evidence has been reviewed.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from server.app.ops.closeout_recommendation import (
    APCCloseoutRecommendationReport,
    build_closeout_recommendation_report,
)


@dataclass(frozen=True, slots=True)
class BacklogPatchChange:
    task_id: str
    current_line: str
    proposed_line: str


@dataclass(frozen=True, slots=True)
class BacklogPatchPlan:
    status: str
    task_backlog_path: str
    changes: tuple[BacklogPatchChange, ...] = field(default_factory=tuple)
    blocked_task_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            "# APC Backlog Patch Plan",
            "",
            f"- Status: `{self.status}`",
            f"- Target: `{self.task_backlog_path}`",
            f"- Proposed changes: `{len(self.changes)}`",
            "",
        ]
        if self.changes:
            for change in self.changes:
                lines.extend(
                    [
                        f"## {change.task_id}",
                        "",
                        "```diff",
                        f"- {change.current_line}",
                        f"+ {change.proposed_line}",
                        "```",
                        "",
                    ]
                )
        else:
            lines.append("No tasks are ready to close based on current evidence/signoff artifacts.")
            lines.append("")
        if self.blocked_task_ids:
            lines.append("## Still blocked")
            lines.append("")
            for task_id in self.blocked_task_ids:
                lines.append(f"- `{task_id}`")
            lines.append("")
        return "\n".join(lines)


def build_backlog_patch_plan(
    *,
    project_root: Path | str = ".",
    recommendation_report: APCCloseoutRecommendationReport | None = None,
    task_backlog_path: Path | str = "docs/TASK_BACKLOG.md",
) -> BacklogPatchPlan:
    root = Path(project_root)
    backlog_path = root / task_backlog_path
    backlog_text = backlog_path.read_text(encoding="utf-8")
    report = recommendation_report or build_closeout_recommendation_report(project_root=root)
    changes: list[BacklogPatchChange] = []
    blocked_task_ids: list[str] = []
    for recommendation in report.recommendations:
        if not recommendation.ready_to_close:
            blocked_task_ids.append(recommendation.task_id)
            continue
        current_line = _find_task_status_line(backlog_text, recommendation.task_id)
        if current_line is None:
            blocked_task_ids.append(recommendation.task_id)
            continue
        if current_line.strip() != recommendation.backlog_status_line:
            changes.append(
                BacklogPatchChange(
                    task_id=recommendation.task_id,
                    current_line=current_line,
                    proposed_line=recommendation.backlog_status_line,
                )
            )
    status = "changes_ready" if changes else "no_changes_ready"
    return BacklogPatchPlan(
        status=status,
        task_backlog_path=str(task_backlog_path),
        changes=tuple(changes),
        blocked_task_ids=tuple(blocked_task_ids),
    )


def write_backlog_patch_plan(
    plan: BacklogPatchPlan,
    *,
    output_dir: Path | str = "runtime/reports",
) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "apc-backlog-patch-plan.json"
    md_path = output / "apc-backlog-patch-plan.md"
    json_path.write_text(plan.to_json(), encoding="utf-8")
    md_path.write_text(plan.to_markdown(), encoding="utf-8")
    return json_path, md_path


def _find_task_status_line(backlog_text: str, task_id: str) -> str | None:
    marker = f"### {task_id}"
    start = backlog_text.find(marker)
    if start < 0:
        return None
    next_task = backlog_text.find("\n### APC-", start + len(marker))
    section = backlog_text[start:] if next_task < 0 else backlog_text[start:next_task]
    for line in section.splitlines():
        if line.startswith("- **状态**："):
            return line
    return None
