# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-03 10:35:00

"""Fregata shadow-analysis bridge.

The bridge never emits alerts directly. It normalizes external VLM/object-detection
responses into shadow events for the camera pipeline, while real device endpoints
remain local-environment configuration.
"""

from __future__ import annotations

from typing import Any, Protocol


class AsyncPostClient(Protocol):
    async def post(self, url: str, **kwargs: Any) -> Any: ...


class FregataBridge:
    def __init__(
        self,
        endpoint_url: str | None = None,
        *,
        timeout_seconds: float = 10.0,
        http_client: AsyncPostClient | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url.rstrip("/") if endpoint_url else None
        self.timeout_seconds = timeout_seconds
        self.http_client = http_client

    async def analyze_snapshot(self, snapshot: bytes) -> dict[str, object]:
        if self.endpoint_url is None:
            return {"mode": "shadow", "bytes": len(snapshot), "events": [], "source": "local"}
        try:
            response = await self._post(snapshot)
            payload = self._response_json(response)
        except Exception as exc:
            return {
                "mode": "shadow",
                "bytes": len(snapshot),
                "events": [],
                "source": "fregata",
                "error": str(exc),
            }
        events = payload.get("events") or payload.get("detections") or []
        return {
            "mode": "shadow",
            "bytes": len(snapshot),
            "events": events if isinstance(events, list) else [],
            "source": "fregata",
            "http_status": int(getattr(response, "status_code", 0)),
        }

    async def _post(self, snapshot: bytes) -> Any:
        kwargs: dict[str, Any] = {
            "content": snapshot,
            "headers": {"content-type": "image/jpeg"},
            "timeout": self.timeout_seconds,
        }
        if self.http_client is not None:
            return await self.http_client.post(self.endpoint_url or "", **kwargs)
        import httpx

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            return await client.post(
                self.endpoint_url or "",
                content=snapshot,
                headers=kwargs["headers"],
            )

    @staticmethod
    def _response_json(response: Any) -> dict[str, Any]:
        payload = response.json()
        return payload if isinstance(payload, dict) else {}
