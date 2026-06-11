# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-10 23:03:36 CST
"""五阶段状态机定义与流转校验（架构书第 4 章）。

设计理由：把"阶段顺序、进入条件、退出产物、Gate"用数据结构固化，
让 CLI / Hooks / Orchestrator 有一个唯一可信的真相源，避免散落在 Prompt 里。
"""
from __future__ import annotations

from dataclasses import dataclass


# 五阶段顺序（DISCOVERY → SPEC → BUILD → HARDEN → RETRO）
PHASES: tuple[str, ...] = ("DISCOVERY", "SPEC", "BUILD", "HARDEN", "RETRO")


@dataclass(frozen=True)
class PhaseDef:
    """单个阶段的定义。"""

    name: str
    entry_docs: tuple[str, ...]   # 进入本阶段前应已存在的文档
    exit_artifacts: tuple[str, ...]  # 本阶段必须产出的文档
    hitl_gate: str                # 退出时的人工门控编号


PHASE_DEFS: dict[str, PhaseDef] = {
    "DISCOVERY": PhaseDef(
        name="DISCOVERY",
        entry_docs=(),
        exit_artifacts=("docs/DISCOVERY.md",),
        hitl_gate="GATE-1",
    ),
    "SPEC": PhaseDef(
        name="SPEC",
        entry_docs=("docs/DISCOVERY.md",),
        exit_artifacts=(
            "docs/SPEC.md",
            "docs/TASK_GRAPH.md",
            "docs/RISK.md",
        ),
        hitl_gate="GATE-2",
    ),
    "BUILD": PhaseDef(
        name="BUILD",
        entry_docs=("docs/SPEC.md", "docs/TASK_GRAPH.md"),
        exit_artifacts=("docs/BUILD_LOG.md",),
        hitl_gate="",  # BUILD 无独立 HITL，靠 Hooks 门控
    ),
    "HARDEN": PhaseDef(
        name="HARDEN",
        entry_docs=("docs/SPEC.md",),
        exit_artifacts=("docs/harden/SECURITY_REVIEW.md",),
        hitl_gate="GATE-4",
    ),
    "RETRO": PhaseDef(
        name="RETRO",
        entry_docs=(),
        exit_artifacts=(),  # 产物写到 _factory/lessons/
        hitl_gate="GATE-5",
    ),
}


def next_phase(current: str) -> str | None:
    """返回下一阶段名；已是最后阶段则返回 None。

    Raises:
        ValueError: 当 current 不是合法阶段名。
    """
    if current not in PHASES:
        raise ValueError(f"未知阶段：{current}")
    idx = PHASES.index(current)
    if idx + 1 >= len(PHASES):
        return None
    return PHASES[idx + 1]


def can_advance(current: str, existing_files: set[str]) -> tuple[bool, list[str]]:
    """判断能否从 current 阶段前进（即当前阶段的退出产物是否齐全）。

    Args:
        current: 当前阶段名。
        existing_files: 项目里已存在的相对路径集合。

    Returns:
        (是否可前进, 缺失的产物列表)
    """
    if current not in PHASE_DEFS:
        raise ValueError(f"未知阶段：{current}")
    pdef = PHASE_DEFS[current]
    missing = [f for f in pdef.exit_artifacts if f not in existing_files]
    return (len(missing) == 0, missing)
