# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 12:35:00

"""Export API routes for visit summaries."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field

from server.app.common.errors import AppError, NotFoundError
from server.app.export.service import ExportRecord, ExportService
from server.app.observability.request_audit import record_request_audit

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


class ExportSummaryRequest(BaseModel):
    title: str
    events: list[dict[str, object]] = Field(default_factory=list)
    format: Literal["md", "pdf"] = "md"
    generated_by: str | None = None


def _service(request: Request) -> ExportService:
    service = getattr(request.app.state, "export_service", None)
    if service is None:
        raise AppError(
            "Export service is not configured",
            code="EXPORT_SERVICE_UNAVAILABLE",
            status_code=500,
        )
    return cast(ExportService, service)


@router.post("/summary", response_model=ExportRecord)
async def export_summary(payload: ExportSummaryRequest, request: Request) -> ExportRecord:
    record = _service(request).export_summary(
        title=payload.title,
        events=payload.events,
        format=payload.format,
        generated_by=payload.generated_by,
    )
    await record_request_audit(
        request,
        action="export.summary",
        resource=f"export:{record.id}",
        after=record.model_dump(mode="json"),
    )
    return record


@router.get("/{export_id}")
async def read_export(export_id: str, request: Request) -> Response:
    record = _service(request).records.get(export_id)
    if record is None:
        raise NotFoundError("Export not found", evidence={"export_id": export_id})
    path = Path(record.local_path)
    if not path.exists():
        raise NotFoundError("Export file not found", evidence={"export_id": export_id})
    media_type = "text/markdown; charset=utf-8" if record.format == "md" else "application/pdf"
    return Response(content=path.read_bytes(), media_type=media_type)
