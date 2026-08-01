# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 10:15:00

"""PowerSync health probe."""

from __future__ import annotations

from server.app.health.monitor import ProbeResult, ProbeStatus
from server.app.sync.service.powersync_probe import probe_powersync


class PowerSyncHealthProbe:
    name = "powersync"

    def __init__(self, base_url: str | None, *, timeout_seconds: float = 1.0) -> None:
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    async def check(self) -> ProbeResult:
        result = probe_powersync(self.base_url, timeout_seconds=self.timeout_seconds)
        if result.ok:
            return ProbeResult(name=self.name, status=ProbeStatus.ONLINE, message="liveness ok")
        return ProbeResult(
            name=self.name,
            status=ProbeStatus.OFFLINE,
            message=result.liveness.error or f"status={result.liveness.status_code}",
        )
