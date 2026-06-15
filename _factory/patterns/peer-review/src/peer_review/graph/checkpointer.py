# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 02:00:00 CST
"""LangGraph SqliteSaver 检查点初始化

职责：
- 为 LangGraph 图执行提供状态持久化
- 支持中断恢复（HITL）
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


def make_checkpointer(db_path: Path | str = "runtime/checkpoints.sqlite") -> SqliteSaver:
    """创建并返回 SqliteSaver 实例

    Args:
        db_path: SQLite 数据库路径，用于存储图执行检查点

    Returns:
        SqliteSaver 实例
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    return SqliteSaver(conn)
