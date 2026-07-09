# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 06:40:00


"""APC-T036 scheduler job tests."""

from __future__ import annotations

import pytest

from server.app.health.monitor import DeviceHealthMonitor, MockHealthProbe
from server.app.notification.alert_repo import InMemoryAlertRepository
from server.app.rule_engine.domains.vaccine import VaccineRuleModule
from server.app.rule_engine.loader import load_rule_pack
from server.app.scheduler.jobs.health_check import HealthCheckJob
from server.app.scheduler.jobs.morning_brief import MorningBriefJob
from server.app.scheduler.jobs.supplement import SupplementReminderJob
from server.app.scheduler.jobs.vaccine_due import VaccineDueJob
from server.app.scheduler.runner import SchedulerRunner


@pytest.mark.asyncio
async def test_scheduler_manual_trigger_jobs() -> None:
    runner = SchedulerRunner()
    runner.register(MorningBriefJob())
    runner.register(SupplementReminderJob([{"name": "vitamin_d"}]))

    morning = await runner.trigger("morning_brief")
    supplement = await runner.trigger("supplement")

    assert morning["kind"] == "morning_brief"
    assert supplement["alert_level"] == "blue"


@pytest.mark.asyncio
async def test_vaccine_due_job_generates_due_items() -> None:
    module = VaccineRuleModule(
        load_rule_pack(__import__("pathlib").Path("config/rules/vaccine/cn-nip-2024.yaml"))
    )
    job = VaccineDueJob(module, {"birth_date": "2026-07-09", "as_of": "2026-07-09"})

    result = await job.run()

    assert result["kind"] == "vaccine_due"
    assert result["count"] >= 1
    assert result["alert_level"] == "blue"


@pytest.mark.asyncio
async def test_health_check_job_runs_monitor() -> None:
    repo = InMemoryAlertRepository()
    monitor = DeviceHealthMonitor([MockHealthProbe("mqtt", online=True)], repo)
    job = HealthCheckJob(monitor, family_id="family-1", baby_id="baby-1")

    result = await job.run()

    assert result["statuses"] == {"mqtt": "online"}
