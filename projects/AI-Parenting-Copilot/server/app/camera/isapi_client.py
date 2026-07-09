# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-09 07:15:00


"""ISAPI client placeholder for camera event/control integration."""

from __future__ import annotations


class ISAPIClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    async def health(self) -> dict[str, str]:
        return {"status": "not_configured", "base_url": self.base_url}
