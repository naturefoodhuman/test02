# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Architecture-defined FEOS case transitions."""

from __future__ import annotations

from _infra.feos.models.enums import CaseStatus

MAIN_PATH = [
    CaseStatus.DRAFT,
    CaseStatus.CREATED,
    CaseStatus.COLLECTING_EVIDENCE,
    CaseStatus.GRAPH_BUILDING,
    CaseStatus.INVESTIGATING,
    CaseStatus.POLICY_CHECKING,
    CaseStatus.CONTEXT_COMPILING,
    CaseStatus.PACKAGE_GENERATED,
    CaseStatus.WAITING_HUMAN_EXPORT,
    CaseStatus.WAITING_EXTERNAL_RESPONSE,
    CaseStatus.RESPONSE_IMPORTED,
    CaseStatus.PARSING_RESPONSE,
    CaseStatus.VERIFYING,
    CaseStatus.PLANNING_EXECUTION,
    CaseStatus.EXECUTING,
    CaseStatus.EVALUATING_OUTCOME,
]

TERMINAL_TRANSITIONS = {
    CaseStatus.EVALUATING_OUTCOME: {CaseStatus.RESOLVED, CaseStatus.UNRESOLVED, CaseStatus.ABANDONED},
    CaseStatus.UNRESOLVED: {CaseStatus.COLLECTING_EVIDENCE, CaseStatus.DISTILLING_KNOWLEDGE, CaseStatus.ARCHIVED},
    CaseStatus.RESOLVED: {CaseStatus.DISTILLING_KNOWLEDGE, CaseStatus.ARCHIVED},
    CaseStatus.ABANDONED: {CaseStatus.ARCHIVED},
    CaseStatus.DISTILLING_KNOWLEDGE: {CaseStatus.ARCHIVED},
}

ALLOWED_TRANSITIONS: dict[CaseStatus, set[CaseStatus]] = {
    current: {next_status} for current, next_status in zip(MAIN_PATH, MAIN_PATH[1:])
}
for current, targets in TERMINAL_TRANSITIONS.items():
    ALLOWED_TRANSITIONS.setdefault(current, set()).update(targets)
