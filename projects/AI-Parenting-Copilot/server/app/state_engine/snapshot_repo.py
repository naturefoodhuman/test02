# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""DerivedBabyState snapshot repository."""

from __future__ import annotations

from pydantic import BaseModel, Field

from server.app.common.clock import utc_now


class DerivedBabyStateSnapshot(BaseModel):
    baby_id: str
    family_id: str
    snapshot: dict[str, object] = Field(default_factory=dict)
    computed_at: str = Field(default_factory=lambda: utc_now().isoformat())
    source_event_count: int = 0


class InMemoryStateSnapshotRepository:
    def __init__(self) -> None:
        self.snapshots: dict[str, DerivedBabyStateSnapshot] = {}

    def upsert(self, snapshot: DerivedBabyStateSnapshot) -> DerivedBabyStateSnapshot:
        self.snapshots[snapshot.baby_id] = snapshot
        return snapshot

    def get(self, baby_id: str) -> DerivedBabyStateSnapshot | None:
        return self.snapshots.get(baby_id)
