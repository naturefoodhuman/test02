# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import json
from typing import Any

SECRET_KEYS = ("secret", "token", "password", "api_key", "cookie")


def _sanitize(data: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in data.items():
        if any(s in k.lower() for s in SECRET_KEYS):
            out[k] = "<redacted>"
        else:
            out[k] = v
    return out


class FEOSLogger:
    def event(self, component: str, operation: str, case_id: str | None = None, **data: Any) -> str:
        payload = {"component": component, "operation": operation, "case_id": case_id, **_sanitize(data)}
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)
