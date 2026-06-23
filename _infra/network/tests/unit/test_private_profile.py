# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 14:55:00

"""Tests for Chrome DevTools private profile setup (E8-C1/E8-C2/E6-C1-S1-T3)."""

import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]


def test_chrome_devtools_lockfile_entry_is_pinned():
    data = yaml.safe_load((ROOT / "config" / "mcp_lockfile.yaml").read_text(encoding="utf-8"))
    entry = data["servers"]["chrome-devtools"]

    assert entry["repo_url"] == "https://github.com/ChromeDevTools/chrome-devtools-mcp.git"
    assert entry["commit_hash"] == "0cafee074cc4947f5672f71cb2f50dec863caa3e"
    assert entry["local_path"] == "mcp-servers/chrome-devtools"
    assert "--no-usage-statistics" in entry["mcp_args"]
    assert "--no-performance-crux" in entry["mcp_args"]
    assert "--browser-url=http://127.0.0.1:9222" in entry["mcp_args"]


def test_start_private_chrome_print_command_contains_required_flags(tmp_path):
    env = {
        "AI_AGENT_PROFILE_ROOT": str(tmp_path / "profiles"),
        "CHROME_BIN": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "PATH": "/usr/bin:/bin:/usr/local/bin",
    }
    proc = subprocess.run(
        [
            "bash",
            str(ROOT / "_infra" / "network" / "scripts" / "start_private_chrome.sh"),
            "--print-command",
            "ai-private-github",
            "9222",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    assert proc.returncode == 0
    assert "--remote-debugging-port=9222" in proc.stdout
    assert "--user-data-dir=" in proc.stdout
    assert "ai-private-github" in proc.stdout
    assert "--no-first-run" in proc.stdout
    assert "--no-default-browser-check" in proc.stdout
    assert "--disable-extensions" in proc.stdout


def test_private_profile_documentation_exists_and_forbids_passwords():
    text = (ROOT / "profiles" / "ai-private-github" / "README.md").read_text(encoding="utf-8")

    assert "github.com" in text
    assert "Do not save passwords" in text
    assert "Do not add payment methods" in text
    assert "Read-only" in text or "read-only" in text


def test_private_mcp_profile_json_valid_and_private_only():
    profile = json.loads((ROOT / ".mcp.json.private").read_text(encoding="utf-8"))
    servers = set(profile["mcpServers"])

    assert profile["_forge_trace"]["llm"] == "Arena.ai Agent Mode - Execution Lead Engineer"
    assert servers == {"chrome-devtools-private"}
    assert "searxng" not in servers
    assert "crawl4ai" not in servers
    assert "shell" not in servers
    args = profile["mcpServers"]["chrome-devtools-private"]["args"]
    assert "--browser-url=http://127.0.0.1:9222" in args
    assert "--no-usage-statistics" in args
    assert "--no-performance-crux" in args
