# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 04:25:00


"""Dose Interceptor for LLM/Copilot free text."""

from __future__ import annotations

import re
from dataclasses import dataclass

from server.app.observability.audit import AuditActor, AuditRecord, AuditSink

DOSE_RE = re.compile(r"(?P<dose>\d+(?:\.\d+)?)\s*(?P<unit>mg|ml|毫升|滴|片)", re.I)
SAFE_REPLACEMENT = (
    "[剂量已拦截：具体用药剂量必须由医生/药师确认，系统仅展示 Rule Engine 校验后的结构化剂量。]"
)


@dataclass(frozen=True)
class InterceptResult:
    text: str
    intercepted: bool
    matches: list[str]


class DoseInterceptor:
    def intercept_text(
        self,
        text: str,
        *,
        source: str,
        allow_rule_engine: bool = False,
    ) -> InterceptResult:
        if allow_rule_engine and source == "rule_engine":
            return InterceptResult(text=text, intercepted=False, matches=[])
        matches = [match.group(0) for match in DOSE_RE.finditer(text)]
        if not matches:
            return InterceptResult(text=text, intercepted=False, matches=[])
        return InterceptResult(
            text=DOSE_RE.sub(SAFE_REPLACEMENT, text),
            intercepted=True,
            matches=matches,
        )

    async def intercept_and_audit(
        self,
        text: str,
        *,
        source: str,
        audit_sink: AuditSink | None = None,
    ) -> InterceptResult:
        result = self.intercept_text(text, source=source)
        if result.intercepted and audit_sink is not None:
            await audit_sink.record(
                AuditRecord(
                    actor=AuditActor(actor_kind="system"),
                    action="dose_intercept",
                    resource="copilot_output",
                    before={"source": source, "matches": result.matches},
                    after={"text": result.text},
                )
            )
        return result
