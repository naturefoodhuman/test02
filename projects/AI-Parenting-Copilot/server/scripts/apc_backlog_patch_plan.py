#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 01:55:00

"""Generate dry-run TASK_BACKLOG patch plan from closeout recommendations."""

from __future__ import annotations

import argparse
from pathlib import Path

from server.app.ops.backlog_patch_plan import build_backlog_patch_plan, write_backlog_patch_plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-dir", default="runtime/reports")
    args = parser.parse_args()

    plan = build_backlog_patch_plan(project_root=Path(args.project_root))
    json_path, md_path = write_backlog_patch_plan(plan, output_dir=Path(args.output_dir))
    print(f"json={json_path}")
    print(f"markdown={md_path}")
    print(plan.to_json())


if __name__ == "__main__":
    main()
