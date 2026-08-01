# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 10:36:00

"""Start a temporary uvicorn process and smoke-check health endpoints."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _request_json(url: str, *, method: str = "GET", timeout: float = 2.0) -> dict[str, object]:
    request = Request(url, method=method, headers={"accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _wait_ready(base_url: str, timeout_seconds: float) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return _request_json(f"{base_url}/healthz")
        except (TimeoutError, URLError, OSError) as exc:
            last_error = exc
            time.sleep(0.2)
    raise RuntimeError(f"API did not become ready: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--timeout-seconds", type=float, default=15.0)
    args = parser.parse_args()
    base_url = f"http://{args.host}:{args.port}"
    process = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "uvicorn",
            "server.app.main:app",
            "--host",
            args.host,
            "--port",
            str(args.port),
        ],
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        health = _wait_ready(base_url, args.timeout_seconds)
        query = urlencode({"family_id": "dev-family", "baby_id": "dev-baby"})
        check = _request_json(f"{base_url}/api/v1/system/health/check?{query}", method="POST")
        system = _request_json(f"{base_url}/api/v1/system/health")
        print(
            json.dumps(
                {"healthz": health, "check": check, "system": system},
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        if process.returncode not in {0, -15, -9, None}:
            stderr = process.stderr.read() if process.stderr is not None else ""
            print(stderr, file=sys.stderr)


if __name__ == "__main__":
    main()
