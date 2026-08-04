#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 22:10:00

"""Generate external validation plan for remaining blockers."""

from __future__ import annotations

import argparse
from pathlib import Path

from server.app.ops.external_validation import (
    build_external_validation_plan,
    write_external_validation_plan,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="runtime/reports")
    args = parser.parse_args()

    plan = build_external_validation_plan()
    json_path, md_path = write_external_validation_plan(plan, output_dir=Path(args.output_dir))
    print(f"json={json_path}")
    print(f"markdown={md_path}")
    print(plan.to_json())


if __name__ == "__main__":
    main()
