# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
"""TASK_GRAPH.md 解析与校验（机器可读格式）。

为什么自己写解析而不用 YAML：架构书 7.1 定义的 TASK_GRAPH 是
"## Task: name" + "- key: value" 的 Markdown 格式，对人和 Agent 都友好，
且不依赖额外库。这里做一个零依赖的健壮解析器，便于 Hooks 与 CLI 复用。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

VALID_STATUS = {"TODO", "IN_PROGRESS", "DONE", "BLOCKED"}

_TASK_HEADER = re.compile(r"^##\s+Task:\s*(?P<name>.+?)\s*$")
_KV = re.compile(r"^-\s*(?P<key>[A-Za-z0-9_\-]+)\s*:\s*(?P<val>.*?)\s*$")


@dataclass
class Task:
    """单个任务节点。"""

    name: str
    status: str = "TODO"
    depends_on: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)


@dataclass
class TaskGraph:
    """整张任务图。"""

    tasks: list[Task] = field(default_factory=list)

    def by_name(self, name: str) -> Task | None:
        """按名查找任务。"""
        for t in self.tasks:
            if t.name == name:
                return t
        return None

    def in_progress(self) -> list[Task]:
        """返回所有 IN_PROGRESS 任务（pre-commit 用于拦截）。"""
        return [t for t in self.tasks if t.status == "IN_PROGRESS"]

    def ready(self) -> list[Task]:
        """返回所有依赖已 DONE 且自身为 TODO 的可执行任务。"""
        done = {t.name for t in self.tasks if t.status == "DONE"}
        out: list[Task] = []
        for t in self.tasks:
            if t.status == "TODO" and all(d in done for d in t.depends_on):
                out.append(t)
        return out


def parse_task_graph(text: str) -> TaskGraph:
    """解析 TASK_GRAPH.md 文本为 TaskGraph。

    Args:
        text: TASK_GRAPH.md 的完整文本。

    Returns:
        TaskGraph 实例。
    """
    graph = TaskGraph()
    current: Task | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        m = _TASK_HEADER.match(line)
        if m:
            current = Task(name=m.group("name"))
            graph.tasks.append(current)
            continue
        if current is None:
            continue
        kv = _KV.match(line)
        if not kv:
            continue
        key, val = kv.group("key"), kv.group("val")
        if key == "status":
            current.status = val
        elif key in ("depends-on", "depends_on"):
            # 支持逗号分隔的多依赖
            current.depends_on = [d.strip() for d in val.split(",") if d.strip()]
        else:
            current.attrs[key] = val
    return graph


def load_task_graph(path: str | Path) -> TaskGraph:
    """从文件加载 TASK_GRAPH。"""
    p = Path(path)
    return parse_task_graph(p.read_text(encoding="utf-8"))


def validate_task_graph(graph: TaskGraph) -> list[str]:
    """校验任务图，返回问题列表（空列表=通过）。

    校验项：
    - status 合法
    - depends-on 指向存在的任务
    - 无循环依赖
    """
    problems: list[str] = []
    names = {t.name for t in graph.tasks}

    for t in graph.tasks:
        if t.status not in VALID_STATUS:
            problems.append(f"任务 '{t.name}' 的 status 非法：{t.status}")
        for d in t.depends_on:
            if d not in names:
                problems.append(f"任务 '{t.name}' 依赖不存在的任务：{d}")

    # 循环依赖检测（DFS）
    color: dict[str, int] = {}  # 0=白 1=灰 2=黑

    def dfs(name: str) -> bool:
        color[name] = 1
        t = graph.by_name(name)
        if t:
            for d in t.depends_on:
                if d not in names:
                    continue
                c = color.get(d, 0)
                if c == 1:
                    return True
                if c == 0 and dfs(d):
                    return True
        color[name] = 2
        return False

    for t in graph.tasks:
        if color.get(t.name, 0) == 0:
            if dfs(t.name):
                problems.append(f"检测到循环依赖，涉及任务：{t.name}")
                break

    return problems
