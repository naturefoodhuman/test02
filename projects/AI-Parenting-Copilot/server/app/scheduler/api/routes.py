# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-03 10:05:00

"""Manual scheduler API routes.

The production scheduler worker is still intentionally conservative. These routes
let operators and tests trigger P0 jobs explicitly without introducing a new
scheduler infrastructure dependency.
"""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request

from server.app.common.errors import AppError, NotFoundError
from server.app.notification.alert_repo import (
    AlertLevel,
    CreateAlertRequest,
    InMemoryAlertRepository,
)
from server.app.notification.sqlalchemy_alert_repo import SQLAlchemyAlertRepository
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


def _alert_repo(request: Request) -> InMemoryAlertRepository | SQLAlchemyAlertRepository:
    db_session = getattr(request.state, "db_session", None)
    if db_session is not None:
        return SQLAlchemyAlertRepository(db_session)
    repo = getattr(request.app.state, "alert_repository", None)
    if repo is None:
        raise AppError(
            "Alert repository is not configured",
            code="ALERT_REPO_UNAVAILABLE",
            status_code=500,
        )
    return cast(InMemoryAlertRepository, repo)


def _recommended_action(job_name: str, result: dict[str, object]) -> str:
    summary = result.get("summary")
    if isinstance(summary, str) and summary:
        return summary
    if job_name == "vaccine_due":
        return "查看疫苗到期提醒并按接种机构建议预约。"
    if job_name == "supplement":
        return "查看补剂待办，按家庭既定计划确认。"
    return "查看定时任务提醒。"


async def _maybe_create_reminder_alert(
    *,
    request: Request,
    job_name: str,
    result: dict[str, object],
    family_id: str | None,
    baby_id: str | None,
    create_alert: bool,
) -> dict[str, object]:
    if not create_alert:
        return result
    alert_level = result.get("alert_level")
    if not alert_level or family_id is None or baby_id is None:
        return result
    alert = await _alert_repo(request).create(
        CreateAlertRequest(
            baby_id=baby_id,
            family_id=family_id,
            level=AlertLevel(str(alert_level)),
            type=f"scheduler.{job_name}",
            evidence={"job": job_name, "result": result},
            recommended_action=_recommended_action(job_name, result),
        )
    )
    await record_request_audit(
        request,
        action="alert.create",
        resource=f"alert:{alert.id}",
        after=alert.model_dump(mode="json"),
        db_only=True,
    )
    enriched = dict(result)
    enriched["created_alert_id"] = alert.id
    return enriched


@router.get("/jobs", response_model=list[str])
async def list_scheduler_jobs(request: Request) -> list[str]:
    return sorted(_runner(request).jobs)


@router.post("/jobs/{job_name}/trigger", response_model=dict[str, object])
async def trigger_scheduler_job(
    job_name: str,
    request: Request,
    family_id: str | None = None,
    baby_id: str | None = None,
    create_alert: bool = False,
) -> dict[str, object]:
    runner = _runner(request)
    if job_name not in runner.jobs:
        raise NotFoundError("Scheduler job not found", evidence={"job_name": job_name})
    result = await runner.trigger(job_name)
    result = await _maybe_create_reminder_alert(
        request=request,
        job_name=job_name,
        result=result,
        family_id=family_id,
        baby_id=baby_id,
        create_alert=create_alert,
    )
    await record_request_audit(
        request,
        action="scheduler.trigger",
        resource=f"scheduler_job:{job_name}",
        after=result,
    )
    return result


@router.post("/trigger-all", response_model=dict[str, dict[str, object]])
async def trigger_all_scheduler_jobs(
    request: Request,
    family_id: str | None = None,
    baby_id: str | None = None,
    create_alert: bool = False,
) -> dict[str, dict[str, object]]:
    results = await _runner(request).trigger_all()
    enriched: dict[str, dict[str, object]] = {}
    for job_name, result in results.items():
        enriched[job_name] = await _maybe_create_reminder_alert(
            request=request,
            job_name=job_name,
            result=result,
            family_id=family_id,
            baby_id=baby_id,
            create_alert=create_alert,
        )
    await record_request_audit(
        request,
        action="scheduler.trigger_all",
        resource="scheduler_job:*",
        after={"jobs": enriched},
    )
    return enriched
