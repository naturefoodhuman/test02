#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 20:32:00

"""
Initialize encrypted pii_map.db (FORGE Network incremental, E5-C6-S1-T2).

Usage:
    export PII_MAP_ENCRYPTION_KEY='at-least-16-chars'
    python _infra/network/scripts/init_pii_map_db.py
    python _infra/network/scripts/init_pii_map_db.py --db runtime/pii_map.db --require-sqlcipher
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from _infra.network.privacy_gateway.pii_map_db import PIIMapDB


def init_pii_map_db(db_path: Path = Path("runtime/pii_map.db"), require_sqlcipher: bool = False) -> PIIMapDB:
    db = PIIMapDB.from_env(db_path=db_path, require_sqlcipher=require_sqlcipher)
    print(f"✅ pii_map.db 已初始化：{db.db_path}")
    print(f"   DB driver：{db.driver_name}")
    return db


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize encrypted PII map DB")
    parser.add_argument("--db", default="runtime/pii_map.db", help="PII map DB path")
    parser.add_argument(
        "--require-sqlcipher",
        action="store_true",
        help="Fail if SQLCipher Python driver is unavailable",
    )
    args = parser.parse_args()
    init_pii_map_db(Path(args.db), require_sqlcipher=args.require_sqlcipher)


if __name__ == "__main__":
    main()
