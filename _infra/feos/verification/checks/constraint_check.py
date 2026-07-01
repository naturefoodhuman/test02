# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ParsedResponse, VerificationCheckResult


class ConstraintCheck:
    check_id = "constraint"
    fatal = False

    def run(self, parsed: ParsedResponse, context=None):
        bad = any("直接执行" in rec.text or "自动执行" in rec.text for rec in parsed.recommendations)
        return VerificationCheckResult(check_id=self.check_id, status="failed" if bad else "passed", summary="external execution suggestion blocked" if bad else "constraints ok")
