# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 15:30:00 CST

"""
AuditLogger - 审计日志记录器（FORGE Network 增量）

职责：
- 追加写入 runtime/audit.db
- 支持 tool_call、privacy、canary 等事件
- 查询接口（用于 forge network audit 等命令）

复用现有 FORGE 审计风格（轻量 SQLite）。
"""

from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import AuditEvent
from pathlib import Path as _Path  # 避免与内置 Path 冲突

DEFAULT_DB_PATH = Path("runtime/audit.db")


class AuditLogger:
    """审计日志记录器（线程安全追加写入）"""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None,
            )
            self._conn.row_factory = sqlite3.Row

            # 自动确保表存在（测试友好 + 生产安全）
            self._ensure_tables()
        return self._conn

    def _ensure_tables(self):
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                self._conn.executescript(f.read())
            self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def record(self, event: AuditEvent) -> str:
        """记录审计事件（追加）"""
        conn = self._get_conn()
        data = event.to_dict()

        conn.execute(
            """
            INSERT INTO tool_calls (id, event_type, server_id, tool_name, mode, decision, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["event_type"],
                data["server_id"],
                data["tool_name"],
                data["mode"],
                data["decision"],
                data["details"],
                data["created_at"],
            ),
        )
        return data["id"]

    def record_tool_call(
        self,
        server_id: str,
        tool_name: str,
        mode: str,
        decision: str,
        details: Dict[str, Any] | None = None,
    ) -> str:
        """便捷方法：记录工具调用"""
        event = AuditEvent(
            event_type="tool_call",
            server_id=server_id,
            tool_name=tool_name,
            mode=mode,
            decision=decision,
            details=details or {},
        )
        return self.record(event)

    def query(
        self,
        event_type: Optional[str] = None,
        mode: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """查询审计记录"""
        conn = self._get_conn()
        query = "SELECT * FROM tool_calls WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if mode:
            query += " AND mode = ?"
            params.append(mode)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_recent_canary_hits(self, limit: int = 10) -> List[Dict]:
        """快速查询 Canary 命中（可扩展）"""
        # 简化实现：通过 details 包含 canary 关键字
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT * FROM tool_calls 
            WHERE event_type LIKE '%canary%' OR details LIKE '%canary%'
            ORDER BY created_at DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
