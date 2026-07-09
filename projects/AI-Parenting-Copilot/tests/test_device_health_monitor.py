# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 06:40:00


"""APC-T035 Device Health Monitor tests."""

from __future__ import annotations

import pytest

from server.app.health.monitor import DeviceHealthMonitor, MockHealthProbe, ProbeStatus
from server.app.notification.alert_repo import InMemoryAlertRepository


@pytest.mark.asyncio
async def test_probe_failure_generates_gray_alert() -> None:
    alert_repo = InMemoryAlertRepository()
    monitor = DeviceHealthMonitor([MockHealthProbe("camera", online=False)], alert_repo)

    results = await monitor.run_once(family_id="family-1", baby_id="baby-1")
    active = await alert_repo.list_active(family_id="family-1")

    assert results[0].status == ProbeStatus.OFFLINE
    assert active[0].level == "gray"
    assert active[0].type == "device_health"
    assert monitor.snapshot() == {"camera": "offline"}
