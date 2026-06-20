# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-20 21:35:00 CST
"""Legacy orchestrator compatibility shim.

SSOT:
- 当前真实执行入口：peer_review.graph.execution.run_langgraph_review
- 旧 Agno 大实现已迁移到：_obsolete/_factory/patterns/peer-review/src/peer_review/orchestrator.py

本文件只保留极薄兼容层，避免历史测试、`debt continue`、旧文档中的
`from peer_review.orchestrator import ...` 在仓库清理后直接 ImportError。
禁止在本文件恢复 Agno 旧实现；新功能必须进入 graph/* 或 platform/*。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def run_langgraph_review(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Lazy wrapper for the current LangGraph execution entry.

    Lazy import keeps this compatibility module importable even in minimal audit
    environments where LangGraph/runtime dependencies are not installed yet.
    """
    from peer_review.graph.execution import run_langgraph_review as _run_langgraph_review

    return _run_langgraph_review(*args, **kwargs)


def continue_langgraph_review(
    thread_id: str,
    project_root: Path | None = None,
    use_live: bool = True,
    **_: Any,
) -> dict[str, Any]:
    """Compatibility placeholder for the retired HITL resume API.

    The historical Agno-era implementation was moved to `_obsolete/` during repository
    cleanup. The current graph execution path does not expose a durable resume API yet.
    Existing tests intentionally assert that an unknown thread raises ValueError.
    """
    raise ValueError(
        "HITL resume via peer_review.orchestrator is retired; "
        f"no active checkpoint found for thread_id={thread_id!r}. "
        "Use peer_review.graph.execution.run_langgraph_review for new runs."
    )


def build_review_team(experts_dir: Path):
    """Lazy compatibility wrapper for old Agno team construction.

    Kept only for legacy verification scripts. It imports Agno-dependent code lazily so
    normal LangGraph imports do not require Agno.
    """
    from peer_review.team_orchestrator import build_review_team as _build_review_team

    return _build_review_team(experts_dir)


__all__ = ["run_langgraph_review", "continue_langgraph_review", "build_review_team"]
