# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 14:54:47

"""Tests for Claude Code PreToolUse hook (E6-C3-S1-T1)."""

import json
import subprocess
from pathlib import Path

from _infra.network.mcp_guard.hooks.pre_tool_use import handle_hook_event, parse_hook_payload

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "hooks" / "pre_tool_use.sh"


def test_parse_hook_payload_aliases():
    call = parse_hook_payload(
        {
            "server_name": "searxng",
            "tool": "search",
            "arguments": {"query": "hello"},
            "mode": "research",
            "traceId": "t1",
        }
    )

    assert call.server_id == "searxng"
    assert call.tool_name == "search"
    assert call.args["query"] == "hello"
    assert call.trace_id == "t1"


def test_handle_hook_event_allows_safe_research_call():
    result = handle_hook_event({"server_id": "searxng", "tool_name": "search", "args": {"query": "public"}, "mode": "research"})

    assert result["allow"] is True
    assert result["decision"] == "allow"


def test_handle_hook_event_denies_shell_in_research():
    result = handle_hook_event({"server_id": "shell", "tool_name": "execute_shell", "args": {"cmd": "echo hi"}, "mode": "research"})

    assert result["allow"] is False
    assert result["decision"] == "deny"
    assert result["reason"] == "server_denied:shell"


def test_pre_tool_use_shell_script_outputs_json():
    payload = {"server_id": "searxng", "tool_name": "search", "args": {"query": "public"}, "mode": "research"}
    proc = subprocess.run(
        ["bash", str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=ROOT,
        check=False,
    )

    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["allow"] is True
    assert data["reason"] in {"default_allow", "human_approved"}


def test_pre_tool_use_shell_script_denies_bad_argument():
    payload = {
        "server_id": "chrome-devtools-private",
        "tool_name": "evaluate_js",
        "args": {"script": "document.cookie"},
        "mode": "private",
    }
    proc = subprocess.run(
        ["bash", str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=ROOT,
        check=False,
    )

    assert proc.returncode == 2
    data = json.loads(proc.stdout)
    assert data["allow"] is False
    assert data["reason"] in {"tool_forbidden:evaluate_js", "forbidden_argument_pattern"}
