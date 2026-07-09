# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 08:40:00


"""Media API using JSON/base64 dev uploads to avoid multipart dependency."""

from __future__ import annotations

import base64
from typing import cast

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field

from server.app.common.errors import AppError, NotFoundError
from server.app.media.storage import MediaAssetRecord, MediaStorageService
from server.app.media.thumbnails import generate_thumbnail

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
        service.attach_thumbnail(record.id, str(thumb))
    return record


@router.get("/{asset_id}")
async def read_media(asset_id: str, request: Request) -> Response:
    service = _service(request)
    record = service.assets.get(asset_id)
    if record is None:
        raise NotFoundError("Media asset not found", evidence={"asset_id": asset_id})
    return Response(content=service.read(asset_id), media_type=record.content_type)
