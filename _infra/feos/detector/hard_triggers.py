# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Hard trigger detection."""

from __future__ import annotations

from .signals import DetectorSignals

HARD_TRIGGER_FIELDS = {
    "same_error_repeated_2_times",
    "tool_call_loop_detected",
    "local_agent_declares_no_new_strategy",
    "context_window_exceeded",
    "security_sensitive_failure",
    "architecture_decision_deadlock",
}


def detect_hard_triggers(signals: DetectorSignals) -> list[str]:
    hits = []
    if signals.execution.repeated_failure_count >= 2 or signals.execution.same_error_repeated:
        hits.append("same_error_repeated_2_times")
    if signals.agent.tool_call_loop:
        hits.append("tool_call_loop_detected")
    if signals.agent.declares_no_new_strategy:
        hits.append("local_agent_declares_no_new_strategy")
    if signals.context.context_window_exceeded:
        hits.append("context_window_exceeded")
    if signals.task.security_sensitive:
        hits.append("security_sensitive_failure")
    if signals.task.architecture_decision_deadlock:
        hits.append("architecture_decision_deadlock")
    return hits
