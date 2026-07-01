# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Basic deterministic relation extraction placeholder."""

from __future__ import annotations

from _infra.feos.models import Evidence


def basic_relations(evidence: list[Evidence]) -> list[tuple[str, str, str]]:
    return [(ev.id, f"fact_{ev.id}", "supports") for ev in evidence]
