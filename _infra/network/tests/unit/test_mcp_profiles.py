# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 11:45:00

"""Tests for mode-specific .mcp.json profiles (E6-C1)."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def load_profile(name: str) -> dict:
    path = ROOT / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_coding_profile_json_valid_and_trace_present():
    profile = load_profile(".mcp.json.coding")

    assert profile["_forge_trace"]["llm"] == "Arena.ai Agent Mode - Execution Lead Engineer"
    assert profile["_forge_trace"]["task"] == "E6-C1-S1-T1"
    assert isinstance(profile["mcpServers"], dict)


def test_coding_profile_allows_only_coding_servers():
    profile = load_profile(".mcp.json.coding")
    servers = set(profile["mcpServers"])

    assert {"filesystem", "git", "tests"}.issubset(servers)
    assert not ({"searxng", "crawl4ai", "playwright", "playwright-public", "chrome-devtools", "chrome-devtools-private"} & servers)


def test_coding_profile_uses_local_pinned_paths_not_latest():
    profile = load_profile(".mcp.json.coding")
    serialized = json.dumps(profile, ensure_ascii=False)

    assert "@latest" not in serialized
    assert "npx" not in serialized
    assert "uvx" not in serialized
    for server in profile["mcpServers"].values():
        args = server.get("args", [])
        assert args
        assert str(args[0]).startswith("mcp-servers/")
