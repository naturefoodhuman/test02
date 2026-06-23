# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 14:54:47

"""Integration-style tests for scripts/switch-mode.sh (E6-C2-S1-T1)."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "switch-mode.sh"


def make_profiles(tmp_path: Path):
    for mode in ("coding", "research", "private"):
        (tmp_path / f".mcp.json.{mode}").write_text('{"mcpServers":{}}\n', encoding="utf-8")


def run_switch(tmp_path: Path, mode: str):
    return subprocess.run(
        ["bash", str(SCRIPT), mode],
        cwd=tmp_path,
        env={"FORGE_ROOT": str(tmp_path), "PATH": "/usr/bin:/bin:/usr/local/bin"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_switch_mode_creates_repeated_symlink(tmp_path):
    make_profiles(tmp_path)

    first = run_switch(tmp_path, "coding")
    second = run_switch(tmp_path, "research")

    assert first.returncode == 0
    assert second.returncode == 0
    assert (tmp_path / ".mcp.json").is_symlink()
    assert (tmp_path / ".mcp.json").readlink() == Path(".mcp.json.research")


def test_switch_mode_current_reports_mode(tmp_path):
    make_profiles(tmp_path)
    run_switch(tmp_path, "private")

    result = run_switch(tmp_path, "current")

    assert result.returncode == 0
    assert "current: private" in result.stdout


def test_switch_mode_rejects_invalid_mode(tmp_path):
    make_profiles(tmp_path)

    result = run_switch(tmp_path, "all")

    assert result.returncode != 0
    assert "invalid mode" in result.stderr
