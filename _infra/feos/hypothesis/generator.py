# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import Evidence, Hypothesis


def generate_hypothesis_from_evidence(case_id: str, hyp_id: str, evidence: Evidence) -> Hypothesis:
    statement = evidence.content.text_preview or f"Issue related to {evidence.id}"
    return Hypothesis(id=hyp_id, case_id=case_id, statement=statement[:300], supports=[evidence.id], confidence=1.0)
