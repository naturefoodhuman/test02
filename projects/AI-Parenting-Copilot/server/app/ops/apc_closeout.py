# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 23:45:00

"""APC closeout gate for remaining BLOCKED tasks.

The gate reads rule sign-off artifacts and external validation evidence files, then
reports which remaining APC tasks are ready to close. It does not modify backlog
state; a human/agent still reviews the report and updates docs in a separate change.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from server.app.ops.external_evidence import (
    ExternalEvidenceValidationResult,
    load_evidence_file,
    validate_external_evidence,
)
from server.app.rule_engine.review_signoff import (
    RuleReviewSignoffResult,
    load_signoff_file,
    validate_rule_signoff,
)

REMAINING_TASKS = (
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
)

EVIDENCE_TASKS = {
    "APC-T030",
    "APC-T036",
    "APC-T038",
    "APC-T039",
    "APC-T040",
    "APC-T041",
    "APC-T044",
    "APC-T059",
}


@dataclass(frozen=True, slots=True)
class APCCloseoutTaskResult:
    task_id: str
    status: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
    dependencies: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class APCCloseoutGateReport:
    status: str
    tasks: tuple[APCCloseoutTaskResult, ...]
    signoff_count: int
    evidence_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def build_apc_closeout_gate_report(
    *,
    project_root: Path | str = ".",
    signoff_dir: Path | str = "runtime/reports/rule-signoffs",
    evidence_dir: Path | str = "runtime/reports/external-evidence",
) -> APCCloseoutGateReport:
    root = Path(project_root)
    signoffs = _load_signoffs(root, root / signoff_dir)
    evidence = _load_evidence(root / evidence_dir)
    results = tuple(_task_result(task_id, signoffs, evidence) for task_id in REMAINING_TASKS)
    status = (
        "all_ready"
        if all(result.status == "ready_to_close" for result in results)
        else "blocked"
    )
    return APCCloseoutGateReport(
        status=status,
        tasks=results,
        signoff_count=len(signoffs),
        evidence_count=len(evidence),
    )


def _task_result(
    task_id: str,
    signoffs: dict[str, RuleReviewSignoffResult],
    evidence: dict[str, ExternalEvidenceValidationResult],
) -> APCCloseoutTaskResult:
    reasons: list[str] = []
    dependencies: list[str] = []
    if task_id == "APC-T022":
        _require_rule_signoff("vaccine", signoffs, reasons)
    elif task_id == "APC-T023":
        _require_rule_signoff("growth", signoffs, reasons)
    elif task_id == "APC-T030":
        dependencies.extend(["APC-T022", "APC-T023"])
        _require_rule_signoff("vaccine", signoffs, reasons)
        _require_rule_signoff("growth", signoffs, reasons)
        _require_evidence(task_id, evidence, reasons)
    elif task_id == "APC-T036":
        dependencies.append("APC-T022")
        _require_rule_signoff("vaccine", signoffs, reasons)
        _require_evidence(task_id, evidence, reasons)
    elif task_id in EVIDENCE_TASKS:
        _require_evidence(task_id, evidence, reasons)
        if task_id == "APC-T059":
            dependencies.extend(["APC-T039", "APC-T054", "APC-T057", "APC-T058"])
    else:
        reasons.append("no closeout rule defined")
    return APCCloseoutTaskResult(
        task_id=task_id,
        status="ready_to_close" if not reasons else "blocked",
        reasons=tuple(reasons),
        dependencies=tuple(dependencies),
    )


def _require_rule_signoff(
    domain: str,
    signoffs: dict[str, RuleReviewSignoffResult],
    reasons: list[str],
) -> None:
    result = signoffs.get(domain)
    if result is None:
        reasons.append(f"missing production rule signoff for {domain}")
        return
    if result.scope != "production" or not result.ok:
        reasons.append(f"production rule signoff not accepted for {domain}: {result.errors}")


def _require_evidence(
    task_id: str,
    evidence: dict[str, ExternalEvidenceValidationResult],
    reasons: list[str],
) -> None:
    result = evidence.get(task_id)
    if result is None:
        reasons.append(f"missing external evidence for {task_id}")
        return
    if not result.ok:
        reasons.append(f"external evidence not accepted for {task_id}: {result.errors}")


def _load_signoffs(
    project_root: Path,
    signoff_dir: Path,
) -> dict[str, RuleReviewSignoffResult]:
    results: dict[str, RuleReviewSignoffResult] = {}
    if not signoff_dir.exists():
        return results
    for path in sorted(signoff_dir.glob("*.json")):
        try:
            signoff = load_signoff_file(path)
            results[signoff.domain] = validate_rule_signoff(signoff, project_root=project_root)
        except Exception as exc:
            domain = path.stem.split("-")[0]
            results[domain] = RuleReviewSignoffResult(
                ok=False,
                domain=domain,
                scope="unknown",
                pack_hash="",
                errors=(f"signoff load failed: {exc}",),
            )
    return results


def _load_evidence(evidence_dir: Path) -> dict[str, ExternalEvidenceValidationResult]:
    results: dict[str, ExternalEvidenceValidationResult] = {}
    if not evidence_dir.exists():
        return results
    for path in sorted(evidence_dir.glob("*.json")):
        try:
            evidence = load_evidence_file(path)
            results[evidence.task_id] = validate_external_evidence(evidence)
        except Exception as exc:
            task_id = path.stem.split("-")[0].upper()
            results[task_id] = ExternalEvidenceValidationResult(
                ok=False,
                task_id=task_id,
                status="unknown",
                errors=(f"evidence load failed: {exc}",),
            )
    return results
