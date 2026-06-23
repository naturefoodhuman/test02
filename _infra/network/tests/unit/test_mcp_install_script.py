# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 22:38:00

"""Unit-style tests for pinned MCP install script (E2-C1-S1-T1)."""

import subprocess
from pathlib import Path

import yaml

SCRIPT = Path("_infra/network/scripts/install_mcp.sh").resolve()


def make_git_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "fake-mcp-repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    (repo / "README.md").write_text("fake mcp server\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, stdout=subprocess.PIPE)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    return repo, commit


def run_script(tmp_path: Path, *args: str):
    env = {
        "FORGE_ROOT": str(tmp_path / "forge-root"),
        "FORGE_MCP_INSTALL_SKIP_SCAN": "1",
        "PATH": "/usr/bin:/bin:/usr/local/bin",
    }
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )


def test_install_mcp_script_clones_checkout_and_updates_lockfile(tmp_path):
    repo, commit = make_git_repo(tmp_path)

    result = run_script(tmp_path, "fake-server", str(repo), commit)

    assert result.returncode == 0, result.stderr
    server_dir = tmp_path / "forge-root" / "mcp-servers" / "fake-server"
    assert server_dir.exists()
    checked_out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=server_dir, text=True).strip()
    assert checked_out == commit

    lockfile = tmp_path / "forge-root" / "config" / "mcp_lockfile.yaml"
    data = yaml.safe_load(lockfile.read_text(encoding="utf-8"))
    server = data["servers"]["fake-server"]
    assert server["repo_url"] == str(repo)
    assert server["commit_hash"] == commit
    assert server["scan_status"] == "skipped_for_test"
    assert server["local_path"] == str(server_dir)


def test_install_mcp_script_rejects_latest_source(tmp_path):
    result = run_script(tmp_path, "bad-server", "https://example.test/mcp@latest", "abcdef1")

    assert result.returncode != 0
    assert "forbidden" in result.stderr.lower()


def test_install_mcp_script_rejects_branch_name_commit(tmp_path):
    repo, _commit = make_git_repo(tmp_path)

    result = run_script(tmp_path, "bad-server", str(repo), "main")

    assert result.returncode != 0
    assert "immutable git commit" in result.stderr
