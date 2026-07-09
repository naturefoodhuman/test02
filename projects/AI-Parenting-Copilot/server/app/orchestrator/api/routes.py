# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 04:25:00


"""Orchestrator API routes."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request

from server.app.common.errors import AppError
from server.app.orchestrator.orchestrator import (
    Orchestrator,
    OrchestratorRequest,
    OrchestratorResponse,
)

router = APIRouter(prefix="/api/v1/copilot", tags=["copilot"])


def _orchestrator(request: Request) -> Orchestrator:
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if orchestrator is None:
        raise AppError(
            "Orchestrator is not configured",
            code="ORCHESTRATOR_UNAVAILABLE",
            status_code=500,
        )
    return cast(Orchestrator, orchestrator)


@router.post("/query", response_model=OrchestratorResponse)
async def query(payload: OrchestratorRequest, request: Request) -> OrchestratorResponse:
    return await _orchestrator(request).handle(payload)
