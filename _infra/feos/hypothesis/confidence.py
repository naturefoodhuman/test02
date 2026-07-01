# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations


def compute_confidence(support_count: int, refute_count: int) -> float:
    total = support_count + refute_count
    if total == 0:
        return 0.0
    return max(0.0, min(1.0, support_count / total))
