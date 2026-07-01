# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Transition guard validators."""

from __future__ import annotations

from typing import Any

from _infra.feos.models.enums import CaseStatus


def validate_transition_context(current: CaseStatus, target: CaseStatus, context: dict[str, Any] | None = None) -> tuple[bool, str | None]:
    ctx = context or {}
    if target == CaseStatus.GRAPH_BUILDING and int(ctx.get("evidence_count", 1)) <= 0:
        return False, "GraphBuilding requires evidence_count > 0"
    if target == CaseStatus.CONTEXT_COMPILING and ctx.get("policy_allowed") is False:
        return False, "ContextCompiling requires policy_allowed != false"
    if target == CaseStatus.EXECUTING and ctx.get("approved_plan") is False:
        return False, "Executing requires approved_plan != false"
    return True, None
