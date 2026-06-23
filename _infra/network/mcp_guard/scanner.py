# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-23 10:24:12

"""
mcp-scan integration for MCP Guard (E2-C2-S1-T1).

Responsibilities:
- Run ``mcp-scan scan`` for pinned local MCP server checkouts.
- Parse JSON output into a stable internal report model.
- Return non-zero / failed status when any issue is detected or the scanner
  command itself fails.

The parser is intentionally tolerant because mcp-scan output schemas may evolve.
It recognizes common issue containers such as findings, issues, vulnerabilities,
violations, warnings and errors, including per-server nested lists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence

import yaml


ISSUE_KEYS = ("findings", "issues", "vulnerabilities", "violations", "warnings", "errors")
FAIL_STATUSES = {"fail", "failed", "error", "blocked", "unsafe", "denied"}


@dataclass(frozen=True)
class MCPScanFinding:
    """Normalized mcp-scan finding."""

    category: str
    severity: str
    message: str
    server_id: str | None = None
    tool_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)

    @property
    def is_blocking(self) -> bool:
        # For admission control any finding is blocking. Severity is kept for
        # reporting but not used to allow warnings through silently.
        return True


@dataclass(frozen=True)
class MCPScanReport:
    """Normalized mcp-scan report."""

    target: str
    status: str
    findings: list[MCPScanFinding] = field(default_factory=list)
    exit_code: int = 0
    raw: Any = None
    stderr: str = ""

    @property
    def has_findings(self) -> bool:
        return bool(self.findings)

    @property
    def passed(self) -> bool:
        return self.exit_code == 0 and not self.findings and self.status.lower() not in FAIL_STATUSES

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "status": self.status,
            "exit_code": self.exit_code,
            "passed": self.passed,
            "findings": [finding.__dict__ for finding in self.findings],
            "stderr": self.stderr,
        }


def _stringify_message(item: Mapping[str, Any]) -> str:
    for key in ("message", "description", "detail", "details", "reason", "title", "name"):
        value = item.get(key)
        if value:
            if isinstance(value, str):
                return value
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return json.dumps(item, ensure_ascii=False, sort_keys=True)


def _finding_from_item(item: Any, inherited_server: str | None = None) -> MCPScanFinding:
    if not isinstance(item, Mapping):
        return MCPScanFinding(
            category="mcp_scan",
            severity="unknown",
            message=str(item),
            server_id=inherited_server,
            raw={"value": item},
        )

    return MCPScanFinding(
        category=str(item.get("category") or item.get("type") or item.get("check") or item.get("id") or "mcp_scan"),
        severity=str(item.get("severity") or item.get("level") or item.get("risk") or "unknown").lower(),
        message=_stringify_message(item),
        server_id=str(item.get("server_id") or item.get("server") or inherited_server or "") or None,
        tool_name=str(item.get("tool_name") or item.get("tool") or "") or None,
        raw=dict(item),
    )


def _iter_issue_items(data: Any, inherited_server: str | None = None) -> Iterable[MCPScanFinding]:
    if isinstance(data, list):
        for item in data:
            yield _finding_from_item(item, inherited_server=inherited_server)
        return

    if not isinstance(data, Mapping):
        return

    current_server = str(data.get("server_id") or data.get("server") or data.get("name") or inherited_server or "") or None

    for key in ISSUE_KEYS:
        value = data.get(key)
        if isinstance(value, list):
            for item in value:
                yield _finding_from_item(item, inherited_server=current_server)
        elif isinstance(value, Mapping):
            yield from _iter_issue_items(value, inherited_server=current_server)
        elif isinstance(value, str) and value:
            yield MCPScanFinding(
                category=key,
                severity="error" if key == "errors" else "warning",
                message=value,
                server_id=current_server,
                raw={key: value},
            )

    # Common nested layouts: {servers: [{name, findings: [...]}, ...]}
    for nested_key in ("servers", "results", "scans", "reports"):
        nested = data.get(nested_key)
        if isinstance(nested, list):
            for item in nested:
                yield from _iter_issue_items(item, inherited_server=current_server)
        elif isinstance(nested, Mapping):
            for name, item in nested.items():
                if isinstance(item, Mapping):
                    yield from _iter_issue_items(item, inherited_server=str(name))


def parse_mcp_scan_output(output: str, *, target: str = "mcp", exit_code: int = 0, stderr: str = "") -> MCPScanReport:
    """Parse mcp-scan JSON output into a normalized report."""
    text = (output or "").strip()
    if not text:
        status = "passed" if exit_code == 0 else "failed"
        findings = [] if exit_code == 0 else [
            MCPScanFinding(
                category="mcp_scan_process",
                severity="error",
                message=stderr or f"mcp-scan exited with code {exit_code}",
            )
        ]
        return MCPScanReport(target=target, status=status, findings=findings, exit_code=exit_code, raw=None, stderr=stderr)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # If the process failed with non-JSON output, preserve the text as an error.
        if exit_code != 0:
            return MCPScanReport(
                target=target,
                status="failed",
                findings=[
                    MCPScanFinding(
                        category="mcp_scan_parse_error",
                        severity="error",
                        message=text[:1000],
                    )
                ],
                exit_code=exit_code,
                raw=text,
                stderr=stderr,
            )
        return MCPScanReport(target=target, status="unknown", findings=[], exit_code=exit_code, raw=text, stderr=stderr)

    findings = list(_iter_issue_items(data))
    raw_status = ""
    if isinstance(data, Mapping):
        raw_status = str(data.get("status") or data.get("result") or data.get("decision") or "")

    if exit_code != 0 and not findings:
        findings.append(
            MCPScanFinding(
                category="mcp_scan_process",
                severity="error",
                message=stderr or f"mcp-scan exited with code {exit_code}",
            )
        )

    if raw_status.lower() in FAIL_STATUSES and not findings:
        findings.append(
            MCPScanFinding(
                category="mcp_scan_status",
                severity="error",
                message=f"mcp-scan reported failing status: {raw_status}",
            )
        )

    status = "failed" if findings or exit_code != 0 or raw_status.lower() in FAIL_STATUSES else (raw_status or "passed")
    return MCPScanReport(target=target, status=status, findings=findings, exit_code=exit_code, raw=data, stderr=stderr)


class MCPScanRunner:
    """Subprocess runner for mcp-scan."""

    def __init__(self, mcp_scan_bin: str = "mcp-scan"):
        self.mcp_scan_bin = mcp_scan_bin

    def scan_path(self, target_path: str | Path = ".") -> MCPScanReport:
        target = Path(target_path)
        cmd = [self.mcp_scan_bin, "scan", "--json"]
        proc = subprocess.run(
            cmd,
            cwd=str(target),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return parse_mcp_scan_output(
            proc.stdout,
            target=str(target),
            exit_code=proc.returncode,
            stderr=proc.stderr.strip(),
        )


def load_locked_server_paths(lockfile: str | Path = "config/mcp_lockfile.yaml") -> list[Path]:
    """Load local MCP server paths from config/mcp_lockfile.yaml."""
    path = Path(lockfile)
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    servers = data.get("servers", {}) if isinstance(data, Mapping) else {}
    paths: list[Path] = []
    for server in servers.values():
        if isinstance(server, Mapping) and server.get("local_path"):
            paths.append(Path(str(server["local_path"])))
    return paths


def _print_report(report: MCPScanReport) -> None:
    status = "PASS" if report.passed else "FAIL"
    print(f"[{status}] {report.target} ({len(report.findings)} finding(s))")
    for finding in report.findings:
        location = ":".join(part for part in [finding.server_id, finding.tool_name] if part)
        prefix = f"  - {finding.severity} {finding.category}"
        if location:
            prefix += f" [{location}]"
        print(f"{prefix}: {finding.message}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run and parse mcp-scan for pinned MCP servers")
    parser.add_argument("--target", help="Local MCP server directory to scan")
    parser.add_argument("--lockfile", default="config/mcp_lockfile.yaml", help="MCP lockfile to read when --target is omitted")
    parser.add_argument("--from-json", help="Parse an existing mcp-scan JSON output file instead of running mcp-scan")
    parser.add_argument("--json", action="store_true", help="Print normalized JSON report")
    args = parser.parse_args(argv)

    if args.from_json:
        text = Path(args.from_json).read_text(encoding="utf-8")
        report = parse_mcp_scan_output(text, target=args.from_json)
        if args.json:
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            _print_report(report)
        return 0 if report.passed else 1

    runner = MCPScanRunner()
    targets = [Path(args.target)] if args.target else load_locked_server_paths(args.lockfile)
    if not targets:
        targets = [Path(".")]

    reports = [runner.scan_path(target) for target in targets]
    if args.json:
        print(json.dumps([report.to_dict() for report in reports], ensure_ascii=False, indent=2))
    else:
        for report in reports:
            _print_report(report)

    return 0 if all(report.passed for report in reports) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
