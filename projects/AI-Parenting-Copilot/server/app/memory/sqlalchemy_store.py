# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 22:52:00

"""SQLAlchemy-backed M1-M5 MemoryStore implementation."""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.common.clock import utc_now
from server.app.memory.injector import MemorySnapshot
from server.app.memory.local_rag import LocalRAGMemoryAdapter
from server.app.models import (
    Baby as ORMBaby,
)
from server.app.models import (
    DerivedBabyState as ORMDerivedBabyState,
)
from server.app.models import (
    EvidencePolicy as ORMEvidencePolicy,
)
from server.app.models import (
    FamilyKnowledge as ORMFamilyKnowledge,
)
from server.app.models import (
    ObservationEvent as ORMObservationEvent,
)

JsonDict = dict[str, Any]


class SQLAlchemyMemoryStore:
    """Build structured Copilot memory from PostgreSQL first, Local RAG second."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        local_rag: LocalRAGMemoryAdapter | None = None,
    ) -> None:
        self.session = session
        self.local_rag = local_rag or LocalRAGMemoryAdapter()

    async def build_snapshot(
        self,
        *,
        baby_id: str | None = None,
        family_id: str | None = None,
        rule_versions: JsonDict | None = None,
    ) -> MemorySnapshot:
        family_id = family_id or await self._family_id_for_baby(baby_id)
        rule_version_map = await self._rule_versions()
        rule_version_map.update(dict(rule_versions or {}))
        family_preferences, correction_memory = await self._family_knowledge(family_id)
        if self.local_rag.available() and family_id:
            correction_memory["local_rag"] = self.local_rag.search_corrections(
                f"family:{family_id} baby:{baby_id or ''} correction memory",
                limit=5,
            )
        return MemorySnapshot(
            baby_id=baby_id,
            family_id=family_id,
            hard_facts=await self._hard_facts(baby_id),
            family_preferences=family_preferences,
            behavior_baseline=await self._behavior_baseline(baby_id),
            short_context=await self._short_context(baby_id),
            correction_memory=correction_memory,
            rule_versions=rule_version_map,
        )

    async def _family_id_for_baby(self, baby_id: str | None) -> str | None:
        if not baby_id:
            return None
        row = await self.session.scalar(select(ORMBaby).where(ORMBaby.id == baby_id))
        return row.family_id if row is not None else None

    async def _hard_facts(self, baby_id: str | None) -> JsonDict:
        if not baby_id:
            return {}
        row = await self.session.scalar(select(ORMBaby).where(ORMBaby.id == baby_id))
        if row is None:
            return {}
        facts: JsonDict = {
            "name": row.name,
            "family_id": row.family_id,
            "gestational_age_weeks": row.gestational_age_weeks,
            "is_preterm": row.is_preterm,
            "birth_weight_g": row.birth_weight_g,
            "current_weight_g": row.current_weight_g,
            "current_weight_kg": (row.current_weight_g / 1000) if row.current_weight_g else None,
            "sex": row.sex,
            "vaccine_region": row.vaccine_region,
            "allergies": row.allergies,
        }
        if isinstance(row.birth_date, date):
            facts["birth_date"] = row.birth_date.isoformat()
            facts["age_days"] = max(0, (utc_now().date() - row.birth_date).days)
        if row.current_weight_at is not None:
            facts["current_weight_at"] = row.current_weight_at.isoformat()
        return facts

    async def _family_knowledge(self, family_id: str | None) -> tuple[JsonDict, JsonDict]:
        if not family_id:
            return {}, {}
        rows = await self.session.scalars(
            select(ORMFamilyKnowledge).where(
                ORMFamilyKnowledge.family_id == family_id,
                ORMFamilyKnowledge.is_deleted.is_(False),
            )
        )
        preferences: JsonDict = {}
        corrections: JsonDict = {}
        for row in rows:
            target = corrections if row.key.startswith("correction.") else preferences
            target[row.key] = row.value
        return preferences, corrections

    async def _behavior_baseline(self, baby_id: str | None) -> JsonDict:
        if not baby_id:
            return {}
        row = await self.session.scalar(
            select(ORMDerivedBabyState).where(ORMDerivedBabyState.baby_id == baby_id)
        )
        return dict(row.snapshot) if row is not None else {}

    async def _short_context(self, baby_id: str | None) -> JsonDict:
        if not baby_id:
            return {}
        cutoff = utc_now() - timedelta(hours=72)
        rows = list(
            await self.session.scalars(
                select(ORMObservationEvent)
                .where(
                    ORMObservationEvent.baby_id == baby_id,
                    ORMObservationEvent.is_deleted.is_(False),
                    ORMObservationEvent.start_time >= cutoff,
                )
                .order_by(ORMObservationEvent.start_time.desc())
                .limit(20)
            )
        )
        counts = Counter(row.event_type for row in rows)
        return {
            "window_hours": 72,
            "event_count": len(rows),
            "event_type_counts": dict(counts),
            "last_event_at": rows[0].start_time.isoformat() if rows else None,
            "recent_event_types": [row.event_type for row in rows[:5]],
        }

    async def _rule_versions(self) -> JsonDict:
        rows = await self.session.scalars(
            select(ORMEvidencePolicy).where(ORMEvidencePolicy.effective_to.is_(None))
        )
        return {row.policy_type: row.version for row in rows}
