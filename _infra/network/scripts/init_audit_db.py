#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 15:25:00 CST

"""
初始化 audit.db（FORGE Network 增量）

用法：
    python _infra/network/scripts/init_audit_db.py
"""

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent.parent / "audit_log" / "schema.sql"
DB_PATH = Path("runtime/audit.db")


def init_audit_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()

    print(f"✅ audit.db 已初始化：{db_path}")
    print(f"   表结构来源：{SCHEMA_PATH}")


if __name__ == "__main__":
    init_audit_db()
