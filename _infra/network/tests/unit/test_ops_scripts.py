# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 16:20:00

"""Tests for operations scripts (E10-C1/E10-C3)."""

import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HEALTH = ROOT / "scripts" / "health-check.sh"
BACKUP = ROOT / "scripts" / "backup.sh"


def test_health_check_static_passes():
    proc = subprocess.run(
        ["bash", str(HEALTH), "--static"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "network config loads" in proc.stdout
    assert "static file exists: config/network.yaml" in proc.stdout


def make_temp_root(tmp_path: Path) -> Path:
    root = tmp_path / "forge"
    (root / "config").mkdir(parents=True)
    (root / "docker" / "searxng").mkdir(parents=True)
    (root / "runtime").mkdir(parents=True)
    (root / "profiles" / "ai-private-github").mkdir(parents=True)
    (root / ".mcp.json.coding").write_text("{}\n", encoding="utf-8")
    (root / "config" / "network.yaml").write_text("version: '1.0'\n", encoding="utf-8")
    (root / "config" / "mcp_lockfile.yaml").write_text("version: '1.0'\nservers: {}\n", encoding="utf-8")
    (root / "docker" / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (root / "docker" / "searxng" / "settings.yml").write_text("search:\n  formats: [json]\n", encoding="utf-8")
    (root / "runtime" / "audit.db").write_bytes(b"not a real db but selected file")
    (root / "profiles" / "ai-private-github" / "Cookies").write_text("SECRET_COOKIE", encoding="utf-8")
    return root


def test_backup_dry_run_lists_includes_and_excludes(tmp_path):
    root = make_temp_root(tmp_path)
    proc = subprocess.run(
        ["bash", str(BACKUP), "--dry-run", "--dest", str(root / "runtime" / "backups")],
        cwd=root,
        env={"FORGE_ROOT": str(root), "PATH": "/usr/bin:/bin:/usr/local/bin"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert proc.returncode == 0
    assert "config" in proc.stdout
    assert "docker" in proc.stdout
    assert "profiles" in proc.stdout  # listed as excluded, not included


def test_backup_creates_archive_without_profiles_or_cookies(tmp_path):
    root = make_temp_root(tmp_path)
    backup_dir = root / "runtime" / "backups"
    proc = subprocess.run(
        ["bash", str(BACKUP), "--dest", str(backup_dir)],
        cwd=root,
        env={"FORGE_ROOT": str(root), "PATH": "/usr/bin:/bin:/usr/local/bin"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    archives = list(backup_dir.glob("forge-network-*.tar.gz"))
    assert len(archives) == 1
    with tarfile.open(archives[0], "r:gz") as tar:
        names = tar.getnames()

    assert "config/network.yaml" in names
    assert "docker/docker-compose.yml" in names
    assert "profiles/ai-private-github/Cookies" not in names
    assert not any("cookie" in name.lower() or "session" in name.lower() or "payment" in name.lower() for name in names)
