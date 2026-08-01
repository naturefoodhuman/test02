# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 10:15:00

"""HTTP endpoint health probe."""

from __future__ import annotations

import asyncio
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from server.app.health.monitor import ProbeResult, ProbeStatus


def _http_status(url: str, timeout_seconds: float) -> tuple[int | None, str]:
    request = Request(url, headers={"accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            return int(response.status), "http ok"
    except HTTPError as exc:
        return exc.code, str(exc)
    except (TimeoutError, URLError, OSError) as exc:
        return None, str(exc)


class HTTPHealthProbe:
    def __init__(self, name: str, url: str, *, timeout_seconds: float = 1.0) -> None:
        self.name = name
        self.url = url
        self.timeout_seconds = timeout_seconds

    async def check(self) -> ProbeResult:
        status_code, message = await asyncio.to_thread(_http_status, self.url, self.timeout_seconds)
        if status_code is not None and 200 <= status_code < 300:
            return ProbeResult(name=self.name, status=ProbeStatus.ONLINE, message=message)
        detail = f"{status_code}: {message}" if status_code is not None else message
        return ProbeResult(name=self.name, status=ProbeStatus.OFFLINE, message=detail)
