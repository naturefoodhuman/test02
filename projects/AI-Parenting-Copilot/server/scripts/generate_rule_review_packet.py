#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-03 11:05:00

"""Generate rule review packet artifacts for human sign-off."""

from __future__ import annotations

import argparse
from pathlib import Path

from server.app.rule_engine.review_packet import build_rule_review_packet, write_rule_review_packet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-dir", default="runtime/reports")
    args = parser.parse_args()

    packet = build_rule_review_packet(Path(args.project_root))
    json_path, md_path = write_rule_review_packet(packet, output_dir=args.output_dir)
    print(f"json={json_path}")
    print(f"markdown={md_path}")
    print(f"review_status={packet.review_status}")
    failed = [case for case in packet.golden_cases if not case.passed]
    if failed:
        raise SystemExit(f"Golden case failures: {[case.name for case in failed]}")


if __name__ == "__main__":
    main()
