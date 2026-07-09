# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 16:05:00


"""SQLAlchemy MediaAsset metadata repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.media.storage import MediaAssetRecord
from server.app.models import MediaAsset as ORMMediaAsset


class SQLAlchemyMediaAssetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, record: MediaAssetRecord) -> MediaAssetRecord:
        self.session.add(
            ORMMediaAsset(
                id=record.id,
                family_id=record.family_id,
                baby_id=record.baby_id,
                event_id=record.event_id,
                local_path=record.local_path,
                thumbnail_path=record.thumbnail_path,
                encrypted=record.encrypted,
                tags=record.tags,
                meta={"filename": record.filename, "content_type": record.content_type},
            )
        )
        await self.session.flush()
        return record

    async def get(self, asset_id: str) -> MediaAssetRecord | None:
        row = await self.session.scalar(select(ORMMediaAsset).where(ORMMediaAsset.id == asset_id))
        if row is None:
            return None
        meta = row.meta or {}
        return MediaAssetRecord(
            id=row.id,
            family_id=row.family_id,
            baby_id=row.baby_id,
            event_id=row.event_id,
            filename=str(meta.get("filename", row.id)),
            content_type=str(meta.get("content_type", "application/octet-stream")),
            local_path=row.local_path,
            thumbnail_path=row.thumbnail_path,
            encrypted=row.encrypted,
            tags=row.tags,
            created_at=row.created_at.isoformat(),
        )
