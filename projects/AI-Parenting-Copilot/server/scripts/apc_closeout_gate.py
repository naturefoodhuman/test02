#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 23:45:00

"""Run APC closeout gate over sign-off and external evidence artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from server.app.ops.apc_closeout import build_apc_closeout_gate_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--signoff-dir", default="runtime/reports/rule-signoffs")
    parser.add_argument("--evidence-dir", default="runtime/reports/external-evidence")
    parser.add_argument("--output", default="runtime/reports/apc-closeout-gate.json")
    args = parser.parse_args()

    report = build_apc_closeout_gate_report(
        project_root=Path(args.project_root),
        signoff_dir=Path(args.signoff_dir),
        evidence_dir=Path(args.evidence_dir),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.to_json(), encoding="utf-8")
    print(report.to_json())


if __name__ == "__main__":
    main()
