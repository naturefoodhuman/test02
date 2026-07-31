# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-31 22:02:00

"""PowerSync service smoke probe helpers.

This module does not implement synchronization. It only verifies that the
self-hosted PowerSync service exposed by docker compose is reachable and serving
its health probe endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ProbeResponse:
    endpoint: str
    status_code: int | None
    ok: bool
    error: str | None = None


@dataclass(frozen=True)
class PowerSyncProbeResult:
    base_url: str
    liveness: ProbeResponse
    readiness: ProbeResponse | None = None

    @property
    def ok(self) -> bool:
        return self.liveness.ok and (self.readiness is None or self.readiness.ok)


def normalize_powersync_url(url: str | None) -> str:
    """Normalize a PowerSync base URL for local smoke checks."""

    raw = (url or "http://127.0.0.1:9081").strip().rstrip("/")
    if not raw.startswith(("http://", "https://")):
        return f"http://{raw}"
    return raw


def _probe_endpoint(url: str, *, timeout_seconds: float) -> ProbeResponse:
    request = Request(url, headers={"accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            status = int(response.status)
            return ProbeResponse(endpoint=url, status_code=status, ok=200 <= status < 300)
    except HTTPError as exc:
        return ProbeResponse(endpoint=url, status_code=exc.code, ok=False, error=str(exc))
    except (TimeoutError, URLError, OSError) as exc:
        return ProbeResponse(endpoint=url, status_code=None, ok=False, error=str(exc))


def probe_powersync(
    base_url: str | None = None,
    *,
    timeout_seconds: float = 2.0,
    include_readiness: bool = False,
) -> PowerSyncProbeResult:
    """Probe PowerSync liveness and optionally readiness endpoints."""

    normalized = normalize_powersync_url(base_url)
    liveness = _probe_endpoint(f"{normalized}/probes/liveness", timeout_seconds=timeout_seconds)
    readiness = None
    if include_readiness:
        readiness = _probe_endpoint(
            f"{normalized}/probes/readiness",
            timeout_seconds=timeout_seconds,
        )
    return PowerSyncProbeResult(base_url=normalized, liveness=liveness, readiness=readiness)
