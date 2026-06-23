# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 16:05:00

"""Tests for restricted Playwright CLI wrapper (E7-C6-S1-T1)."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "_infra" / "network" / "scripts" / "run_playwright_action.py"


def run_action(*args):
    return subprocess.run(
        ["python", str(SCRIPT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=ROOT,
        check=False,
    )


def test_open_dry_run_builds_safe_command():
    proc = run_action("open", "--url", "https://example.com", "--dry-run")

    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["action"] == "open"
    assert data["payload"]["url"] == "https://example.com"
    assert data["argv"][:3] == ["node", "mcp-servers/playwright-public/cli.js", "open"]


def test_snapshot_and_close_dry_run():
    snap = run_action("snapshot", "--dry-run")
    close = run_action("close", "--dry-run")

    assert snap.returncode == 0
    assert close.returncode == 0
    assert json.loads(snap.stdout)["action"] == "snapshot"
    assert json.loads(close.stdout)["action"] == "close"


def test_type_rejects_cookie_payload():
    proc = run_action("type", "--ref", "input-1", "--text", "document.cookie", "--dry-run")

    assert proc.returncode != 0
    assert "unsafe arguments" in proc.stderr


def test_wait_requires_valid_range():
    proc = run_action("wait", "--ms", "70000", "--dry-run")

    assert proc.returncode != 0
    assert "between 0 and 60000" in proc.stderr


def test_missing_required_arg_rejected():
    proc = run_action("click", "--dry-run")

    assert proc.returncode != 0
    assert "click requires --ref" in proc.stderr


def test_invalid_action_rejected_by_argparse():
    proc = run_action("shell", "--dry-run")

    assert proc.returncode != 0
    assert "invalid choice" in proc.stderr
