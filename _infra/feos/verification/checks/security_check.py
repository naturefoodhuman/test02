# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

from _infra.feos.models import ParsedResponse, VerificationCheckResult


class SecurityCheck:
    check_id = "security"
    fatal = False

    def run(self, parsed: ParsedResponse, context=None):
        text = "\n".join([rec.text for rec in parsed.recommendations] + parsed.risks + parsed.assumptions)
        bad = any(word in text.lower() for word in ["api_key", "password", "cookie", "secret"])
        return VerificationCheckResult(check_id=self.check_id, status="failed" if bad else "passed", summary="secret-like content detected" if bad else "security ok")
