#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 21:45:00

"""Generate aggregate P0 release-readiness report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))



def main() -> None:
    from server.app.ops.p0_readiness import build_p0_readiness_report
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output", default="runtime/reports/p0-readiness-report.json")
    args = parser.parse_args()

    report = build_p0_readiness_report(Path(args.project_root))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.to_json(), encoding="utf-8")
    print(report.to_json())
    if report.automated_status == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
