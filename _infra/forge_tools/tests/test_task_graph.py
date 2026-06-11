# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
"""TASK_GRAPH 解析与校验测试。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forge.task_graph import parse_task_graph, validate_task_graph  # noqa: E402

SAMPLE = """
# TASK_GRAPH
## Task: a
- status: DONE
## Task: b
- status: IN_PROGRESS
- depends-on: a
## Task: c
- status: TODO
- depends-on: a, b
"""


def test_parse_basic() -> None:
    g = parse_task_graph(SAMPLE)
    assert len(g.tasks) == 3
    assert g.by_name("a").status == "DONE"
    assert g.by_name("c").depends_on == ["a", "b"]


def test_in_progress() -> None:
    g = parse_task_graph(SAMPLE)
    ip = g.in_progress()
    assert len(ip) == 1 and ip[0].name == "b"


def test_ready_respects_dependencies() -> None:
    g = parse_task_graph(SAMPLE)
    ready = [t.name for t in g.ready()]
    # c 依赖 a(done) 和 b(in_progress, 未完成) → 不可执行；b 是 IN_PROGRESS 也不算 ready(TODO)
    assert ready == []


def test_ready_when_deps_done() -> None:
    text = """
## Task: a
- status: DONE
## Task: b
- status: TODO
- depends-on: a
"""
    g = parse_task_graph(text)
    assert [t.name for t in g.ready()] == ["b"]


def test_validate_bad_status() -> None:
    g = parse_task_graph("## Task: x\n- status: WIP\n")
    problems = validate_task_graph(g)
    assert any("status 非法" in p for p in problems)


def test_validate_missing_dep() -> None:
    g = parse_task_graph("## Task: x\n- status: TODO\n- depends-on: ghost\n")
    problems = validate_task_graph(g)
    assert any("不存在的任务" in p for p in problems)


def test_validate_cycle() -> None:
    text = """
## Task: a
- status: TODO
- depends-on: b
## Task: b
- status: TODO
- depends-on: a
"""
    g = parse_task_graph(text)
    problems = validate_task_graph(g)
    assert any("循环依赖" in p for p in problems)


def test_validate_clean() -> None:
    g = parse_task_graph("## Task: a\n- status: DONE\n## Task: b\n- status: TODO\n- depends-on: a\n")
    assert validate_task_graph(g) == []
