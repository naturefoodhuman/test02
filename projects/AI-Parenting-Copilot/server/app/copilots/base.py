# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 04:25:00


"""Copilot base protocol and registry."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from server.app.common.errors import ConflictError, NotFoundError
from server.app.memory.injector import MemorySnapshot


class CopilotRequest(BaseModel):
    text: str
    intent: str = "record"
    baby_id: str | None = None
    family_id: str | None = None
    context: dict[str, object] = Field(default_factory=dict)
    memory: dict[str, object] = Field(default_factory=dict)


class CopilotResponse(BaseModel):
    copilot: str
    intent: str
    payload: dict[str, object] = Field(default_factory=dict)
    evidence: list[dict[str, object]] = Field(default_factory=list)
    requires_confirmation: bool = True
    safety_level: str = "low"


class DomainCopilot(Protocol):
    name: str
    safety_level: str

    def can_handle(self, request: CopilotRequest) -> bool: ...

    async def handle(self, request: CopilotRequest, memory: MemorySnapshot) -> CopilotResponse: ...


class CopilotRegistry:
    def __init__(self) -> None:
        self._copilots: dict[str, DomainCopilot] = {}

    def register(self, copilot: DomainCopilot) -> None:
        if copilot.name in self._copilots:
            raise ConflictError("Copilot already registered", evidence={"name": copilot.name})
        self._copilots[copilot.name] = copilot

    def get(self, name: str) -> DomainCopilot:
        copilot = self._copilots.get(name)
        if copilot is None:
            raise NotFoundError("Copilot not registered", evidence={"name": name})
        return copilot

    def select(self, request: CopilotRequest) -> DomainCopilot:
        for copilot in self._copilots.values():
            if copilot.can_handle(request):
                return copilot
        raise NotFoundError("No copilot can handle request", evidence={"intent": request.intent})

    def names(self) -> list[str]:
        return sorted(self._copilots)
