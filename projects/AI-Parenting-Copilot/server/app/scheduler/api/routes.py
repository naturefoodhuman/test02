# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 11:15:00

"""Manual scheduler API routes.

The production scheduler worker is still intentionally conservative. These routes
let operators and tests trigger P0 jobs explicitly without introducing a new
scheduler infrastructure dependency.
"""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request

from server.app.common.errors import AppError, NotFoundError
from server.app.observability.request_audit import record_request_audit
from server.app.scheduler.runner import SchedulerRunner

router = APIRouter(prefix="/api/v1/scheduler", tags=["scheduler"])


def _runner(request: Request) -> SchedulerRunner:
    runner = getattr(request.app.state, "scheduler_runner", None)
    if runner is None:
        raise AppError(
            "Scheduler runner is not configured",
            code="SCHEDULER_UNAVAILABLE",
            status_code=500,
        )
    return cast(SchedulerRunner, runner)


@router.get("/jobs", response_model=list[str])
async def list_scheduler_jobs(request: Request) -> list[str]:
    return sorted(_runner(request).jobs)


@router.post("/jobs/{job_name}/trigger", response_model=dict[str, object])
async def trigger_scheduler_job(job_name: str, request: Request) -> dict[str, object]:
    runner = _runner(request)
    if job_name not in runner.jobs:
        raise NotFoundError("Scheduler job not found", evidence={"job_name": job_name})
    result = await runner.trigger(job_name)
    await record_request_audit(
        request,
        action="scheduler.trigger",
        resource=f"scheduler_job:{job_name}",
        after=result,
    )
    return result


@router.post("/trigger-all", response_model=dict[str, dict[str, object]])
async def trigger_all_scheduler_jobs(request: Request) -> dict[str, dict[str, object]]:
    result = await _runner(request).trigger_all()
    await record_request_audit(
        request,
        action="scheduler.trigger_all",
        resource="scheduler_job:*",
        after={"jobs": result},
    )
    return result
