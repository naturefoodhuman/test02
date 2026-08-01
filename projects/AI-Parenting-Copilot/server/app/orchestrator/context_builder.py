# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 23:20:00


"""Context Builder for Orchestrator."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable
from typing import Any, Protocol

from server.app.memory.injector import MemorySnapshot, MemoryStore


class ContextMemoryStore(Protocol):
    def build_snapshot(
        self,
        *,
        baby_id: str | None = None,
        family_id: str | None = None,
        rule_versions: dict[str, Any] | None = None,
    ) -> MemorySnapshot | Awaitable[MemorySnapshot]: ...


class ContextBuilder:
    def __init__(self, memory_store: ContextMemoryStore | None = None) -> None:
        self.memory_store = memory_store or MemoryStore()

    def build(
        self,
        *,
        baby_id: str | None = None,
        family_id: str | None = None,
        rule_versions: dict[str, object] | None = None,
    ) -> MemorySnapshot:
        result = self.memory_store.build_snapshot(
            baby_id=baby_id,
            family_id=family_id,
            rule_versions=rule_versions,
        )
        if inspect.isawaitable(result):
            raise RuntimeError("Async memory store requires build_async")
        return result

    async def build_async(
        self,
        *,
        baby_id: str | None = None,
        family_id: str | None = None,
        rule_versions: dict[str, object] | None = None,
    ) -> MemorySnapshot:
        result = self.memory_store.build_snapshot(
            baby_id=baby_id,
            family_id=family_id,
            rule_versions=rule_versions,
        )
        if inspect.isawaitable(result):
            return await result
        return result
