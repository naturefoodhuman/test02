# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Evidence importance scoring."""

from __future__ import annotations

from _infra.feos.models.enums import EvidenceType

IMPORTANCE_WEIGHTS = {
    EvidenceType.STACK_TRACE: 0.95,
    EvidenceType.FAILING_TEST: 0.95,
    EvidenceType.GIT_DIFF: 0.90,
    EvidenceType.TOOL_CALL_TRACE: 0.90,
    EvidenceType.MCP_CALL_TRACE: 0.90,
    EvidenceType.CONFIG: 0.80,
    EvidenceType.DEPENDENCY_LOCK: 0.80,
    EvidenceType.RUNTIME_ENV: 0.70,
    EvidenceType.ARCHITECTURE_DOC: 0.65,
    EvidenceType.AGENT_PROMPT: 0.60,
    EvidenceType.PREVIOUS_ATTEMPT: 0.60,
    EvidenceType.USER_INPUT: 0.60,
    EvidenceType.LOG: 0.55,
    EvidenceType.CODE: 0.50,
    EvidenceType.OTHER: 0.30,
}


def importance_for_type(evidence_type: EvidenceType | str) -> float:
    try:
        ev_type = EvidenceType(evidence_type)
    except Exception:
        ev_type = EvidenceType.OTHER
    return IMPORTANCE_WEIGHTS.get(ev_type, 0.30)
