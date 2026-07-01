# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ParsedResponse, VerificationCheckResult


class EvidenceAlignmentCheck:
    check_id = "evidence_alignment"
    fatal = False

    def run(self, parsed: ParsedResponse, context=None):
        has_refs = any(claim.evidence_refs for claim in parsed.claims)
        return VerificationCheckResult(check_id=self.check_id, status="passed" if has_refs or not parsed.claims else "warning", summary="claims have evidence refs" if has_refs else "claims need human evidence review")
