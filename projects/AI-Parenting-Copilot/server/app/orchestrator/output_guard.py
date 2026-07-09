# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 04:25:00


"""Output guard pipeline."""

from __future__ import annotations

from server.app.observability.audit import AuditSink
from server.app.orchestrator.dose_interceptor import DoseInterceptor, InterceptResult


class OutputGuard:
    def __init__(self, dose_interceptor: DoseInterceptor | None = None) -> None:
        self.dose_interceptor = dose_interceptor or DoseInterceptor()

    async def guard_text(
        self,
        text: str,
        *,
        source: str,
        audit_sink: AuditSink | None = None,
    ) -> InterceptResult:
        return await self.dose_interceptor.intercept_and_audit(
            text,
            source=source,
            audit_sink=audit_sink,
        )
