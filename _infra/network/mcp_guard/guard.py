# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 11:02:00

"""
MCP Guard core abstraction (E2-C4-S1-T1).

This is the common PreToolUse entry point. Later tasks will plug mode policies,
high-risk approvals and argument validators into this class. The current task
establishes:
- stable request / result / decision models
- auditable ``check(call) -> GuardDecision`` interface
- schema hash verification integration
"""

from __future__ import annotations

from typing import Any, Mapping

from ..audit_log.logger import AuditLogger
from ..exceptions import MCPSchemaChangedError
from .approval import HighRiskApprovalEngine
from .argument_validator import ArgumentValidator
from .mode_policy import ModePolicyEngine
from .models import GuardDecision, MCPToolCall, PolicyDecision
from .schema_validator import MCPToolSchemaValidator


class MCPGuard:
    """Core MCP PreToolUse guard."""

    def __init__(
        self,
        audit_logger: AuditLogger | None = None,
        schema_validator: MCPToolSchemaValidator | None = None,
        mode_policy: ModePolicyEngine | None = None,
        approval_engine: HighRiskApprovalEngine | None = None,
        argument_validator: ArgumentValidator | None = None,
        default_decision: PolicyDecision = PolicyDecision.ALLOW,
        enable_mode_policy: bool = True,
        enable_approval: bool = True,
        enable_argument_validation: bool = True,
    ):
        self.audit_logger = audit_logger or AuditLogger()
        self.schema_validator = schema_validator or MCPToolSchemaValidator()
        self.mode_policy = mode_policy if mode_policy is not None else (ModePolicyEngine.from_config() if enable_mode_policy else None)
        self.approval_engine = approval_engine if approval_engine is not None else (HighRiskApprovalEngine() if enable_approval else None)
        self.argument_validator = argument_validator if argument_validator is not None else (ArgumentValidator() if enable_argument_validation else None)
        self.default_decision = default_decision

    def check(self, call: MCPToolCall) -> GuardDecision:
        """
        Check a tool call and return an auditable decision.

        Current behavior:
        - If call.schema is provided, verify it against the schema hash store.
        - Schema changes are denied and audited.
        - Otherwise return default_decision (allow by default for this core task).
        """
        details: dict[str, Any] = {
            "reason": "core_guard_default",
            "arg_keys": sorted(str(key) for key in call.args.keys()),
        }
        if call.trace_id:
            details["trace_id"] = call.trace_id

        if self.mode_policy is not None:
            policy_result = self.mode_policy.evaluate(call)
            details["mode_policy_reason"] = policy_result.reason
            if not policy_result.allowed:
                details["reason"] = "mode_policy_denied"
                audit_id = self._audit(call, PolicyDecision.DENY, details)
                return GuardDecision(
                    decision=PolicyDecision.DENY,
                    reason=policy_result.reason,
                    server_id=call.server_id,
                    tool_name=call.tool_name,
                    mode=call.mode,
                    audit_event_id=audit_id,
                    details=details,
                )

        if self.argument_validator is not None:
            arg_result = self.argument_validator.validate(call)
            details["argument_validation_reason"] = arg_result.reason
            details["argument_length"] = arg_result.arg_length
            if not arg_result.allowed:
                details["reason"] = "argument_validation_denied"
                details["argument_matches"] = list(arg_result.matches)
                audit_id = self._audit(call, PolicyDecision.DENY, details)
                return GuardDecision(
                    decision=PolicyDecision.DENY,
                    reason=arg_result.reason,
                    server_id=call.server_id,
                    tool_name=call.tool_name,
                    mode=call.mode,
                    audit_event_id=audit_id,
                    details=details,
                )

        if call.schema is not None:
            try:
                result = self.schema_validator.verify_schema(call.server_id, call.tool_name, call.schema)
                details["schema_hash"] = result.schema_hash
                details["schema_status"] = result.status
            except MCPSchemaChangedError as exc:
                details.update(
                    {
                        "reason": "schema_changed",
                        "old_hash": exc.details.get("old_hash"),
                        "new_hash": exc.details.get("new_hash"),
                    }
                )
                audit_id = self._audit(call, PolicyDecision.DENY, details)
                return GuardDecision(
                    decision=PolicyDecision.DENY,
                    reason="schema_changed",
                    server_id=call.server_id,
                    tool_name=call.tool_name,
                    mode=call.mode,
                    audit_event_id=audit_id,
                    details=details,
                )

        if self.approval_engine is not None:
            approval_check = self.approval_engine.check_requires_approval(call)
            if approval_check.requires_approval:
                details["high_risk"] = True
                details["approval_reason"] = approval_check.reason
                details["matched_terms"] = list(approval_check.matched_terms)
                approval_result = self.approval_engine.request_approval(call, approval_check)
                details["approved"] = approval_result.approved
                details["reason"] = approval_result.reason
                decision = PolicyDecision.ALLOW if approval_result.approved else PolicyDecision.DENY
                audit_id = self._audit(call, decision, details)
                return GuardDecision(
                    decision=decision,
                    reason=approval_result.reason,
                    server_id=call.server_id,
                    tool_name=call.tool_name,
                    mode=call.mode,
                    audit_event_id=audit_id,
                    details=details,
                )

        decision = self.default_decision
        reason = "default_allow" if decision == PolicyDecision.ALLOW else "default_policy"
        details["reason"] = reason
        audit_id = self._audit(call, decision, details)
        return GuardDecision(
            decision=decision,
            reason=reason,
            server_id=call.server_id,
            tool_name=call.tool_name,
            mode=call.mode,
            audit_event_id=audit_id,
            details=details,
        )

    def verify_schema(self, server_id: str, tool_name: str, schema: Mapping[str, Any]) -> bool:
        """Verify schema against pinned hash; returns True or raises on change."""
        self.schema_validator.verify_schema(server_id, tool_name, schema)
        return True

    def record_schema(self, server_id: str, tool_name: str, schema: Mapping[str, Any]) -> None:
        """Explicitly pin/update schema hash."""
        self.schema_validator.record_schema(server_id, tool_name, schema)

    def _audit(self, call: MCPToolCall, decision: PolicyDecision, details: Mapping[str, Any]) -> str:
        return self.audit_logger.record_tool_call(
            server_id=call.server_id,
            tool_name=call.tool_name,
            mode=call.mode,
            decision=decision.value,
            details=dict(details),
        )


__all__ = ["MCPGuard"]
