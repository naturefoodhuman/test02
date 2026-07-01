# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations


def aggregate_risk(errors: list[str], warnings: list[str]) -> str:
    if errors: return "high"
    if warnings: return "medium"
    return "low"
