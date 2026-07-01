# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import Evidence


class ContextSelector:
    def select_evidence(self, evidence: list[Evidence], limit: int = 20) -> tuple[list[Evidence], list[dict]]:
        ordered = sorted(evidence, key=lambda ev: ev.quality.importance, reverse=True)
        selected = ordered[:limit]
        omitted = [{"id": ev.id, "reason": "low_priority_or_over_limit"} for ev in ordered[limit:]]
        return selected, omitted
