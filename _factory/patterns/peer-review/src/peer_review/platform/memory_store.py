# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 01:40:00 CST
"""MemoryStore: 跨会话记忆 + 模型方案运行记录

职责：
- 记录每次评审的方案 ID、模型、耗时、成本、分歧度
- 支持 forge compare-plans 查询对比
- 使用 SQLite 持久化到 runtime/memory.db
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ModelRunRecord:
    """单次评审运行记录"""

    run_id: str
    case_hash: str
    plan_id: str
    models_used: dict[str, str]
    total_time_seconds: int
    total_cost_usd: float
    divergence_score: float
    human_quality_score: int | None = None
    adopted_by_user: bool | None = None
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class MemoryStore:
    """记忆存储：SQLite 持久化"""

    def __init__(self, db_path: Path | str = "runtime/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS model_runs (
                    run_id TEXT PRIMARY KEY,
                    case_hash TEXT NOT NULL,
                    plan_id TEXT NOT NULL,
                    models_used TEXT NOT NULL,
                    total_time_seconds INTEGER NOT NULL,
                    total_cost_usd REAL NOT NULL,
                    divergence_score REAL NOT NULL,
                    human_quality_score INTEGER,
                    adopted_by_user INTEGER,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def record_run(self, record: ModelRunRecord) -> None:
        """记录一次运行"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO model_runs (
                    run_id, case_hash, plan_id, models_used, total_time_seconds,
                    total_cost_usd, divergence_score, human_quality_score,
                    adopted_by_user, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.run_id or str(uuid.uuid4()),
                    record.case_hash,
                    record.plan_id,
                    str(record.models_used),
                    record.total_time_seconds,
                    record.total_cost_usd,
                    record.divergence_score,
                    record.human_quality_score,
                    1 if record.adopted_by_user else 0 if record.adopted_by_user is not None else None,
                    record.created_at or datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()

    def get_plan_comparison(self, days: int = 30) -> list[dict[str, Any]]:
        """查询最近 N 天各方案汇总数据"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT
                    plan_id,
                    COUNT(*) as run_count,
                    AVG(total_time_seconds) as avg_time_seconds,
                    AVG(total_cost_usd) as avg_cost_usd,
                    AVG(divergence_score) as avg_divergence,
                    AVG(human_quality_score) as avg_quality
                FROM model_runs
                WHERE created_at >= datetime('now', '-{} days')
                GROUP BY plan_id
                ORDER BY run_count DESC
                """.format(days)
            )
            return [dict(row) for row in cursor.fetchall()]
