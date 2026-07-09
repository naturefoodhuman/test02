# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 06:40:00


"""Device/service health monitor that creates gray alerts in dev mode."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from server.app.notification.alert_repo import (
    AlertLevel,
    CreateAlertRequest,
    InMemoryAlertRepository,
)


class ProbeStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"


@dataclass(slots=True)
class ProbeResult:
    name: str
    status: ProbeStatus
    message: str = ""


class HealthProbe(Protocol):
    name: str

    async def check(self) -> ProbeResult: ...


class MockHealthProbe:
    def __init__(self, name: str, *, online: bool = True) -> None:
        self.name = name
        self.online = online

    async def check(self) -> ProbeResult:
        return ProbeResult(
            name=self.name,
            status=ProbeStatus.ONLINE if self.online else ProbeStatus.OFFLINE,
            message="ok" if self.online else "offline",
        )


class DeviceHealthMonitor:
    def __init__(self, probes: list[HealthProbe], alert_repo: InMemoryAlertRepository) -> None:
        self.probes = probes
        self.alert_repo = alert_repo
        self.last_results: dict[str, ProbeResult] = {}

    async def run_once(self, *, family_id: str, baby_id: str) -> list[ProbeResult]:
        results = [await probe.check() for probe in self.probes]
        for result in results:
            self.last_results[result.name] = result
            if result.status == ProbeStatus.OFFLINE:
                await self.alert_repo.create(
                    CreateAlertRequest(
                        family_id=family_id,
                        baby_id=baby_id,
                        level=AlertLevel.GRAY,
                        type="device_health",
                        evidence={"probe": result.name, "message": result.message},
                        recommended_action="检查设备或服务连接状态",
                    )
                )
        return results

    def snapshot(self) -> dict[str, str]:
        return {name: result.status.value for name, result in self.last_results.items()}
