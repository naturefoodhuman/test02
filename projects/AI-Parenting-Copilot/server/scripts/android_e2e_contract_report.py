#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 04:48:00

"""Generate Android/PowerSync MVP E2E contract report."""

from __future__ import annotations

import argparse
from pathlib import Path

from server.app.sync.e2e_contract import build_android_e2e_contract_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output", default="runtime/reports/android-e2e-contract-report.json")
    args = parser.parse_args()

    report = build_android_e2e_contract_report(Path(args.project_root))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.to_json(), encoding="utf-8")
    print(report.to_json())
    if not report.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
