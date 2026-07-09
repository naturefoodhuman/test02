# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-07-09 14:30:00

"""Family-scale soak test plan.

Target: 1 req/s household scale. The file imports without locust installed so CI can
validate syntax; running it as a Locust test requires installing `locust` manually.
"""

from __future__ import annotations

try:
    from locust import HttpUser, between, task
except Exception:  # pragma: no cover - locust is optional in CI

    class HttpUser:  # type: ignore[no-redef]
        wait_time = None

    def between(_min_wait: float, _max_wait: float):  # type: ignore[no-untyped-def]
        return None

    def task(func):  # type: ignore[no-untyped-def]
        return func


class ParentingUser(HttpUser):
    wait_time = between(1.0, 1.0)

    @task
    def healthz(self) -> None:
        self.client.get("/healthz")  # type: ignore[attr-defined]

    @task
    def metrics(self) -> None:
        self.client.get("/metrics")  # type: ignore[attr-defined]
