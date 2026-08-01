# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-08-01 10:35:00

"""Smoke-check a running FastAPI server.

This script intentionally does not start uvicorn. It gives a clear action message
when the user forgot to start the API process before using curl.
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _request_json(url: str, *, method: str = "GET", timeout: float = 3.0) -> dict[str, object]:
    request = Request(url, method=method, headers={"accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--family-id", default="dev-family")
    parser.add_argument("--baby-id", default="dev-baby")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    query = urlencode({"family_id": args.family_id, "baby_id": args.baby_id})
    try:
        health = _request_json(f"{base_url}/healthz")
        check = _request_json(f"{base_url}/api/v1/system/health/check?{query}", method="POST")
        system = _request_json(f"{base_url}/api/v1/system/health")
    except (TimeoutError, URLError, OSError) as exc:
        print(
            "FastAPI server is not reachable. Start it in a separate terminal first:\n"
            "  cd projects/AI-Parenting-Copilot\n"
            "  export PARENTING_DATABASE__URL=postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting\n"
            "  export PARENTING_POWERSYNC__URL=http://127.0.0.1:9081\n"
            "  make run-api\n\n"
            f"Then retry: make api-health-smoke\nOriginal error: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    print(
        json.dumps(
            {"healthz": health, "check": check, "system": system},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
