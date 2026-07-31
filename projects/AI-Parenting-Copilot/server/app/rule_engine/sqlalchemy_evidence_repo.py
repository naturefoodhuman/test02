# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 20:55:00


"""SQLAlchemy EvidencePolicy repository adapter."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.common.clock import utc_now
from server.app.common.ids import new_ulid
from server.app.models import EvidencePolicy as ORMEvidencePolicy
from server.app.rule_engine.evidence_repo import EvidencePolicyRecord
from server.app.rule_engine.loader import RulePack


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


class SQLAlchemyEvidencePolicyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def activate(self, pack: RulePack) -> EvidencePolicyRecord:
        existing = await self.session.scalar(
            select(ORMEvidencePolicy).where(
                ORMEvidencePolicy.policy_type == pack.policy_type,
                ORMEvidencePolicy.region == pack.region,
                ORMEvidencePolicy.version == pack.version,
            )
        )
        if existing is not None and existing.effective_to is None:
            return self._to_record(existing)

        now = utc_now()
        current_rows = await self.session.scalars(
            select(ORMEvidencePolicy).where(
                ORMEvidencePolicy.policy_type == pack.policy_type,
                ORMEvidencePolicy.region == pack.region,
                ORMEvidencePolicy.effective_to.is_(None),
            )
        )
        for current in current_rows:
            if current.version != pack.version:
                current.effective_to = now
                current.updated_at = now
        effective_from = _parse_datetime(pack.effective_from)
        rule_text = pack.model_dump_json(exclude={"hash"})
        policy_hash = pack.compute_hash()
        if existing is not None:
            existing.effective_from = effective_from
            existing.effective_to = None
            existing.source = pack.source
            existing.rule_text = rule_text
            existing.display_text = pack.source
            existing.hash = policy_hash
            existing.updated_at = now
            await self.session.flush()
            return self._to_record(existing)
        row = ORMEvidencePolicy(
            id=new_ulid(),
            policy_type=pack.policy_type,
            region=pack.region,
            version=pack.version,
            effective_from=effective_from,
            source=pack.source,
            rule_text=rule_text,
            display_text=pack.source,
            hash=policy_hash,
        )
        self.session.add(row)
        await self.session.flush()
        return self._to_record(row)

    async def get_current(
        self,
        policy_type: str,
        region: str = "CN",
    ) -> EvidencePolicyRecord | None:
        row = await self.session.scalar(
            select(ORMEvidencePolicy).where(
                ORMEvidencePolicy.policy_type == policy_type,
                ORMEvidencePolicy.region == region,
                ORMEvidencePolicy.effective_to.is_(None),
            )
        )
        return self._to_record(row) if row is not None else None

    @staticmethod
    def _to_record(row: ORMEvidencePolicy) -> EvidencePolicyRecord:
        return EvidencePolicyRecord(
            policy_type=row.policy_type,
            region=row.region,
            version=row.version,
            effective_from=row.effective_from.isoformat(),
            source=row.source or "",
            rule_text=row.rule_text or "",
            hash=row.hash,
            effective_to=row.effective_to.isoformat() if row.effective_to else None,
        )
