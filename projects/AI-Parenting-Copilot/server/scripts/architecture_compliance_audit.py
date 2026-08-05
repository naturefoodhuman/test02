#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 02:20:00

"""Generate architecture compliance audit report."""

from __future__ import annotations

import argparse
from pathlib import Path

from server.app.ops.architecture_compliance import (
    build_architecture_compliance_report,
    write_architecture_compliance_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-dir", default="runtime/reports")
    args = parser.parse_args()

    report = build_architecture_compliance_report(Path(args.project_root))
    json_path, md_path = write_architecture_compliance_report(
        report,
        output_dir=Path(args.output_dir),
    )
    print(f"json={json_path}")
    print(f"markdown={md_path}")
    print(report.to_json())
    if report.status == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
