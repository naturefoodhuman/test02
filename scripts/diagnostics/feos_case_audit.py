#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _infra.feos.bootstrap import bootstrap_feos
from _infra.feos.observability import diagnose_case


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    ctx = bootstrap_feos()
    report = diagnose_case(ctx.workspace, args.case_id)
    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        print(f"case={report.case_id} ok={report.ok}")
        for e in report.errors:
            print(f"ERROR: {e}")
        for w in report.warnings:
            print(f"WARN: {w}")
    return 0 if report.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
