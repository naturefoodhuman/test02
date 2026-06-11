# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
"""CLI 端到端测试（在临时项目目录上跑真实命令）。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forge.cli import main  # noqa: E402


def _make_project(tmp_path: Path, with_spec: bool = False) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "DISCOVERY.md").write_text("# d", encoding="utf-8")
    tg = "## Task: a\n- status: DONE\n## Task: b\n- status: TODO\n- depends-on: a\n"
    (tmp_path / "docs" / "TASK_GRAPH.md").write_text(tg, encoding="utf-8")
    if with_spec:
        (tmp_path / "docs" / "SPEC.md").write_text("# s", encoding="utf-8")
        (tmp_path / "docs" / "RISK.md").write_text("# r", encoding="utf-8")
    return tmp_path


def test_cli_status(tmp_path, capsys) -> None:
    root = _make_project(tmp_path)
    rc = main(["--root", str(root), "status"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "推断当前阶段" in out


def test_cli_check_clean(tmp_path, capsys) -> None:
    root = _make_project(tmp_path)
    rc = main(["--root", str(root), "check"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "TASK_GRAPH 结构合法" in out


def test_cli_check_detects_in_progress(tmp_path, capsys) -> None:
    root = _make_project(tmp_path)
    (root / "docs" / "TASK_GRAPH.md").write_text(
        "## Task: a\n- status: IN_PROGRESS\n", encoding="utf-8"
    )
    main(["--root", str(root), "check"])
    out = capsys.readouterr().out
    assert "IN_PROGRESS" in out


def test_cli_tasks(tmp_path, capsys) -> None:
    root = _make_project(tmp_path)
    main(["--root", str(root), "tasks"])
    out = capsys.readouterr().out
    assert "b" in out  # a 已 DONE，b 依赖满足 → 可执行


def test_cli_gate(tmp_path, capsys) -> None:
    rc = main(["--root", str(tmp_path), "gate", "GATE-2"])
    out = capsys.readouterr().out
    assert rc == 0 and "架构" in out
