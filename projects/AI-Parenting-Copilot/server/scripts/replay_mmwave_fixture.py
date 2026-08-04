#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 04:45:00

"""Replay an mmWave JSONL fixture through parser/mapper contracts."""

from __future__ import annotations

import argparse
from pathlib import Path

from server.app.mmwave.replay import replay_mmwave_fixture


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="tests/fixtures/radar_frames.jsonl")
    parser.add_argument("--output", default="runtime/reports/mmwave-replay-report.json")
    parser.add_argument("--topic", default="baby/radar/telemetry")
    parser.add_argument("--baby-id", default="baby-replay")
    parser.add_argument("--family-id", default="family-replay")
    args = parser.parse_args()

    report = replay_mmwave_fixture(
        Path(args.fixture),
        topic=args.topic,
        baby_id=args.baby_id,
        family_id=args.family_id,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.to_json(), encoding="utf-8")
    print(report.to_json())
    if report.total_frames == 0:
        raise SystemExit("No frames replayed")


if __name__ == "__main__":
    main()
