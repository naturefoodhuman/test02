# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-21 15:28:00 CST

"""审计事件数据模型（轻量）"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import json
import uuid


@dataclass
class AuditEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""                    # tool_call | privacy_detection | canary_hit | ...
    server_id: str | None = None
    tool_name: str | None = None
    mode: str = "research"
    decision: str = "allow"
    details: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.event_id,
            "event_type": self.event_type,
            "server_id": self.server_id,
            "tool_name": self.tool_name,
            "mode": self.mode,
            "decision": self.decision,
            "details": json.dumps(self.details, ensure_ascii=False),
            "created_at": self.created_at,
        }
