# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 10:15:00

"""TCP port health probe."""

from __future__ import annotations

import asyncio

from server.app.health.monitor import ProbeResult, ProbeStatus


class TCPPortHealthProbe:
    def __init__(self, name: str, host: str, port: int, *, timeout_seconds: float = 1.0) -> None:
        self.name = name
        self.host = host
        self.port = port
        self.timeout_seconds = timeout_seconds

    async def check(self) -> ProbeResult:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout_seconds,
            )
            writer.close()
            await writer.wait_closed()
            del reader
            return ProbeResult(name=self.name, status=ProbeStatus.ONLINE, message="tcp connect ok")
        except Exception as exc:
            return ProbeResult(name=self.name, status=ProbeStatus.OFFLINE, message=str(exc))
