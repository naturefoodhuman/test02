# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import uuid


def new_trace_id() -> str:
    return "trace_" + uuid.uuid4().hex[:16]
