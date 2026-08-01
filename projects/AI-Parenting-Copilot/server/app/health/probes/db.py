# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 10:15:00

"""PostgreSQL database health probe."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from server.app.health.monitor import ProbeResult, ProbeStatus


class DatabaseHealthProbe:
    name = "database"

    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def check(self) -> ProbeResult:
        try:
            async with self.engine.connect() as connection:
                value = await connection.scalar(text("SELECT 1"))
            if value == 1:
                return ProbeResult(name=self.name, status=ProbeStatus.ONLINE, message="select 1 ok")
            return ProbeResult(
                name=self.name,
                status=ProbeStatus.OFFLINE,
                message="unexpected result",
            )
        except Exception as exc:
            return ProbeResult(name=self.name, status=ProbeStatus.OFFLINE, message=str(exc))
