# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 14:54:47

"""
Claude Code PreToolUse hook entry point (E6-C3-S1-T1).

Reads a JSON event from stdin, converts it into MCPToolCall, runs MCPGuard, and
prints a compact JSON decision:

    {"allow": true|false, "reason": "..."}

The parser is intentionally tolerant because hook event field names can differ
between clients. Supported aliases:
- tool_name / tool / name
- server_id / server_name / server
- args / arguments / input
- mode / FORGE_MCP_MODE env var
- schema / tool_schema

High-risk approvals are non-interactive by default in hook mode to avoid hanging
on stdin after the event is consumed. Set FORGE_MCP_APPROVAL=yes for one-shot
approval in tests/manual runs.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Mapping, Sequence

from ..approval import HighRiskApprovalEngine
from ..guard import MCPGuard
from ..models import MCPToolCall, PolicyDecision


def _first(payload: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in payload and payload[name] is not None:
            return payload[name]
    return default


def _extract_payload(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    # Some hooks wrap the actual tool call in a nested payload.
    for key in ("tool_call", "toolCall", "request", "event"):
        value = raw.get(key)
        if isinstance(value, Mapping):
            merged = dict(raw)
            merged.update(value)
            return merged
    return raw


def parse_hook_payload(payload: Mapping[str, Any]) -> MCPToolCall:
    data = _extract_payload(payload)
    tool_name = str(_first(data, "tool_name", "tool", "name", default="unknown"))
    server_id = str(_first(data, "server_id", "server_name", "server", default="unknown"))
    args = _first(data, "args", "arguments", "input", default={})
    if not isinstance(args, Mapping):
        args = {"value": args}
    mode = str(_first(data, "mode", default=os.getenv("FORGE_MCP_MODE", "research")))
    schema = _first(data, "schema", "tool_schema", default=None)
    trace_id = _first(data, "trace_id", "traceId", default=None)
    return MCPToolCall(
        server_id=server_id,
        tool_name=tool_name,
        args=args,
        mode=mode,  # type: ignore[arg-type]
        schema=schema if isinstance(schema, Mapping) else None,
        trace_id=str(trace_id) if trace_id is not None else None,
    )


def build_hook_guard() -> MCPGuard:
    approval_response = os.getenv("FORGE_MCP_APPROVAL", "")
    approval_engine = HighRiskApprovalEngine(input_func=lambda _prompt: approval_response)
    return MCPGuard(approval_engine=approval_engine)


def handle_hook_event(payload: Mapping[str, Any], guard: MCPGuard | None = None) -> dict[str, Any]:
    guard = guard or build_hook_guard()
    call = parse_hook_payload(payload)
    decision = guard.check(call)
    return {
        "allow": decision.decision == PolicyDecision.ALLOW,
        "reason": decision.reason,
        "decision": decision.decision.value,
        "server_id": decision.server_id,
        "tool_name": decision.tool_name,
        "audit_event_id": decision.audit_event_id,
    }


def main(argv: Sequence[str] | None = None) -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw or "{}")
        if not isinstance(payload, Mapping):
            raise ValueError("hook payload must be a JSON object")
        result = handle_hook_event(payload)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["allow"] else 2
    except Exception as exc:  # fail closed
        print(
            json.dumps(
                {
                    "allow": False,
                    "reason": f"hook_error:{type(exc).__name__}",
                    "decision": "deny",
                    "error": str(exc),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
