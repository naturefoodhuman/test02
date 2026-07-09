# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 12:50:00


"""Baby State Engine service."""

from __future__ import annotations

from server.app.normalization.dedup import apply_correction
from server.app.normalization.service import NormalizedRecord
from server.app.state_engine.projections.diaper import project_diaper
from server.app.state_engine.projections.feeding import project_feeding
from server.app.state_engine.projections.sleep import project_sleep
from server.app.state_engine.projections.supplement import project_supplement
from server.app.state_engine.projections.temperature import project_temperature
from server.app.state_engine.snapshot_repo import (
    DerivedBabyStateSnapshot,
    InMemoryStateSnapshotRepository,
)


class BabyStateEngine:
    def __init__(self, snapshot_repo: InMemoryStateSnapshotRepository | None = None) -> None:
        self.snapshot_repo = snapshot_repo or InMemoryStateSnapshotRepository()

    def recompute(
        self,
        *,
        baby_id: str,
        family_id: str,
        records: list[NormalizedRecord],
    ) -> DerivedBabyStateSnapshot:
        active_records = apply_correction([r for r in records if r.baby_id == baby_id])
        snapshot: dict[str, object] = {}
        for projection in [
            project_feeding,
            project_diaper,
            project_sleep,
            project_temperature,
            project_supplement,
        ]:
            snapshot.update(projection(active_records))
        result = DerivedBabyStateSnapshot(
            baby_id=baby_id,
            family_id=family_id,
            snapshot=snapshot,
            source_event_count=len(active_records),
        )
        return self.snapshot_repo.upsert(result)
