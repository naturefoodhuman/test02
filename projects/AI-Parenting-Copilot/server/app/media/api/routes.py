# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 12:25:00

"""Media API using JSON/base64 uploads to avoid multipart dependency."""

from __future__ import annotations

import base64
from typing import cast

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field

from server.app.common.errors import AppError, NotFoundError
from server.app.media.sqlalchemy_media_repo import SQLAlchemyMediaAssetRepository
from server.app.media.storage import MediaAssetRecord, MediaStorageService
from server.app.media.thumbnails import generate_thumbnail
from server.app.observability.request_audit import record_request_audit

router = APIRouter(prefix="/api/v1/media", tags=["media"])


class MediaUploadRequest(BaseModel):
    family_id: str
    baby_id: str | None = None
    event_id: str | None = None
    filename: str
    content_type: str
    content_base64: str
    tags: dict[str, object] = Field(default_factory=dict)


def _service(request: Request) -> MediaStorageService:
    service = getattr(request.app.state, "media_storage", None)
    if service is None:
        raise AppError(
            "Media storage is not configured",
            code="MEDIA_STORAGE_UNAVAILABLE",
            status_code=500,
        )
    return cast(MediaStorageService, service)


async def _persist_if_db(request: Request, record: MediaAssetRecord) -> None:
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        await SQLAlchemyMediaAssetRepository(db_session).add(record)


async def _get_record_from_db(request: Request, asset_id: str) -> MediaAssetRecord | None:
    db_session = getattr(request.state, "db_session", None)
    if db_session is None:
        return None
    return await SQLAlchemyMediaAssetRepository(db_session).get(asset_id)


@router.post("", response_model=MediaAssetRecord)
async def upload_media(payload: MediaUploadRequest, request: Request) -> MediaAssetRecord:
    content = base64.b64decode(payload.content_base64.encode())
    service = _service(request)
    record = service.store(
        content=content,
        filename=payload.filename,
        content_type=payload.content_type,
        family_id=payload.family_id,
        baby_id=payload.baby_id,
        event_id=payload.event_id,
        tags=payload.tags,
    )
    if payload.content_type.startswith("image/"):
        thumb = generate_thumbnail(content, service.thumbs_dir / f"{record.id}.png")
        record = service.attach_thumbnail(record.id, str(thumb))
    await _persist_if_db(request, record)
    await record_request_audit(
        request,
        action="media.upload",
        resource=f"media_asset:{record.id}",
        after=record.model_dump(mode="json"),
        db_only=True,
    )
    return record


@router.get("/{asset_id}")
async def read_media(asset_id: str, request: Request) -> Response:
    service = _service(request)
    record = service.assets.get(asset_id)
    if record is None:
        record = await _get_record_from_db(request, asset_id)
        if record is not None:
            service.assets[asset_id] = record
    if record is None:
        raise NotFoundError("Media asset not found", evidence={"asset_id": asset_id})
    return Response(content=service.read(asset_id), media_type=record.content_type)
