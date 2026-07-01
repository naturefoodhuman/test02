# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ParsedResponse, VerificationCheckResult


class TestabilityCheck:
    check_id = "testability"
    fatal = False

    def run(self, parsed: ParsedResponse, context=None):
        status = "skipped" if "testability" == "sandbox" else "passed"
        summary = "sandbox disabled" if "testability" == "sandbox" else "testability ok"
        if "testability" == "testability" and not any("test" in rec.text.lower() or "测试" in rec.text for rec in parsed.recommendations):
            status = "warning"; summary = "recommendation should include validation/test plan"
        return VerificationCheckResult(check_id=self.check_id, status=status, summary=summary)
