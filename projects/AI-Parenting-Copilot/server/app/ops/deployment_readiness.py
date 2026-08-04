# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 21:22:00

"""Local deployment readiness report for APC-T054."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from server.app.ops.launchd_validator import validate_launchd_directory


@dataclass(frozen=True, slots=True)
class DeploymentReadinessReport:
    ok: bool
    checks: dict[str, str]
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def build_deployment_readiness_report(
    project_root: Path | str = ".",
) -> DeploymentReadinessReport:
    root = Path(project_root)
    checks: dict[str, str] = {}
    errors: list[str] = []
    for rel in (
        "server/scripts/run_dev.sh",
        "server/scripts/run_worker.sh",
        "server/scripts/run_mmwave_worker.py",
        "server/scripts/api_health_smoke.py",
        "server/scripts/api_server_smoke.py",
        "docs/RUNBOOK_LOCAL_API.md",
        "docs/RUNBOOK_DEPLOYMENT.md",
        "deploy/launchd/com.parenting.server.plist",
        "deploy/launchd/com.parenting.fregata.plist",
        "deploy/launchd/com.parenting.backup.plist",
    ):
        _expect((root / rel).exists(), f"file:{rel}", checks, errors)
    makefile = _read(root / "Makefile")
    for target in (
        "run-api",
        "run-dev",
        "api-health-smoke",
        "api-server-smoke-test",
        "launchd-validate",
        "backup-verify-dry-run",
    ):
        _expect(f"{target}:" in makefile, f"make_target:{target}", checks, errors)
    run_dev = _read(root / "server/scripts/run_dev.sh")
    _expect("uvicorn" in run_dev, "run_dev_uvicorn", checks, errors)
    _expect("0.0.0.0" in run_dev or "127.0.0.1" in run_dev, "run_dev_host_declared", checks, errors)
    launchd_results = validate_launchd_directory(root / "deploy/launchd")
    for result in launchd_results:
        _expect(result.ok, f"launchd:{result.label}", checks, errors)
        for error in result.errors:
            errors.append(f"{result.label}: {error}")
    runbook = _read(root / "docs/RUNBOOK_DEPLOYMENT.md")
    _expect("launchd" in runbook.lower(), "runbook_launchd", checks, errors)
    _expect("runtime/logs" in runbook, "runbook_runtime_logs", checks, errors)
    local_api = _read(root / "docs/RUNBOOK_LOCAL_API.md")
    _expect("make run-api" in local_api, "runbook_run_api", checks, errors)
    _expect("make api-health-smoke" in local_api, "runbook_api_health_smoke", checks, errors)
    return DeploymentReadinessReport(ok=not errors, checks=checks, errors=tuple(errors))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _expect(
    condition: bool,
    check_name: str,
    checks: dict[str, str],
    errors: list[str],
) -> None:
    checks[check_name] = "ok" if condition else "failed"
    if not condition:
        errors.append(f"Deployment readiness failed: {check_name}")
