# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 04:25:00


"""AI Orchestrator façade."""

from __future__ import annotations

from pydantic import BaseModel, Field

from server.app.copilots.base import (
    CopilotRegistry,
    CopilotRequest,
    CopilotResponse,
    DomainCopilot,
)
from server.app.copilots.family_memory import FamilyMemoryCopilot
from server.app.copilots.growth_milestone import GrowthMilestoneCopilot
from server.app.copilots.logger_copilot import LoggerCopilot
from server.app.copilots.medication_safety import MedicationSafetyCopilot
from server.app.copilots.proactive_copilot import ProactiveCopilot
from server.app.copilots.vaccine_planner import VaccinePlannerCopilot
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
    context: dict[str, object] = Field(default_factory=dict)


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
            default_copilots: list[DomainCopilot] = [
                LoggerCopilot(),
                ProactiveCopilot(),
                FamilyMemoryCopilot(),
                VaccinePlannerCopilot(),
                GrowthMilestoneCopilot(),
                MedicationSafetyCopilot(),
            ]
            for copilot in default_copilots:
                self.registry.register(copilot)
        self.audit_sink = audit_sink

    async def handle(self, request: OrchestratorRequest) -> OrchestratorResponse:
        intent = request.intent or self.intent_router.route(request.text)
        memory = self.context_builder.build(baby_id=request.baby_id, family_id=request.family_id)
        if intent in {"record", "proactive", "family_memory", "vaccine", "growth", "medication"}:
            copilot = self.registry.select(
                CopilotRequest(
                    text=request.text,
                    intent=intent,
                    baby_id=request.baby_id,
                    family_id=request.family_id,
                    context=request.context,
                )
            )
            response = await copilot.handle(
                CopilotRequest(
                    text=request.text,
                    intent=intent,
                    baby_id=request.baby_id,
                    family_id=request.family_id,
                    context=request.context,
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
