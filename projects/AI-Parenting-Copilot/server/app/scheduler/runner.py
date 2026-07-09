# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 06:40:00


"""Manual-trigger scheduler runner used until APScheduler worker is enabled."""

from __future__ import annotations

from typing import Protocol


class SchedulerJob(Protocol):
    name: str

    async def run(self) -> dict[str, object]: ...


class SchedulerRunner:
    def __init__(self) -> None:
        self.jobs: dict[str, SchedulerJob] = {}

    def register(self, job: SchedulerJob) -> None:
        self.jobs[job.name] = job

    async def trigger(self, name: str) -> dict[str, object]:
        return await self.jobs[name].run()

    async def trigger_all(self) -> dict[str, dict[str, object]]:
        return {name: await job.run() for name, job in self.jobs.items()}
