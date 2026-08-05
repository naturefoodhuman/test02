# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 02:20:00

"""Architecture compliance audit for AI Parenting Copilot.

The audit is intentionally static and conservative: it checks that core boundary
modules, route audit hooks, Android offline guarantees, and closeout controls remain
present. It does not replace code review, clinical review, or real-device validation.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from server.app.ops.external_validation import build_external_validation_plan


@dataclass(frozen=True, slots=True)
class ArchitectureCheck:
    check_id: str
    title: str
    status: str
    evidence: tuple[str, ...] = field(default_factory=tuple)
    details: str | None = None


@dataclass(frozen=True, slots=True)
class ArchitectureComplianceReport:
    status: str
    checks: tuple[ArchitectureCheck, ...]
    external_blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            "# Architecture Compliance Audit",
            "",
            f"- Status: `{self.status}`",
            f"- Checks: `{len(self.checks)}`",
            f"- External blockers: `{len(self.external_blockers)}`",
            "",
            "This audit is a static engineering control. It does not replace "
            "clinical review, hardware validation, NAS restore drills, or long-running soak.",
            "",
            "## Checks",
            "",
        ]
        for check in self.checks:
            lines.extend(
                [
                    f"### {check.check_id} — {check.title}",
                    "",
                    f"- Status: `{check.status}`",
                ]
            )
            if check.details:
                lines.append(f"- Details: {check.details}")
            if check.evidence:
                lines.append("- Evidence:")
                lines.extend(f"  - `{item}`" for item in check.evidence)
            lines.append("")
        lines.append("## Remaining external blockers")
        lines.append("")
        for blocker in self.external_blockers:
            lines.append(f"- {blocker}")
        lines.append("")
        return "\n".join(lines)


def build_architecture_compliance_report(
    project_root: Path | str = ".",
) -> ArchitectureComplianceReport:
    root = Path(project_root)
    checks = [
        _model_gateway_check(root),
        _privacy_gateway_check(root),
        _rule_engine_check(root),
        _dose_interceptor_check(root),
        _notification_orchestrator_check(root),
        _mutating_routes_audit_check(root),
        _android_offline_check(root),
        _db_runtime_check(root),
        _readiness_closeout_check(root),
        _docs_state_check(root),
    ]
    external_blockers = tuple(
        f"{item.task_id}: {item.blocked_by}"
        for item in build_external_validation_plan().items
    )
    failed = [check for check in checks if check.status == "fail"]
    status = "fail" if failed else "pass_with_external_blockers"
    return ArchitectureComplianceReport(
        status=status,
        checks=tuple(checks),
        external_blockers=external_blockers,
    )


def write_architecture_compliance_report(
    report: ArchitectureComplianceReport,
    *,
    output_dir: Path | str = "runtime/reports",
) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "architecture-compliance-audit.json"
    md_path = output / "architecture-compliance-audit.md"
    json_path.write_text(report.to_json(), encoding="utf-8")
    md_path.write_text(report.to_markdown(), encoding="utf-8")
    return json_path, md_path


def _model_gateway_check(root: Path) -> ArchitectureCheck:
    evidence = ["server/app/model_gateway/client.py", "server/app/model_gateway/routing.py"]
    missing = [path for path in evidence if not (root / path).exists()]
    direct_hits = _grep_code(root / "server/app", ("import openai", "from openai", "anthropic."))
    direct_hits = tuple(
        hit
        for hit in direct_hits
        if "/model_gateway/" not in hit and not hit.endswith("ops/architecture_compliance.py")
    )
    status = "pass" if not missing and not direct_hits else "fail"
    details = (
        None if not direct_hits else "Direct model SDK references found outside model_gateway."
    )
    return ArchitectureCheck(
        check_id="ARCH-001",
        title="LLM calls are isolated behind Model Gateway",
        status=status,
        evidence=tuple(evidence + list(direct_hits)),
        details=details,
    )


def _privacy_gateway_check(root: Path) -> ArchitectureCheck:
    evidence = ["server/app/privacy/adapter.py", "tests/test_privacy_adapter.py"]
    missing = [path for path in evidence if not (root / path).exists()]
    return ArchitectureCheck(
        check_id="ARCH-002",
        title="Privacy adapter exists for outbound/cloud boundary",
        status="pass" if not missing else "fail",
        evidence=tuple(evidence),
        details="Cloud credentials and real outbound validation remain external/local-only.",
    )


def _rule_engine_check(root: Path) -> ArchitectureCheck:
    evidence = [
        "server/app/rule_engine/api/routes.py",
        "server/app/rule_engine/domains/medication.py",
        "server/app/rule_engine/domains/triage.py",
        "server/app/rule_engine/domains/vaccine.py",
        "server/app/rule_engine/domains/growth.py",
        "tests/test_rules_admin_api.py",
    ]
    text = _read(root / "server/app/rule_engine/api/routes.py")
    required = all(
        domain in text for domain in ("medication", "triage", "thresholds", "vaccine", "growth")
    )
    status = "pass" if required and all((root / path).exists() for path in evidence) else "fail"
    return ArchitectureCheck(
        check_id="ARCH-003",
        title="Dose/threshold/medical domains are exposed via Rule Engine",
        status=status,
        evidence=tuple(evidence),
    )


def _dose_interceptor_check(root: Path) -> ArchitectureCheck:
    evidence = [
        "server/app/orchestrator/dose_interceptor.py",
        "tests/test_dose_interceptor.py",
        "tests/security/test_prompt_injection.py",
        "tests/security/test_privacy_regression.py",
    ]
    return ArchitectureCheck(
        check_id="ARCH-004",
        title="Dose Interceptor protects LLM/Copilot free-text dose output",
        status="pass" if all((root / path).exists() for path in evidence) else "fail",
        evidence=tuple(evidence),
    )


def _notification_orchestrator_check(root: Path) -> ArchitectureCheck:
    routes = _read(root / "server/app/notification/api/routes.py")
    orchestrator = _read(root / "server/app/notification/orchestrator.py")
    evidence = [
        "server/app/notification/orchestrator.py",
        "server/app/notification/api/routes.py",
        "tests/test_notification_orchestrator.py",
        "tests/e2e/test_red_alert_escalation_report.py",
    ]
    ok = "NotificationOrchestrator" in routes and "channels_for" in orchestrator
    return ArchitectureCheck(
        check_id="ARCH-005",
        title="Alert delivery is routed through Notification Orchestrator",
        status="pass" if ok and all((root / path).exists() for path in evidence) else "fail",
        evidence=tuple(evidence),
    )


def _mutating_routes_audit_check(root: Path) -> ArchitectureCheck:
    route_files = sorted((root / "server/app").rglob("api/routes.py"))
    missing: list[str] = []
    for path in route_files:
        text = path.read_text(encoding="utf-8")
        has_mutation = any(
            marker in text for marker in ("@router.post", "@router.put", "@router.delete")
        )
        if has_mutation and "record_request_audit" not in text:
            missing.append(str(path.relative_to(root)))
    return ArchitectureCheck(
        check_id="ARCH-006",
        title="Mutating API route modules include request audit hook",
        status="pass" if not missing else "fail",
        evidence=tuple(str(path.relative_to(root)) for path in route_files) + tuple(missing),
        details=None if not missing else "Mutation route files missing record_request_audit.",
    )


def _android_offline_check(root: Path) -> ArchitectureCheck:
    quick = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/QuickRecordActivity.kt"
    )
    drain = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/PendingSyncDrainer.kt"
    )
    ack = _read(
        root / "android/android/app/src/main/java/com/aiparentingcopilot/AlertAckDrainer.kt"
    )
    ok = all(
        [
            "insertPending" in quick,
            "saveFallbackCandidate" in quick,
            "markSynced" in drain,
            "/api/v1/sync/heartbeat" in drain,
            "catch (_: Exception)" in ack,
            "recordLocalAction" in ack,
        ]
    )
    return ArchitectureCheck(
        check_id="ARCH-007",
        title="Android offline records and alert ack actions are not dropped on failure",
        status="pass" if ok else "fail",
        evidence=(
            "android/android/app/src/main/java/com/aiparentingcopilot/QuickRecordActivity.kt",
            "android/android/app/src/main/java/com/aiparentingcopilot/PendingSyncDrainer.kt",
            "android/android/app/src/main/java/com/aiparentingcopilot/AlertAckDrainer.kt",
        ),
    )


def _db_runtime_check(root: Path) -> ArchitectureCheck:
    makefile = _read(root / "Makefile")
    required_targets = (
        "api-db-smoke-test",
        "worker-db-smoke-test",
        "powersync-smoke-test",
        "api-server-smoke-test",
    )
    ok = all(f"{target}:" in makefile for target in required_targets)
    return ArchitectureCheck(
        check_id="ARCH-008",
        title="DB-backed runtime and smoke targets are present",
        status="pass" if ok else "fail",
        evidence=required_targets,
    )


def _readiness_closeout_check(root: Path) -> ArchitectureCheck:
    evidence = [
        "server/app/ops/p0_readiness.py",
        "server/app/ops/external_validation.py",
        "server/app/ops/external_evidence.py",
        "server/app/ops/apc_closeout.py",
        "server/app/ops/backlog_patch_plan.py",
        "tests/test_p0_readiness_report.py",
        "tests/test_external_validation_plan.py",
        "tests/test_apc_closeout_gate.py",
    ]
    return ArchitectureCheck(
        check_id="ARCH-009",
        title="Readiness, external evidence, and closeout controls are present",
        status="pass" if all((root / path).exists() for path in evidence) else "fail",
        evidence=tuple(evidence),
    )


def _docs_state_check(root: Path) -> ArchitectureCheck:
    backlog = _read(root / "docs/TASK_BACKLOG.md")
    status_line = backlog.splitlines()[12] if backlog else ""
    done_count = len(re.findall(r"APC-T\d{3} DONE", status_line))
    blocked_count = len(re.findall(r"APC-T\d{3} BLOCKED", status_line))
    ok = done_count == 49 and blocked_count == 10
    return ArchitectureCheck(
        check_id="ARCH-010",
        title="Task backlog status summary matches current closeout stage",
        status="pass" if ok else "warning",
        evidence=(f"DONE={done_count}", f"BLOCKED={blocked_count}"),
        details="Expected current state is 49 DONE / 10 BLOCKED external-validation tasks.",
    )


def _grep_code(root: Path, needles: tuple[str, ...]) -> tuple[str, ...]:
    hits: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in needles:
            if needle in text:
                hits.append(str(path))
                break
    return tuple(hits)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""
