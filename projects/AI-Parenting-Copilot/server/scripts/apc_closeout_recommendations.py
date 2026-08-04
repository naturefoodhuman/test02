#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 23:58:00

"""Generate APC closeout recommendation report."""

from __future__ import annotations

import argparse
from pathlib import Path

from server.app.ops.closeout_recommendation import (
    build_closeout_recommendation_report,
    write_closeout_recommendation_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--signoff-dir", default="runtime/reports/rule-signoffs")
    parser.add_argument("--evidence-dir", default="runtime/reports/external-evidence")
    parser.add_argument("--output-dir", default="runtime/reports")
    args = parser.parse_args()

    report = build_closeout_recommendation_report(
        project_root=Path(args.project_root),
        signoff_dir=Path(args.signoff_dir),
        evidence_dir=Path(args.evidence_dir),
    )
    json_path, md_path = write_closeout_recommendation_report(
        report,
        output_dir=Path(args.output_dir),
    )
    print(f"json={json_path}")
    print(f"markdown={md_path}")
    print(report.to_json())


if __name__ == "__main__":
    main()
