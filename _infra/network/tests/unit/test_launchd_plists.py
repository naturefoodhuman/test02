# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 16:35:00

"""Static tests for launchd plist files (E10-C2-S1-T1)."""

from pathlib import Path
import plistlib

ROOT = Path(__file__).resolve().parents[4]
LAUNCHD = ROOT / "scripts" / "launchd"


def load_plist(name: str) -> dict:
    with (LAUNCHD / name).open("rb") as f:
        return plistlib.load(f)


def test_health_plist_runs_every_five_minutes_and_logs_to_runtime():
    data = load_plist("com.network-agent.health.plist")

    assert data["Label"] == "com.network-agent.health"
    assert data["StartInterval"] == 300
    command = " ".join(data["ProgramArguments"])
    assert "scripts/health-check.sh" in command
    assert "runtime/logs/launchd-health.log" in command
    assert data["RunAtLoad"] is True


def test_mcp_scan_plist_runs_sunday_3am_and_logs_to_runtime():
    data = load_plist("com.network-agent.mcp-scan.plist")

    assert data["Label"] == "com.network-agent.mcp-scan"
    schedule = data["StartCalendarInterval"]
    assert schedule["Weekday"] == 0
    assert schedule["Hour"] == 3
    assert schedule["Minute"] == 0
    command = " ".join(data["ProgramArguments"])
    assert "_infra/network/scripts/scan_mcp.sh" in command
    assert "--lockfile config/mcp_lockfile.yaml" in command
    assert "runtime/logs/launchd-mcp-scan.log" in command


def test_launchd_readme_documents_install_and_uninstall():
    text = (LAUNCHD / "README.md").read_text(encoding="utf-8")

    assert "launchctl load" in text
    assert "launchctl unload" in text
    assert "runtime/logs/launchd-health.log" in text
    assert "runtime/logs/launchd-mcp-scan.log" in text
