# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import Evidence


def allowed_attachment_refs(evidence: list[Evidence]) -> list[str]:
    return [ev.content.raw_ref for ev in evidence if not ev.security.contains_secret and not ev.security.contains_pii]
