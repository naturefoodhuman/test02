# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 04:25:00


"""Context Builder for Orchestrator."""

from __future__ import annotations

from server.app.memory.injector import MemorySnapshot, MemoryStore


class ContextBuilder:
    def __init__(self, memory_store: MemoryStore | None = None) -> None:
        self.memory_store = memory_store or MemoryStore()

    def build(
        self,
        *,
        baby_id: str | None = None,
        family_id: str | None = None,
        rule_versions: dict[str, object] | None = None,
    ) -> MemorySnapshot:
        return self.memory_store.build_snapshot(
            baby_id=baby_id,
            family_id=family_id,
            rule_versions=rule_versions,
        )
