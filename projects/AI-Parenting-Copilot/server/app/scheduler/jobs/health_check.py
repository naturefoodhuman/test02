# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 06:40:00


"""Health check scheduler job."""

from __future__ import annotations

from server.app.health.monitor import DeviceHealthMonitor


class HealthCheckJob:
    name = "health_check"

    def __init__(self, monitor: DeviceHealthMonitor, *, family_id: str, baby_id: str) -> None:
        self.monitor = monitor
        self.family_id = family_id
        self.baby_id = baby_id

    async def run(self) -> dict[str, object]:
        results = await self.monitor.run_once(family_id=self.family_id, baby_id=self.baby_id)
        return {
            "kind": "health_check",
            "statuses": {item.name: item.status.value for item in results},
        }
