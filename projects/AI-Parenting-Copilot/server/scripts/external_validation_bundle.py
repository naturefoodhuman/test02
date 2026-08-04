#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-05 01:25:00

"""Generate external validation bundle for remaining APC blockers."""

from __future__ import annotations

import argparse
from pathlib import Path

from server.app.ops.external_validation_bundle import build_external_validation_bundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="runtime/reports/external-validation-bundle")
    args = parser.parse_args()

    bundle = build_external_validation_bundle(output_dir=Path(args.output_dir))
    print(bundle.to_json())


if __name__ == "__main__":
    main()
