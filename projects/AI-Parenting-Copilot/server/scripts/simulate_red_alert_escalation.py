#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-04 04:12:00

"""Run deterministic fake-channel red-alert escalation simulation."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from server.app.notification.escalation_report import simulate_red_alert_escalation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="runtime/reports/red-alert-escalation-report.json")
    args = parser.parse_args()

    report = asyncio.run(simulate_red_alert_escalation())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.to_json(), encoding="utf-8")
    print(report.to_json())
    if not report.trigger_only_payloads or not report.acknowledged:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
