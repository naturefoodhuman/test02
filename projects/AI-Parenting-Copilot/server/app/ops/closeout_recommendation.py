# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 23:58:00

"""Backlog closeout recommendation renderer.

This module consumes APC closeout gate reports and produces reviewable recommendations
for task-status changes. It intentionally does not edit TASK_BACKLOG.md directly;
that prevents accidental closure of externally validated tasks without human review.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from server.app.ops.apc_closeout import (
    APCCloseoutGateReport,
    APCCloseoutTaskResult,
    build_apc_closeout_gate_report,
)


@dataclass(frozen=True, slots=True)
class APCCloseoutRecommendation:
    task_id: str
    recommended_status: str
    ready_to_close: bool
    reasons: tuple[str, ...]
    dependencies: tuple[str, ...]
    backlog_status_line: str


@dataclass(frozen=True, slots=True)
class APCCloseoutRecommendationReport:
    status: str
    ready_count: int
    blocked_count: int
    recommendations: tuple[APCCloseoutRecommendation, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            "# APC Closeout Recommendations",
            "",
            f"- Status: `{self.status}`",
            f"- Ready to close: `{self.ready_count}`",
            f"- Still blocked: `{self.blocked_count}`",
            "",
            "This report is advisory. It does not edit TASK_BACKLOG.md automatically.",
            "",
        ]
        for item in self.recommendations:
            lines.extend(
                [
                    f"## {item.task_id}",
                    "",
                    f"- Recommended status: `{item.recommended_status}`",
                    f"- Ready to close: `{str(item.ready_to_close).lower()}`",
                    f"- Suggested status line: `{item.backlog_status_line}`",
                ]
            )
            if item.dependencies:
                lines.append(f"- Dependencies: {', '.join(item.dependencies)}")
            if item.reasons:
                lines.append("- Remaining reasons:")
                lines.extend(f"  - {reason}" for reason in item.reasons)
            lines.append("")
        return "\n".join(lines)


def build_closeout_recommendation_report(
    *,
    closeout_report: APCCloseoutGateReport | None = None,
    project_root: Path | str = ".",
    signoff_dir: Path | str = "runtime/reports/rule-signoffs",
    evidence_dir: Path | str = "runtime/reports/external-evidence",
) -> APCCloseoutRecommendationReport:
    report = closeout_report or build_apc_closeout_gate_report(
        project_root=project_root,
        signoff_dir=signoff_dir,
        evidence_dir=evidence_dir,
    )
    recommendations = tuple(_recommendation(task) for task in report.tasks)
    ready_count = sum(1 for item in recommendations if item.ready_to_close)
    blocked_count = len(recommendations) - ready_count
    return APCCloseoutRecommendationReport(
        status="ready_items_present" if ready_count else "no_ready_items",
        ready_count=ready_count,
        blocked_count=blocked_count,
        recommendations=recommendations,
    )


def write_closeout_recommendation_report(
    report: APCCloseoutRecommendationReport,
    *,
    output_dir: Path | str = "runtime/reports",
) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "apc-closeout-recommendations.json"
    md_path = output / "apc-closeout-recommendations.md"
    json_path.write_text(report.to_json(), encoding="utf-8")
    md_path.write_text(report.to_markdown(), encoding="utf-8")
    return json_path, md_path


def _recommendation(task: APCCloseoutTaskResult) -> APCCloseoutRecommendation:
    ready = task.status == "ready_to_close"
    recommended_status = "DONE" if ready else "BLOCKED"
    if ready:
        status_line = "- **状态**：DONE"
    else:
        reason = "; ".join(task.reasons) if task.reasons else "external validation pending"
        status_line = f"- **状态**：BLOCKED（{reason}）"
    return APCCloseoutRecommendation(
        task_id=task.task_id,
        recommended_status=recommended_status,
        ready_to_close=ready,
        reasons=task.reasons,
        dependencies=task.dependencies,
        backlog_status_line=status_line,
    )
