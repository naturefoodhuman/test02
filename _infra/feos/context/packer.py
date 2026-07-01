# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ContextPackage, ContextSection
from .token_budget import estimate_tokens


class ContextPacker:
    def pack(self, package_id: str, case_id: str, sections: list[ContextSection], budget: int) -> tuple[ContextPackage, list[str]]:
        kept = []
        warnings = []
        total = 0
        for section in sections:
            section.token_estimate = estimate_tokens(section.content)
            if total + section.token_estimate <= budget:
                kept.append(section)
                total += section.token_estimate
            else:
                warnings.append(f"omitted section {section.id}: token budget exceeded")
        return ContextPackage(id=package_id, case_id=case_id, sections=kept, token_budget=budget, token_estimate=total, metadata={"warnings": warnings}), warnings
