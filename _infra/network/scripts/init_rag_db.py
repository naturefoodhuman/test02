#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 16:55:00

"""Initialize local RAG DB."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from _infra.network.local_rag.store import init_rag_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize FORGE Network RAG DB")
    parser.add_argument("--db", default="runtime/rag.db")
    args = parser.parse_args()
    path = init_rag_db(args.db)
    print(f"✅ rag.db initialized: {path}")


if __name__ == "__main__":
    main()
