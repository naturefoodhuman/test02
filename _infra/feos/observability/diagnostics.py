# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from pathlib import Path

from _infra.feos.models.base import FEOSModel
from _infra.feos.storage import FEOSWorkspace


class CaseDiagnosticReport(FEOSModel):
    case_id: str
    ok: bool
    warnings: list[str]
    errors: list[str]
    checked_paths: list[str]


def diagnose_case(workspace: FEOSWorkspace, case_id: str) -> CaseDiagnosticReport:
    case_dir = workspace.case_dir(case_id)
    errors = []
    warnings = []
    checked = []
    case_yaml = case_dir / "case.yaml"
    timeline = case_dir / "timeline.jsonl"
    for path in [case_yaml, timeline]:
        checked.append(str(path.relative_to(workspace.root)))
        if not path.exists():
            errors.append(f"missing {path.name}")
    for optional in ["exports/clipboard.md", "responses"]:
        path = case_dir / optional
        checked.append(str(path.relative_to(workspace.root)))
        if not path.exists():
            warnings.append(f"missing optional {optional}")
    return CaseDiagnosticReport(case_id=case_id, ok=not errors, warnings=warnings, errors=errors, checked_paths=checked)
