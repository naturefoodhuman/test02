# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-03 10:35:00

"""ISAPI client for camera status/control integration.

This adapter stays thin and testable: production credentials/device reachability are
local-environment concerns, while unit tests inject a fake async HTTP client.
"""

from __future__ import annotations

from typing import Any, Protocol


class AsyncGetClient(Protocol):
    async def get(self, url: str, **kwargs: Any) -> Any: ...


class ISAPIClient:
    def __init__(
        self,
        base_url: str,
        *,
        username: str | None = None,
        password: str | None = None,
        timeout_seconds: float = 5.0,
        http_client: AsyncGetClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout_seconds = timeout_seconds
        self.http_client = http_client

    async def health(self) -> dict[str, str]:
        if not self.base_url or self.base_url == "mock":
            return {"status": "not_configured", "base_url": self.base_url}
        url = f"{self.base_url}/ISAPI/System/status"
        try:
            response = await self._get(url)
        except Exception as exc:
            return {"status": "offline", "base_url": self.base_url, "error": str(exc)}
        status_code = int(getattr(response, "status_code", 0))
        return {
            "status": "online" if 200 <= status_code < 400 else "degraded",
            "base_url": self.base_url,
            "http_status": str(status_code),
        }

    async def _get(self, url: str) -> Any:
        auth = (self.username, self.password) if self.username and self.password else None
        if self.http_client is not None:
            kwargs: dict[str, Any] = {"timeout": self.timeout_seconds}
            if auth is not None:
                kwargs["auth"] = auth
            return await self.http_client.get(url, **kwargs)
        import httpx

        async with httpx.AsyncClient(timeout=self.timeout_seconds, auth=auth) as client:
            return await client.get(url)
