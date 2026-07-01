# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""FEOS case state machine."""

from __future__ import annotations

from typing import Any

from _infra.feos.errors import FEOSStateError
from _infra.feos.models.enums import CaseStatus

from .transitions import ALLOWED_TRANSITIONS, MAIN_PATH
from .validators import validate_transition_context


class StateTransitionError(FEOSStateError):
    """Invalid FEOS state transition."""


class CaseStateMachine:
    def can_transition(self, current: CaseStatus | str, target: CaseStatus | str, context: dict[str, Any] | None = None) -> bool:
        try:
            self.validate(current, target, context=context)
            return True
        except StateTransitionError:
            return False

    def validate(self, current: CaseStatus | str, target: CaseStatus | str, context: dict[str, Any] | None = None) -> None:
        cur = CaseStatus(current)
        tgt = CaseStatus(target)
        if cur == CaseStatus.ARCHIVED:
            raise StateTransitionError("Archived cases cannot transition")
        if tgt not in ALLOWED_TRANSITIONS.get(cur, set()):
            raise StateTransitionError(f"illegal transition: {cur.value} -> {tgt.value}")
        ok, reason = validate_transition_context(cur, tgt, context=context)
        if not ok:
            raise StateTransitionError(reason or f"guard rejected transition: {cur.value} -> {tgt.value}")

    def main_path(self) -> list[CaseStatus]:
        return list(MAIN_PATH)
