# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-11 22:10:00 CST
"""ingestion CLI：把资料目录批量转为结构化 Markdown+JSON。

用法：
  python -m ingestion.cli <输入路径> -o <输出目录>
  python -m ingestion.cli ./samples -o ./out
零三方依赖（仅标准库 argparse），保证任何环境可跑。
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ingestion.pipeline import ingest_dir, ingest_file, save_doc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ingestion", description="工厂通用资料整理：多格式→结构化")
    parser.add_argument("input", help="输入文件或目录")
    parser.add_argument("-o", "--out", default="./ingestion_out", help="输出目录")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细日志")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"❌ 输入不存在: {in_path}")
        return 1

    docs = [ingest_file(in_path)] if in_path.is_file() else ingest_dir(in_path)
    if not docs:
        print("（没有可处理的文件）")
        return 0

    print(f"📦 共处理 {len(docs)} 个文件：")
    for d in docs:
        md_path, json_path = save_doc(d, args.out)
        proc = d.meta.get("processor", "?")
        flag = "⚠️ 降级" if any("降级" in w or "占位" in w for w in d.warnings) else "✅"
        print(f"  {flag} [{d.source_type.value:6s}] {Path(d.source_path).name}  →  {proc}")
        for w in d.warnings:
            print(f"        · {w}")
    print(f"📁 输出已写入: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
