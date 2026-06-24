#!/usr/bin/env python3
# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 16:05:00

"""Root wrapper for _infra/network/scripts/run_playwright_action.py."""

from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "_infra" / "network" / "scripts" / "run_playwright_action.py"), run_name="__main__")
