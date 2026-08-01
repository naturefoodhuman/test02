# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 10:20:00

"""Health probe unit tests."""

from __future__ import annotations

import socket

import pytest

from server.app.health.monitor import ProbeStatus
from server.app.health.probes.powersync import PowerSyncHealthProbe
from server.app.health.probes.tcp import TCPPortHealthProbe


@pytest.mark.asyncio
async def test_tcp_probe_reports_online_for_open_socket() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    host, port = server.getsockname()
    try:
        result = await TCPPortHealthProbe("tcp-test", host, port).check()
    finally:
        server.close()

    assert result.status == ProbeStatus.ONLINE


@pytest.mark.asyncio
async def test_powersync_probe_reports_offline_for_unreachable_port() -> None:
    result = await PowerSyncHealthProbe("http://127.0.0.1:9", timeout_seconds=0.1).check()

    assert result.status == ProbeStatus.OFFLINE
    assert result.name == "powersync"
