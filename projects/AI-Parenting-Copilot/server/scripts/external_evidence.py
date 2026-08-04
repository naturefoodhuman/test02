#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 23:20:00

"""Generate or verify external validation evidence artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from server.app.ops.external_evidence import (
    load_evidence_file,
    validate_external_evidence,
    write_evidence_template,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-task")
    parser.add_argument("--evidence")
    parser.add_argument("--output-dir", default="runtime/reports/external-evidence")
    args = parser.parse_args()

    if args.template_task:
        path = write_evidence_template(args.template_task, output_dir=Path(args.output_dir))
        print(f"template={path}")
        return
    if not args.evidence:
        raise SystemExit("Provide --template-task or --evidence")
    evidence = load_evidence_file(args.evidence)
    result = validate_external_evidence(evidence)
    print(result.to_json())
    if not result.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
