# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 04:25:00


"""AI Orchestrator façade."""

from __future__ import annotations

from pydantic import BaseModel, Field

from server.app.copilots.base import CopilotRegistry, CopilotRequest, CopilotResponse
from server.app.copilots.logger_copilot import LoggerCopilot
from server.app.memory.injector import MemoryStore
from server.app.observability.audit import AuditSink
from server.app.orchestrator.context_builder import ContextBuilder
from server.app.orchestrator.intent_router import IntentRouter
from server.app.orchestrator.output_guard import OutputGuard


class OrchestratorRequest(BaseModel):
    text: str
    baby_id: str | None = None
    family_id: str | None = None
    intent: str | None = None


class OrchestratorResponse(BaseModel):
    intent: str
    copilot_response: CopilotResponse | None = None
    text: str | None = None
    evidence: list[dict[str, object]] = Field(default_factory=list)
    dose_intercepted: bool = False


class Orchestrator:
    def __init__(
        self,
        *,
        registry: CopilotRegistry | None = None,
        memory_store: MemoryStore | None = None,
        audit_sink: AuditSink | None = None,
    ) -> None:
        self.intent_router = IntentRouter()
        self.context_builder = ContextBuilder(memory_store)
        self.output_guard = OutputGuard()
        self.registry = registry or CopilotRegistry()
        if registry is None:
            self.registry.register(LoggerCopilot())
        self.audit_sink = audit_sink

    async def handle(self, request: OrchestratorRequest) -> OrchestratorResponse:
        intent = request.intent or self.intent_router.route(request.text)
        memory = self.context_builder.build(baby_id=request.baby_id, family_id=request.family_id)
        if intent == "record":
            copilot = self.registry.select(
                CopilotRequest(
                    text=request.text,
                    intent=intent,
                    baby_id=request.baby_id,
                    family_id=request.family_id,
                )
            )
            response = await copilot.handle(
                CopilotRequest(
                    text=request.text,
                    intent=intent,
                    baby_id=request.baby_id,
                    family_id=request.family_id,
                ),
                memory,
            )
            return OrchestratorResponse(
                intent=intent,
                copilot_response=response,
                evidence=response.evidence,
            )
        guarded = await self.output_guard.guard_text(
            "暂不支持该请求，请使用记录入口或等待后续 Copilot。",
            source="orchestrator",
            audit_sink=self.audit_sink,
        )
        return OrchestratorResponse(
            intent=intent,
            text=guarded.text,
            evidence=[{"source": "orchestrator", "message": "Fallback response"}],
            dose_intercepted=guarded.intercepted,
        )
