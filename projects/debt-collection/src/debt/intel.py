# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-12 00:50:00 CST
"""情报库（ADR-006）：录入/管理关于债务人的新情报，标注来源可信度与策略影响。"""
from __future__ import annotations

from datetime import date

from debt.models import Intel, IntelCredibility, Store


def _row_to_intel(row: dict) -> Intel:
    return Intel(
        id=row["id"], debt_id=row["debt_id"], content=row["content"],
        source=row["source"] or "", credibility=IntelCredibility(row["credibility"])
        if row["credibility"] else IntelCredibility.MEDIUM,
        affects_strategy=bool(row["affects_strategy"]), created_at=row["created_at"] or "",
    )


def add_intel(store: Store, intel: Intel) -> int:
    """录入一条情报。created_at 为空则用今天。"""
    created = intel.created_at or date.today().isoformat()
    cur = store.conn.execute(
        """INSERT INTO intel(debt_id,content,source,credibility,affects_strategy,created_at)
           VALUES(?,?,?,?,?,?)""",
        (intel.debt_id, intel.content, intel.source, intel.credibility.value,
         1 if intel.affects_strategy else 0, created),
    )
    store.conn.commit()
    return int(cur.lastrowid)


def list_intel(store: Store, debt_id: int) -> list[Intel]:
    rows = store.conn.execute(
        "SELECT * FROM intel WHERE debt_id=? ORDER BY created_at, id", (debt_id,)
    ).fetchall()
    return [_row_to_intel(dict(r)) for r in rows]


def strategy_affecting_intel(store: Store, debt_id: int) -> list[Intel]:
    """返回会影响策略的情报（触发动态重算用）。"""
    return [it for it in list_intel(store, debt_id) if it.affects_strategy]
