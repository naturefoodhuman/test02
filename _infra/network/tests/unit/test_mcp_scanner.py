# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-23 10:24:12

"""Unit tests for mcp-scan parser and CLI integration (E2-C2-S1-T1)."""

import json
import subprocess
from pathlib import Path

import yaml

from _infra.network.mcp_guard.scanner import load_locked_server_paths, parse_mcp_scan_output


def test_parse_clean_report_passes():
    report = parse_mcp_scan_output('{"status":"passed","findings":[]}', target="srv")

    assert report.passed is True
    assert report.findings == []


def test_parse_findings_report_fails():
    raw = {
        "status": "failed",
        "findings": [
            {
                "category": "tool_poisoning",
                "severity": "high",
                "message": "Tool description asks model to leak secrets",
                "server_id": "evil",
                "tool_name": "search",
            }
        ],
    }

    report = parse_mcp_scan_output(json.dumps(raw), target="evil")

    assert report.passed is False
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.category == "tool_poisoning"
    assert finding.severity == "high"
    assert finding.server_id == "evil"
    assert finding.tool_name == "search"


def test_parse_nested_server_issues():
    raw = {
        "servers": [
            {
                "name": "playwright",
                "issues": [
                    {"type": "schema_change", "level": "medium", "description": "tool schema changed"}
                ],
            }
        ]
    }

    report = parse_mcp_scan_output(json.dumps(raw), target="lockfile")

    assert report.passed is False
    assert report.findings[0].category == "schema_change"
    assert report.findings[0].server_id == "playwright"


def test_nonzero_exit_without_json_becomes_failure():
    report = parse_mcp_scan_output("fatal scanner error", target="srv", exit_code=2, stderr="boom")

    assert report.passed is False
    assert report.findings[0].category == "mcp_scan_parse_error"


def test_load_locked_server_paths(tmp_path):
    lockfile = tmp_path / "mcp_lockfile.yaml"
    lockfile.write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "servers": {
                    "one": {"local_path": str(tmp_path / "one")},
                    "two": {"local_path": str(tmp_path / "two")},
                },
            }
        ),
        encoding="utf-8",
    )

    paths = load_locked_server_paths(lockfile)

    assert paths == [tmp_path / "one", tmp_path / "two"]


def test_scanner_cli_from_json_returns_nonzero_on_findings(tmp_path):
    scan_json = tmp_path / "scan.json"
    scan_json.write_text(
        json.dumps({"findings": [{"category": "pii", "severity": "high", "message": "PII found"}]}),
        encoding="utf-8",
    )

    proc = subprocess.run(
        ["python", "-m", "_infra.network.mcp_guard.scanner", "--from-json", str(scan_json)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert proc.returncode == 1
    assert "PII found" in proc.stdout


def test_scanner_cli_from_json_returns_zero_on_clean(tmp_path):
    scan_json = tmp_path / "scan.json"
    scan_json.write_text('{"status":"passed","findings":[]}', encoding="utf-8")

    proc = subprocess.run(
        ["python", "-m", "_infra.network.mcp_guard.scanner", "--from-json", str(scan_json), "--json"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert proc.returncode == 0
    parsed = json.loads(proc.stdout)
    assert parsed["passed"] is True
