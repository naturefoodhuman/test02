# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 12:15:00

"""Periodic scheduler worker for in-process FastAPI runtime."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass, field

from server.app.common.clock import utc_now
from server.app.scheduler.runner import SchedulerRunner


@dataclass(slots=True)
class SchedulerWorkerSnapshot:
    started: bool = False
    run_count: int = 0
    last_started_at: str | None = None
    last_finished_at: str | None = None
    last_error: str | None = None
    last_results: dict[str, dict[str, object]] = field(default_factory=dict)


class PeriodicSchedulerWorker:
    """Run SchedulerRunner periodically without adding APScheduler dependency."""

    name = "scheduler-periodic-worker"

    def __init__(
        self,
        runner: SchedulerRunner,
        *,
        interval_seconds: float = 3600.0,
        run_on_start: bool = False,
    ) -> None:
        self.runner = runner
        self.interval_seconds = interval_seconds
        self.run_on_start = run_on_start
        self.snapshot = SchedulerWorkerSnapshot()
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stop_event = asyncio.Event()
        self.snapshot.started = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self.snapshot.started = False
        self._stop_event.set()
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def run_once(self) -> dict[str, dict[str, object]]:
        self.snapshot.last_started_at = utc_now().isoformat()
        try:
            results = await self.runner.trigger_all()
        except Exception as exc:
            self.snapshot.last_error = str(exc)
            raise
        self.snapshot.run_count += 1
        self.snapshot.last_error = None
        self.snapshot.last_finished_at = utc_now().isoformat()
        self.snapshot.last_results = results
        return results

    async def _loop(self) -> None:
        if self.run_on_start:
            with suppress(Exception):
                await self.run_once()
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval_seconds)
            except TimeoutError:
                with suppress(Exception):
                    await self.run_once()
